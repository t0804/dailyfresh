from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin

# Create your views here.


# ajax 发起的请求都在后台， 在浏览器中看不到效果
class CartAddView(View):
    def post(self, request):
        """添加购物车记录"""
        # 接收数据
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：添加购物车记录
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        # 可能用户已经添加过该sku_id的内容
        # 先尝试获取sku_id的值 -> hget cart_key 属性
        cart_count = conn.hget(key, sku_id)
        # 如果没用该属性-返回None
        if cart_count:
            # 如果不是None,累加购物车中商品的数目
            count += int(cart_count)

        # 校验商品库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '超过商品库存'})
        # 设置hash中sku_id对应的值
        # hset->如果sku_id存在->更新;如果不存在->添加
        conn.hset(key, sku_id, count)

        # 计算用户购物车中的商品条目数
        total_count = conn.hlen(key)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': 'Added successfully'})


class CartInfoView(LoginRequiredMixin, View):
    def get(self, request):
        # 获取登录的用户
        user = request.user
        # 获取用户购物车中商品信息

        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        # cart_dict = {'商品id': '商品数量', 'sku_id': 'count'}
        cart_dict = conn.hgetall(key)

        skus = []
        # 保存用户购物车中商品的总件数和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            # 获取对应id的商品信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取对应id的商品的小计
            amount = sku.price * int(count)

            # 动态的给sku对象增加amount属性,保存商品的小计
            sku.amount = amount
            # 动态的给sku对象增加count属性, 保存购物车中对应商品的数量
            sku.count = int(count)
            # 把sku对象添加到列表中
            skus.append(sku)

            # 累加计算商品的总数目和总价格
            total_count += int(count)
            total_price += amount

        return render(request, 'shopping_cart.html', locals())


# /shopping_cart/update
# Ajax post 请求
# 前端需要传递的参数: sku_id, count
class CartUpdateView(View):
    def post(self, request):
        # 购物车记录更新
        # 接收数据
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})
        # 校验添加的商品数
        try:
            count = int(count)
        except Exception:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理：更新购物车记录
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        # 校验商品库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '超过商品库存'})
        # 更新记录
        conn.hset(key, sku_id, count)
        # 统计页面上购物车商品的总件数
        vals = conn.hvals(key)
        total_count = 0
        for val in vals:
            total_count += int(val)
        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': 'Update successfully'})


# /shopping_cart/deleta
# Ajax post 请求
# 前端需要传递的参数: sku_id
class CartDeleteView(View):
    def post(self, request):
        # 购物车记录删除
        # 接收数据
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        sku_id = request.POST.get('sku_id')
        # 数据校验
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 业务处理：删除购物车记录
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        conn.hdel(key, sku_id)

        # 统计页面上购物车商品的总件数
        vals = conn.hvals(key)
        total_count = 0
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 3, 'total_count': total_count, 'message': 'successfully deleted'})

