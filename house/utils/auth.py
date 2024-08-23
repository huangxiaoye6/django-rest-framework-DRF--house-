import datetime
from django.conf import settings
from rest_framework.authentication import BasicAuthentication
from rest_framework.exceptions import AuthenticationFailed
from app.models import User
import jwt
from jwt import exceptions


def create_token(payload):
    salt = settings.SECRET_KEY
    headers = {
        'typ': 'jwt',
        'alg': 'HS256',
    }
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    token = jwt.encode(payload=payload, key=salt, headers=headers, algorithm='HS256')
    return token


class MyAuthentication(BasicAuthentication):
    def authenticate(self, request):
        token = request.META.get('HTTP_AUTHORIZATION')
        if token:
            salt = settings.SECRET_KEY
            payload = None
            try:
                payload = jwt.decode(token, salt, algorithms='HS256', verify=True)
            except exceptions.ExpiredSignatureError:
                raise AuthenticationFailed({'code': '1000', 'msg': 'token已经失效'})
            except jwt.DecodeError:
                raise AuthenticationFailed({'code': '1001', 'msg': 'token认证失败'})
            except jwt.InvalidTokenError:
                raise AuthenticationFailed({'code': '1002', 'msg': '非法的token'})
            user_objects = User.objects.filter(username=payload['user']['username']).first()
            return user_objects, token
        else:
            raise AuthenticationFailed({'code': '1003', 'msg': '没有获取到token'})

    def authenticate_header(self, request):
        return 'API'
