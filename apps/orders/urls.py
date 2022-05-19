from django.urls import path, re_path
from .views import OrderPlaceView, OrderCommitView, OrderPayView, OrderCheckView, CommentView


urlpatterns = [

        path('place', OrderPlaceView.as_view(), name='place'),
        path('commit', OrderCommitView.as_view(), name='commit'),
        path('pay', OrderPayView.as_view(), name='pay'),
        path('check', OrderCheckView.as_view(), name='check'),
        re_path('^comment/(?P<order_id>\\d+)$', CommentView.as_view(), name='commit'),

]
