from django.db import models


class UserInfo(models.Model):
    uuid = models.UUIDField(max_length=32, null=False, blank=False, unique=True, primary_key=True)
    name = models.CharField(max_length=16, null=True, blank=True)
    nick_name = models.CharField(max_length=16, null=False, blank=False)
    age = models.IntegerField(null=True, blank=True)
    sex = models.BooleanField(default=True)
    phone = models.CharField(max_length=11, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    born = models.DateField(null=True, blank=True)
    city = models.CharField(max_length=32, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    avatar = models.ImageField(upload_to='avatar', null=True, blank=True)
    objects = models.Manager()

    class Meta:
        db_table = 'userInfo'


class User(models.Model):
    username = models.CharField(max_length=32, null=False, blank=False, unique=True, primary_key=True,help_text='账号')
    password = models.CharField(max_length=32, null=False, blank=False,help_text='密码')
    role = models.CharField(max_length=16, choices=((0, '普通用户'), (1, '会员用户'), (2, '管理员')),
                            default='普通用户',)
    is_delete = models.BooleanField(default=False)
    userInfo = models.ForeignKey(UserInfo, on_delete=models.CASCADE, null=True, blank=True)
    objects = models.Manager()

    class Meta:
        db_table = 'user'


class HouseInfo(models.Model):
    city = models.CharField(max_length=8, blank=True, null=True)
    title = models.CharField(max_length=56, blank=True, null=True)
    region = models.CharField(max_length=16, blank=True, null=True)
    area = models.CharField(max_length=8, blank=True, null=True)
    house_type = models.CharField(max_length=8, blank=True, null=True)
    house_size = models.CharField(max_length=16, blank=True, null=True)
    toward = models.CharField(max_length=16, blank=True, null=True)
    decoration = models.CharField(max_length=8, blank=True, null=True)
    floor = models.CharField(max_length=16, blank=True, null=True)
    building_type = models.CharField(max_length=8, blank=True, null=True)
    year = models.CharField(max_length=8, blank=True, null=True)
    view_num = models.IntegerField(blank=True, null=True)
    release_time = models.CharField(max_length=16, blank=True, null=True)
    single_price = models.IntegerField(blank=True, null=True)
    total_price = models.IntegerField(blank=True, null=True)
    img = models.CharField(max_length=128, blank=True, null=True)
    objects = models.Manager()

    class Meta:
        managed = False
        db_table = 'houseInfo'
