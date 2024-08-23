from rest_framework import serializers
from app.models import User, HouseInfo, UserInfo
import os

class UserInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserInfo
        exclude = ['time']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class InfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        exclude = ["time"]


class LoginSerializer(serializers.ModelSerializer):
    userInfo = InfoSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['username', 'role', 'userInfo']


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = HouseInfo
        fields = "__all__"


class AvatarSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInfo
        fields = ['avatar']
