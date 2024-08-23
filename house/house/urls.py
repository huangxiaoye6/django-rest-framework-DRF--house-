"""
URL configuration for house project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.yasg home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from app import views

Schema_View = get_schema_view(
    openapi.Info(title='接口文档', default_version='v1', description='描述信息'),
    public=True,
    authentication_classes=[]
)
urlpatterns = [
    path('app/', include('app.urls')),
    path(r'media/avatar/<str:img_path>', views.ImgView.as_view(), name='AvatarDetail'),
    path('docs/', Schema_View.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
