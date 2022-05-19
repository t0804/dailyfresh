from django.conf import settings
from django.db import transaction
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import View
from django_redis import get_redis_connection
from goods.models import GoodsSKU
from user.models import Address
from .models import *

from utils.mixin import LoginRequiredMixin
from alipay import AliPay
from datetime import datetime
import os
# Create your views here.


# /orders/place
class OrderPlaceView(LoginRequiredMixin, View):

    def post(self, request):
        user = request.user

        # 接收用户要购买商品的id
        sku_ids = request.POST.getlist('sku_ids')
        print('-----request.POST.getlist("sku_ids")=%s' % sku_ids)
        # 校验参数
        if not sku_ids:
            # 跳转到购物车页面
            return HttpResponseRedirect(reverse('shopping_cart:cart'))

        # 创建redis数据库连接，拼接key
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id

        skus = []
        total_count = 0
        total_price = 0
        for sku_id in sku_ids:
            # 根据商品id获取商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户要购买商品的数量
            count = conn.hget(key, sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加属性，让前端调用
            sku.count = int(count)
            sku.amount = amount

            skus.append(sku)
            total_count += sku.count
            total_price += sku.amount

        # 运费-实际开发时，属于一个子系统-暂时写死
        transit_price = 10

        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的地址列表
        adds = Address.objects.filter(user=user)
        # 将sku_ids通过，把id拼接成字符串，传给前台使用
        str_sku_ids = ','.join(sku_ids)

        return render(request, 'place_order.html', locals())


# 前端采用Ajax post请求 传递参数：addr_id, pay_method, str_sku_ids
class OrderCommitView1(View):
    # 提交订单--悲观锁
    @transaction.atomic
    def post(self, request):
        # 接收参数
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        str_sku_ids = request.POST.getlist('str_sku_ids')
        # 运费-暂时写死
        transit_price = 10

        # 校验数据完整性
        if not all([addr_id, pay_method, str_sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrdersInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 根据id查询下单地址对象
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist as e:
            print('-----address query err -%s' % e)
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 根据id查询价格数量
        total_count = 0     # 商品件数
        total_price = 0     # 商品总价
        skus = []           # 存放sku对象的列表

        # 创建redis连接， 拼接key
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        # 前端传递的str_sku_ids是一个列表,第0个元素是','分隔的字符串类型,需要转换成按','分隔的list类型列表
        # sku_ids = str_sku_ids.split(',')-----AttributeError: 'list' object has no attribute 'split'
        sku_ids = str_sku_ids[0].split(',')
        #
        for sku_id in sku_ids:
            try:
                # select * from df_goods_sku where id=sku_id for update;
                # 给这个事务加锁, 解决订单并发问题
                sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
            except Exception as e:
                print('-----sku query err -%s' % e)
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
            count = conn.hget(key, sku_id)

            sku.count = int(count)
            sku.amount = sku.count * sku.price

            # 累加商品的数量和价格
            total_count += sku.count
            total_price += sku.amount
            skus.append(sku)

        '''
        用户每下一个订单，就需要向订单信息表中加入一条记录
        用户的订单中有几个商品，就需要向订单商品表中添加几条记录
        订单id---订单id格式:年月日时分秒+用户id(202205131754101)
        '''

        # 拼接订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 创建事务保存点 ，用于回滚
        save_id = transaction.savepoint()
        try:
            # 创建订单信息表记录
            try:
                order = OrdersInfo.objects.create(
                    order_id=order_id,
                    pay_method=pay_method,
                    total_count=total_count,
                    total_price=total_price,
                    transit_price=transit_price,
                    # order_status=0,
                    # trade_no=1,
                    user=user,
                    address=addr,
                )
            except Exception as e:
                print('-----OrdersInfo create err -%s' % e)
                return JsonResponse({'res': 5, 'errmsg': '订单创建失败'})

            # 创建订单商品表记录&更新商品的库存和销量
            for sku in skus:
                # print(sku.__dict__)
                # print(sku.count)
                sku_count = sku.count   # 保存一下sku对象对应商品的数量
                delattr(sku, 'count')   # 删除sku对象的count属性，以便创建记录时使用
                delattr(sku, 'amount')  # 删除sku对象的amount属性，以便创建记录时使用
                # print(sku.__dict__)

                # 判断商品的库存
                if sku_count > sku.stock:
                    # 如果订单商品数量大于库存数量
                    # 回滚到上一保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 7, 'errmsg': '商品库存不足'})

                try:
                    sku = GoodsSKU.objects.get(id=sku.id)
                except Exception as e:
                    print('-----sku query err -%s' % e)
                    # 商品不存在 回滚到上一保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                try:
                    order_goods = OrdersGoods.objects.create(
                        sku=sku,
                        order=order,
                        count=sku_count,
                        price=sku.price,
                        # comment='a',
                    )
                except Exception as e:
                    print('-----OrdersGoods create err -%s' % e)
                    # 商品不存在 回滚到上一保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 6, 'errmsg': '订单商品创建失败'})

                # 更新商品的库存和销量

                sku.stock -= sku_count
                sku.sales += sku_count
                sku.save()
                if sku.stock < 0:
                    print('-----商品库存不足')
                    # 商品小于0 回滚到上一保存点
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 7, 'errmsg': '商品库存不足'})
        except Exception as e:
            print('-----Database operation exception -%s' % e)
            return JsonResponse({'res': 8, 'errmsg': '下单失败'})

        # 数据库操作没有问题 提交事务
        transaction.savepoint_commit(save_id)


        # 删除用户购物车中对应的记录
        conn.hdel(key, *sku_ids)
        print('---delete %s record')
        print('---order commit successfully')
        return JsonResponse({'res': 'ok', 'message': 'commit successfully'})


# /orders/commit
# 前端采用Ajax post请求 传递参数：addr_id, pay_method, str_sku_ids
class OrderCommitView(View):
    # 提交订单---下单失败
    @transaction.atomic
    def post(self, request):
        # 接收参数
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})

        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        str_sku_ids = request.POST.getlist('str_sku_ids')
        # 运费-暂时写死
        transit_price = 10

        # 校验数据完整性
        if not all([addr_id, pay_method, str_sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验支付方式
        if pay_method not in OrdersInfo.PAY_METHOD.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})

        # 根据id查询下单地址对象
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist as e:
            print('-----address query err -%s' % e)
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # 根据id查询价格数量
        total_count = 0     # 商品件数
        total_price = 0     # 商品总价
        skus = []           # 存放sku对象的列表

        # 创建redis连接， 拼接key
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        # 前端传递的str_sku_ids是一个列表,第0个元素是','分隔的字符串类型,需要转换成按','分隔的list类型列表
        # sku_ids = str_sku_ids.split(',')-----AttributeError: 'list' object has no attribute 'split'
        sku_ids = str_sku_ids[0].split(',')
        #
        for sku_id in sku_ids:
            try:
                # select * from df_goods_sku where id=sku_id for update;
                # 给这个事务加锁, 解决订单并发问题
                sku = GoodsSKU.objects.get(id=sku_id)
            except Exception as e:
                print('-----sku query err -%s' % e)
                return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
            count = conn.hget(key, sku_id)

            sku.count = int(count)
            sku.amount = sku.count * sku.price

            # 累加商品的数量和价格
            total_count += sku.count
            total_price += sku.amount
            skus.append(sku)

        '''
        用户每下一个订单，就需要向订单信息表中加入一条记录
        用户的订单中有几个商品，就需要向订单商品表中添加几条记录
        订单id---订单id格式:年月日时分秒+用户id(202205131754101)
        '''

        # 拼接订单id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 创建事务保存点 ，用于回滚
        save_id = transaction.savepoint()
        for i in range(3):
            try:
                # 创建订单信息表记录
                try:
                    order = OrdersInfo.objects.create(
                        order_id=order_id,
                        pay_method=pay_method,
                        total_count=total_count,
                        total_price=total_price,
                        transit_price=transit_price,
                        # order_status=0,
                        # trade_no=1,
                        user=user,
                        address=addr,
                    )
                except Exception as e:
                    print('-----OrdersInfo create err -%s' % e)
                    return JsonResponse({'res': 5, 'errmsg': '订单创建失败'})


                # 创建订单商品表记录&更新商品的库存和销量
                for sku in skus:
                    # print(sku.__dict__)
                    # print(sku.count)
                    sku_count = sku.count   # 保存一下sku对象对应商品的数量
                    delattr(sku, 'count')   # 删除sku对象的count属性，以便创建记录时使用
                    delattr(sku, 'amount')  # 删除sku对象的amount属性，以便创建记录时使用
                    # print(sku.__dict__)


                    # 判断商品的库存
                    if sku_count > sku.stock:
                        # 如果订单商品数量大于库存数量
                        # 回滚到上一保存点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 7, 'errmsg': '商品库存不足'})

                    try:
                        sku = GoodsSKU.objects.get(id=sku.id)
                    except Exception as e:
                        print('-----sku query err -%s' % e)
                        # 商品不存在 回滚到上一保存点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})
                    # import time
                    # time.sleep(10)
                    # 更新商品的库存和销量
                    origin_stock = sku.stock
                    new_stock = origin_stock - sku_count
                    new_sales = sku.sales + sku_count
                    # 返回受影响的行数
                    res = GoodsSKU.objects.filter(id=sku.id, stock=origin_stock).update(stock=new_stock,
                                                                                        sales=new_sales)
                    if res == 0:
                        # 说明操作失败
                        if i == 2:
                            # 尝试的第三次
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 8, 'errmsg': '下单失败2'})
                        continue
                    try:
                        order_goods = OrdersGoods.objects.create(
                            sku=sku,
                            order=order,
                            count=sku_count,
                            price=sku.price,
                            # comment='a',
                        )
                    except Exception as e:
                        print('-----OrdersGoods create err -%s' % e)
                        # 商品不存在 回滚到上一保存点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '订单商品创建失败'})
                    # 商品库存不能为负数
                    if sku.stock < 0:
                        print('-----商品库存不足')
                        # 商品小于0 回滚到上一保存点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 7, 'errmsg': '商品库存不足'})
            except Exception as e:
                print('-----Database operation exception -%s' % e)
                return JsonResponse({'res': 8, 'errmsg': '下单失败'})
            break # 运行完成不需要循环
        # 数据库操作没有问题 提交事务
        transaction.savepoint_commit(save_id)


        # 删除用户购物车中对应的记录
        conn.hdel(key, *sku_ids)
        print('---delete %s record')
        print('---order commit successfully')
        return JsonResponse({'res': 'ok', 'message': 'commit successfully'})


