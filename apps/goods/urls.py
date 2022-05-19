from django.urls import path, re_path
from . import views


urlpatterns = [
    path('index', views.index_view, name='index'),
    re_path('^goods/(?P<sku_id>\\d+)$', views.detail_view, name='detail'),
    re_path('^list/(?P<type_id>\\d+)/(?P<page>\\d+)$', views.list_view, name='list')
]
