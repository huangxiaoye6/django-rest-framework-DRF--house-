from django.urls import path

from app import views

urlpatterns = [
    path('register/', views.UserView.as_view(), name='user'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('pwd/', views.PwdView.as_view(), name='pwd'),
    path('userInfo/', views.UserInfoView.as_view(), name='userInfo'),
    path('houseList/', views.HouseListView.as_view(), name='houseList'),
    path('houseInfo/', views.HouseInfoView.as_view(), name='houseInfo'),
    path('area/',views.AreaView.as_view(), name='area'),
    path('analysis/',views.AnalysisView.as_view(), name='analysis'),
    path('predict/',views.PredictView.as_view(),name='predict'),
    path('options/',views.OptionsAPIview.as_view(),name='options'),
    path('houseview/',views.HouseView.as_view(),name='houseView'),
    path('avatar/',views.AvatarView.as_view(),name='avatar'),
    path('email/',views.EmailView.as_view(),name='email'),
]

