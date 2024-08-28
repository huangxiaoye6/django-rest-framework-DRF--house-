import os.path
import uuid
from django.db.models import Avg, Sum, Count
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from app.tasks import send_email, predict_model
from utils.auth import create_token
from app.models import User, HouseInfo, UserInfo
from app.serializers import UserSerializer, UserInfoSerializer, LoginSerializer, HouseSerializer, AvatarSerializer
from house import settings
from django.core.cache import cache
from utils.throttle import MyThrottle


class UserView(APIView):
    """
    post:创建用户和用户信息
    """
    authentication_classes = []

    def post(self, request):
        email = request.data.get('email')
        code = cache.get(email)
        if not code:
            return Response(data={'msg': '注册失败,验证码已经过期'})
        else:
            emailCode = request.data.get('emailCode')
            if emailCode != code:
                return Response(data={'msg': '注册失败,验证码错误'})
            else:
                username = request.data.get('username')
                user = User.objects.filter(username=username).first()
                if user:
                    return Response(data={'msg': '注册失败,用户已经存在', 'code': 400})
                else:
                    uid = uuid.uuid4()
                    nick_name = str(uid).split('-')[0] + '用户'
                    data = {'username': username, 'password': request.data.get('password'), 'userInfo': uid}
                    info_serializer = UserInfoSerializer(
                        data={'uuid': uid, 'phone': request.data.get('phone'), 'email': request.data.get('email'),
                              'nick_name': nick_name})
                    user_serializer = UserSerializer(data=data)
                    if info_serializer.is_valid():
                        info_serializer.save()
                        if user_serializer.is_valid():
                            user_serializer.save()
                            return Response(data={'msg': '注册成功', 'code': 200})
                        else:
                            return Response(data={'msg': '注册失败', 'error': user_serializer.errors, 'code': 401})
                    else:
                        info = UserInfo.objects.filter(uuid=uid).first()
                        info.delete()
                        return Response(data={'msg': '注册失败', 'error': info_serializer.errors, 'code': 401})


