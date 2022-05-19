from django.urls import path, re_path
from .views import RegisterView, LoginView, UserCenterAddress
from . import views


urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),
    re_path('active/(?P<token>.*)', views.active, name='active'),
    path('login', LoginView.as_view(), name='login'),
    path('user_center_info', views.user_center_info, name='user_center_info'),
    re_path('^user_center_order/(?P<page>\\d+)$', views.user_center_order, name='user_center_order'),
    path('user_center_address', UserCenterAddress.as_view(), name='user_center_address'),
    path('logout', views.logout_view, name='logout'),
]
