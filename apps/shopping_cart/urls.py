from django.urls import path
from .views import *
from . import views


urlpatterns = [
    path('add', CartAddView.as_view(), name='add'),  # 添加购物车记录
    path('', CartInfoView.as_view(), name='cart'),
    path('update', CartUpdateView.as_view(), name='update'),    # 更新购物车记录
    path('delete', CartDeleteView.as_view(), name='delete'),    # 删除购物车记录
]