# /orders/pay
class OrderPayView(View):

    # 前端采用Ajax post请求 传递参数：订单id(order_id)
    def post(self, request):
        order_id = request.POST.get('order_id')
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        # 查询订单
        try:
            order = OrdersInfo.objects.get(order_id=order_id, user=user, pay_method=2)
        except Exception as e:
            print('-----err query OrderInfo -%s' % e)
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
        # 业务处理:使用支付宝SDK接口调用alipay.trade.page.pay

        # 使用alipay-python-sdk
        # 初始化
        alipay = AliPay(
            appid='2021000119697351',
            app_notify_url=None,
            app_private_key_string=open(os.path.join(settings.BASE_DIR, 'apps/orders/app_private_key.pem')).read(),
            alipay_public_key_string=open(os.path.join(settings.BASE_DIR, 'apps/orders/alipay_public_key.pem')).read(),
            sign_type='RSA2',
            debug=True,     # 沙箱环境为True
        )
        # 调用alipay-python-sdk支付接口
        total_amount = order.total_price + order.transit_price  # DecimalField类型
        # 如果你是 Python3 的用户，使用默认的字符串即可
        subject = "天天生鲜-%s" % order_id
        # 电脑网站支付，需要跳转到：https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(total_amount),
            subject=subject,
            return_url=None,
            notify_url=None  # 可选，不填则使用默认 notify url
        )
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


