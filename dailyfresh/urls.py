"""dailyfresh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),   # tinymce的路由
    path('search', include('haystack.urls')),   # haystack的路由
    path('user/', include(('user.urls', 'user'), namespace='user')),
    path('shopping_cart/', include(('shopping_cart.urls', 'shopping_cart'), namespace='shopping_cart')),
    path('orders/', include(('orders.urls', 'order'), namespace='order')),
    path('', include(('goods.urls', 'goods'), namespace='goods')),

]