class PwdView(APIView):
    """
    put:修改密码
    """

    def put(self, request):
        user = User.objects.filter(username=request.data.get('username')).first()
        if user:
            data = {'password': request.data.get('new_password')}
            if user.password == request.data.get('password'):
                serializer = UserSerializer(instance=user, data=data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(data={'msg': '修改成功', 'code': 200})
                else:
                    return Response(data={'msg': '修改失败', 'error': serializer.errors, 'code': 401})
            else:
                return Response(data={'msg': '修改失败', 'error': '输入的密码错误', 'code': 402})
        else:
            return Response(data={'msg': '修改失败', 'error': '用户不存在', 'code': 400})


class LoginView(APIView):
    """
    post:用户登录
    """
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        user = User.objects.filter(username=username, is_delete=False).first()
        if user:
            pwd = request.data.get('password')
            if user.password == pwd:
                serializer = LoginSerializer(instance=user, context={'request': request})
                data = serializer.data
                payload = {'user': data, }
                token = create_token(payload)
                print(data)
                return Response(data={'msg': '登陆成功', 'token': token, 'code': 200})
            else:
                return Response(data={'msg': '登陆失败,密码错误', 'code': 400})
        else:
            return Response(data={'msg': '登录失败，该用户不存在', 'code': 400})


class UserInfoView(APIView):
    """
    get:查询用户信息
    put:修改用户信息
    """

    def get(self, request):
        uuid = request.query_params.get('uuid')
        userInfo = UserInfo.objects.filter(uuid=uuid).first()
        if userInfo:
            serializer = UserInfoSerializer(instance=userInfo)
            return Response(data={'msg': '查询成功', 'data': serializer.data, 'code': 200})
        else:
            return Response(data={'msg': '查询失败', 'error': '用户不存在', 'code': 400})

    def put(self, request):
        try:
            uid = request.query_params.get('uuid')
            userInfo = UserInfo.objects.filter(uuid=uid).first()
        except Exception as error:
            return Response(data={'msg': '修改失败', 'error': error, 'code': 400})
        if userInfo:
            serializer = UserInfoSerializer(instance=userInfo, data=request.data, partial=True,
                                            context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(data={'msg': '修改成功', 'data': serializer.data, 'code': 200})
            else:
                return Response(data={'msg': '修改失败', 'error': serializer.errors, 'code': 401})
        else:
            return Response(data={'msg': '修改失败', 'error': '用户不存在', 'code': 400})


class HouseListView(APIView):
    """
    get:查询房屋信息
    """

    def get(self, request):
        city = request.query_params.get('city')
        if city:
            house = HouseInfo.objects.filter(city=city).all().order_by('id')

        else:
            house = HouseInfo.objects.all().order_by('id')
        page = PageNumberPagination()
        page.page_size = 20
        page.max_page_size = 50
        page.page_query_param = 'page'
        page.page_size_query_param = 'size'
        houseData = page.paginate_queryset(queryset=house, request=request)
        serializer = HouseSerializer(instance=houseData, many=True)
        return Response(data={'msg': '查询成功', 'data': serializer.data, 'code': 200})


class HouseInfoView(APIView):
    """
    get:查询房屋概况
    """

    @method_decorator(cache_page(timeout=60 * 60 * 2, key_prefix='house_info'))
    def get(self, request):
        houseInfo = HouseInfo.objects.aggregate(mean_total_price=Avg('total_price'),
                                                mean_single_price=Avg('single_price'), view_num=Sum('view_num'),
                                                house_num=Count('id'))
        return Response(data={'msg': '查询成功', 'data': houseInfo, 'code': 200})


class AreaView(APIView):
    """
    get:查询房屋区域列表
    """

    @method_decorator(cache_page(timeout=60 * 60 * 2, key_prefix='area'))
    def get(self, request):
        data = HouseInfo.objects.values('city').distinct()
        return Response(data={'msg': '查询成功', 'data': data, 'code': 200})


class AnalysisView(APIView):
    """
    get:查询房屋分析信息
    """

    @method_decorator(cache_page(timeout=60 * 60 * 2, key_prefix='analysis'))
    def get(self, request):
        area_Analysis = HouseInfo.objects.values('city', ).annotate(total_price=Avg('total_price'),
                                                                    single_price=Avg('single_price'),
                                                                    view_num=Sum('view_num'))
        decoration_Analysis = HouseInfo.objects.values('decoration').annotate(view_num=Sum('view_num'))
        house_type_Analysis = HouseInfo.objects.values('house_type').annotate(view_num=Sum('view_num')).filter(
            view_num__gt=10)
        return Response(data={'msg': '查询成功', 'area': area_Analysis, 'decoration': decoration_Analysis,
                              'house_type': house_type_Analysis, 'code': 200})


class OptionsAPIview(APIView):
    """
    get:查询房屋选项
    """

    @method_decorator(cache_page(timeout=60 * 60 * 2, key_prefix='options'))
    def get(self, request):
        data = {}
        house = HouseInfo.objects.values('city', 'area').distinct()
        city_areas = {}
        for item in house:
            city = item['city']
            area = item['area']
            if city in city_areas:
                city_areas[city].append(area)
            else:
                city_areas[city] = [area]
        result_list = [{'city': city, 'areas': areas} for city, areas in city_areas.items()]
        data['city_area_list'] = result_list
        data['house_type_list'] = HouseInfo.objects.values_list('house_type', flat=True).distinct()
        data['decoration_list'] = HouseInfo.objects.values_list('decoration', flat=True).distinct()
        data['building_type_list'] = HouseInfo.objects.values_list('building_type', flat=True).distinct()
        return Response(data={"msg": '查询成功', 'data': data, 'code': 200})


class PredictView(APIView):
    """
    post:预测房价
    """

    def post(self, request):
        try:
            input_data = request.data
            predict_data = predict_model.delay(input_data)
            return Response(data={'msg': '预测成功', 'data': {'single_price': predict_data.get()['single_price'],
                                                              'total_price': predict_data.get()['total_price']},'code': 200})
        except Exception as error:
            return Response(data={'msg': '预测失败', 'error': error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HouseView(APIView):
    """
    get:查询房屋信息
    """

    @method_decorator(cache_page(timeout=60 * 60 * 2, key_prefix='house'))
    def get(self, request):
        data = {'area_Analysis': HouseInfo.objects.values('city', ).annotate(total_price=Avg('total_price'),
                                                                             single_price=Avg('single_price'),
                                                                             view_num=Sum('view_num')),
                'house_type_Analysis': HouseInfo.objects.values('house_type').annotate(view_num=Sum('view_num'))[:10],
                'toward_Analysis': HouseInfo.objects.values('toward').annotate(toward_num=Count('toward'))[:30],
                'decoration_Analysis': HouseInfo.objects.values('decoration').annotate(
                    single_price=Avg('single_price')),
                'building_type_Analysis': HouseInfo.objects.values('building_type').annotate(
                    total_price=Avg('total_price'))}
        return Response(data={"msg": "查询成功", "data": data, 'code': 200})


class AvatarView(APIView):
    """
    post:用户头像上传
    """

    def post(self, request):
        uid = request.data.get('uuid')
        user = UserInfo.objects.filter(uuid=uid).first()
        if user:
            serializer = AvatarSerializer(instance=user, data=request.data, partial=True,context={'request':request})
            if serializer.is_valid():
                path = os.path.join(settings.MEDIA_ROOT, str(user.avatar))
                if os.path.exists(path) and user.avatar:
                    os.remove(path)
                serializer.save()
                data=serializer.data
                return Response(data={'msg': '上传成功', 'data': data, 'code': 200, })
            else:
                return Response(data={'msg': '上传失败', 'error': serializer.errors, 'code': 401})
        else:
            return Response(data={'msg': '上传失败', 'error': '没有查询到用户', 'code': 400})


class ImgView(APIView):
    """
    get:图片查询
    """
    authentication_classes = []

    def get(self, request, img_path):
        path = os.path.join(settings.MEDIA_ROOT, 'avatar', img_path)
        if os.path.exists(path):
            with open(path, 'rb') as f:
                data = f.read()
                return HttpResponse(content=data, content_type='image/jpeg')
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class EmailView(APIView):
    """
    post:发送邮箱验证码
    """
    authentication_classes = []
    throttle_classes = [MyThrottle]

    def post(self, request):
        userEmail = request.data.get('email')
        if not userEmail:
            return Response(data={'msg': '发送失败', 'error': '邮箱不能为空'})
        else:
            try:
                send_email.delay(userEmail)
                return Response(data={'msg': '发送成功'}, status=status.HTTP_200_OK)
            except Exception as error:
                print(error)
                return Response(data={'msg': '发送失败', 'error': str(error)})
