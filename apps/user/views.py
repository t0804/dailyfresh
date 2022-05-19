import itsdangerous
from django.http import HttpResponse
from django.shortcuts import render, HttpResponseRedirect
from django.urls import reverse
import re
from .models import User, Address
from goods.models import GoodsSKU
from django.views.generic import View
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer
from celery_tasks import tasks
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from orders.models import *
from django.core.paginator import Paginator
# Create your views here.

'''
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    elif request.method == 'POST':
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        print(allow)
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        if not password == cpassword:
            return render(request, 'register.html', {'errmsg': '两次密码输入不一致'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})
        if not all([username, password, cpassword]):
            return render(request, 'register.html', {'errmsg': '内容不完整'})

        user = User.objects.filter(username=username)
        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = 0
        user.save()
        return HttpResponseRedirect(reverse('goods:index'))
'''


class RegisterView(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        confirm_password = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # print(allow)
        # 判断内容是否完整
        if not all([username, password, confirm_password]):
            return render(request, 'register.html', {'errmsg': '内容不完整'})
        # 判断是否同意协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})
        # 判断两次密码是否相同
        if not password == confirm_password:
            return render(request, 'register.html', {'errmsg': '两次密码输入不一致'})
        # 判断邮箱格式是否正确
        # ^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$
        # ^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        user = User.objects.filter(username=username)
        # 判断用户是否存在
        if user:
            return render(request, 'register.html', {'errmsg': '用户名已存在'})
        # 开始创建用户
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = 0
        user.save()

        # 加密用户信息生成token
        info = {'confirm': user.id}     # 需要加密的信息
        s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)  # 密钥存活1小时
        token = s.dumps(info)
        token = token.decode()  # 解码

        # 发送激活邮件,激活链接包含token
        tasks.send_register_active_mail.delay(email, username, token)
        # subject = '天天生鲜-用户激活'
        # message = ''
        # email = [user.email]
        # html_message = '<h1>%s，欢迎您注册天天生鲜</h1><br />' \
        #                '请点击下面链接激活您的账户<br />' \
        #                '<a href="http://127.0.0.1:8000/user/active/%s">' \
        #                'http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
        # mail.send_mail(subject, message, settings.EMAIL_FROM, email, html_message=html_message)

        return HttpResponseRedirect(reverse('goods:index'))


def active(request, token):
    # print(token)
    # token激活链接中包含
    s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 3600)
    try:
        info = s.loads(token)
        user = User.objects.get(id=info['confirm'])
        if user.is_active:
            return HttpResponse('已经激活过')
        else:
            user.is_active = True
            user.save()
        return HttpResponseRedirect(reverse('login'))
    except itsdangerous.SignatureExpired as e:
        print(e)
        return HttpResponse('激活链接已失效')


class LoginView(View):
    def get(self, request):
        if 'username' in request.COOKIES:
            # 如果username在cookie中说明已经记住过用户名把用户名返回页面，并且把记住状态默认勾选
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            # 每记住过用户名把用户名和默认勾选取消
            username = ''
            checked = ''
        return render(request, 'login.html', locals())

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        # print(request.POST)
        # 获取地址栏查询字符串的地址，如果没有默认赋值为首页地址
        next_url = request.GET.get('next', reverse('goods:index'))
        # print(next_url)

        # response跳转到next_url, 默认是首页
        resp = HttpResponseRedirect(next_url)
        user = authenticate(username=username, password=password)
        # 验证通过会返回user对象不通过会返回None
        if user is None:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        if not user.is_active:
            return render(request, 'login.html', {'errmsg': '账户尚未激活'})

        # 勾选记住用户名
        if 'remember' in request.POST:
            # cookie中存储用户名,一周后过期
            resp.set_cookie('username', username, max_age=7*24*60*60)
        # 如果不勾选删除cookie
        if 'remember' not in request.POST:
            # cookie中删除存储用户
            resp.delete_cookie('username')
        # 用内建用户系统函数登录
        login(request, user)
        return resp