# /orders/check
class OrderCheckView(View):
    # 前端采用Ajax post请求 传递参数：订单id(order_id)
    def post(self, request):
        order_id = request.POST.get('order_id')
        # 用户是否登录
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的订单id'})
        # 查询订单
        try:
            order = OrdersInfo.objects.get(order_id=order_id, user=user, pay_method=2)
        except Exception as e:
            print('-----err query OrderInfo -%s' % e)
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
        # 业务处理:使用支付宝SDK接口调用alipay.trade.page.pay

        # 使用alipay-python-sdk
        # 初始化
        alipay = AliPay(
            appid='2021000119697351',
            app_notify_url=None,
            app_private_key_string=open(os.path.join(settings.BASE_DIR, 'apps/orders/app_private_key.pem')).read(),
            alipay_public_key_string=open(
                os.path.join(settings.BASE_DIR, 'apps/orders/alipay_public_key.pem')).read(),
            sign_type='RSA2',
            debug=True,  # 沙箱环境为True
        )
        # 调用alipay-python-sdk交易查询接口
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            trade_status = response.get('trade_status')
            code = response.get('code')
            print(code)
            print(trade_status)
            if code == '10000' and trade_status == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                trade_no = response.get('trade_no')
                order.trade_no = trade_no
                order.order_status = 3
                order.save()
                # 返回结果
                return JsonResponse({'res': 3, 'message': '支付成功'})
            elif code == '40004' or (code == '10000' and trade_status) == 'WAIT_BUYER_PAY':
                # 当点击去付款后会立马返回40004
                # 交易创建，等待买家付款 或 业务处理失败，可能一会就成功

                import time
                time.sleep(5)
                continue
            else:
                # 支付出错
                return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class CommentView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        user = request.user

        if not order_id:
            return HttpResponseRedirect(reverse('user:user_center_order', kwargs={'page': 1}))

        try:
            order = OrdersInfo.objects.get(order_id=order_id, user=user)
        except Exception as e:
            print('-----err comment query order_info -%s' % e)
            return HttpResponseRedirect(reverse('user:user_center_order', kwargs={'page': 1}))

        # 订单状态标题
        order_status_name = OrdersInfo.ORDER_STATUS[str(order.order_status)]

        # 获取订单商品信息
        order_skus = OrdersGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            # 计算商品小计 动态增加
            order_sku.amount = order_sku.price * order_sku.count
        # 动态给order增加order_skus属性
        order.order_skus = order_skus

        # 前端需要遍历这个对象时,需要动态增加属性,给可迭代对象中的每一个对象都增加这个属性

        return render(request, 'order_comment.html', locals())

    def post(self, request, order_id):
        user = request.user
        comment = request.POST.get('comment')
        if not order_id:
            return HttpResponseRedirect(reverse('user:user_center_order', kwargs={'page': 1}))
        try:
            order = OrdersInfo.objects.get(order_id=order_id, user=user)
        except Exception as e:
            print('-----err comment query order_info -%s' % e)
            return HttpResponseRedirect(reverse('user:user_center_order', kwargs={'page': 1}))

        # 获取评论条数
        total_count = request.POST.get('total_count')
        total_count = int(total_count)

        for i in range(1, total_count + 1):
            # 获取评论商品的id
            sku_id = request.POST.get('sku_%d' % i)     # sku_1 sku_2 sku_3
            # 获取商品的评论内容
            content = request.POST.get('content_%d' % i)     # content_1 content_2 content_3
            try:
                order_goods = OrdersGoods.objects.get(order=order, sku_id=sku_id)
            except Exception as e:
                print('-----err comment query order_goods -%s' % e)
                continue

            order_goods.comment = content
            order_goods.save()
        order.order_status = 4  # 已完成
        order.save()
        return HttpResponseRedirect(reverse('user:user_center_order', kwargs={'page': 1}))