@login_required()
def user_center_info(request):
    html_class = 'info'
    # 获取用户的基本信息
    # 使用自定义模型管理器方法-获取默认地址
    address_obj = Address.objects.get_default_address(request.user)

    # 获取用户的历史浏览记录
    # 获取用户最近五条历史浏览记录
    # 连接redis数据库
    con = get_redis_connection('default')
    key = 'history_%d' % request.user.id
    sku_ids = con.lrange(key, 0, 4)     # 返回list

    # 通过sku_ids从数据库查询商品信息
    sku = []
    for i in sku_ids:
        sku.append(GoodsSKU.objects.get(id=i))

    return render(request, 'user_center_info.html', locals())


# /user/user_center_order/page
@login_required()
def user_center_order(request, page):
    html_class = 'order'
    page = int(page)

    # page = request.GET.get(page)
    user = request.user

    # 获取用户的订单信息 一个用户有多个订单所以用filter
    orders = OrdersInfo.objects.filter(user=user).order_by('-create_time')
    # 获取用户订单的订单商品信息
    # 遍历每一个订单信息, 获取订单中的商品信息
    for order in orders:
        # 动态给order增加属性order_skus 保存订单中的商品信息
        order.order_skus = OrdersGoods.objects.filter(order=order)
        # 动态给order增加属性status_name 保存订单状态标题
        # OrdersInfo.ORDER_STATUS字典的key为字符串类型将order.order_status转换为str
        order.status_name = OrdersInfo.ORDER_STATUS[str(order.order_status)]
        # 遍历order_skus 计算商品的小计
        for order_sku in order.order_skus:
            # 动态给order_sku增加属性amount 保存订单商品小计
            order_sku.amount = order_sku.count * order_sku.price
            # order_sku.amount = amount

        # order.order_skus = order_skus
    # orders 拥有了订单中的商品信息属性(orders.order_skus)和订单中的商品的小计属性(orders.order_skus.amount)

    # 分页 按orders对象分页 每页显示一条
    paginator = Paginator(orders, 1)

    # 获取第page页的内容
    # 传进来的是str类型需要转换为整型, 已经在函数最上边进行转换
    # 如果url page参数大于分页总页数page默认为1
    if page > paginator.num_pages:
        page = 1
    # 实例化order的第page页的page对象
    order_page = paginator.page(page)

    # 进行页码的控制，页面上最多显示5个页码
    # 1.总页数小于5页, ，页面上显示所有页码
    # 2.如果当前页是前三页， 显示1-5页
    # 3.如果当前页是后三页，显示后5页
    # 4.其他情况，显示当前页的前2页，当前页，当前页的后2页
    num_pages = paginator.num_pages
    if num_pages < 5:
        pages = range(1, num_pages + 1)
    elif page <= 3:
        pages = range(1, 6)
    elif num_pages - page <= 2:
        pages = range(num_pages - 4, num_pages + 1)
    else:
        pages = range(page - 2, page + 3)

    return render(request, 'user_center_order.html', locals())


class UserCenterAddress(LoginRequiredMixin, View):
    def get(self, request):
        html_class = 'address'
        # 获取用户的默认收货地址
        # try:
        #     address_obj = Address.objects.get(user=request.user, is_default=True)
        # except Address.DoesNotExist:
        #     address_obj = None
        address_obj = Address.objects.get_default_address(request.user)
        return render(request, 'user_center_address.html', locals())

    def post(self, request):
        receiver = request.POST.get('receiver')
        address = request.POST.get('address')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        # 邮编可以为空
        print([receiver, address, phone])
        if not all([receiver, address, phone]):
            return render(request, 'user_center_address.html', {'errmsg': '内容不完整'})

        if not re.match(r'^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}$', phone):
            return render(request, 'user_center_address.html', {'errmsg': '手机号不合法'})
        # try:
        #     address_obj = Address.objects.get(user=request.user, is_delete=True)
        # except Address.DoesNotExist:
        #     # 不存在默认收货地址
        #     address_obj = None
        address_obj = Address.objects.get_default_address(request.user)
        if address_obj:
            is_default = True  # 如果address==True 说明没有默认收货地址 新添加地址需要默认
        else:
            is_default = False   # 如果address==False 说明有默认收货地址 新添加地址不需要默认

        # 添加地址
        Address.objects.create(user=request.user, receiver=receiver, address=address, zip_code=zip_code, phone=phone, is_default=is_default)
        # 刷新页面
        return HttpResponseRedirect(reverse('user:user_center_address'))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('user:login'))



