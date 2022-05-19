import django.core.paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import *
from django.core.cache import cache
from django_redis import get_redis_connection
from orders.models import OrdersGoods
from django.core.paginator import Paginator
# Create your views here.


def index_view(request):
    # 获取首页种类信息
    goods_types = GoodsType.objects.all()
    # 获取首页轮播商品信息
    goods_banner = IndexGoodsBanner.objects.all().order_by('index')     # 使用index字段排序 默认升序 '-index'代表降序
    # 获取首页促销活动信息
    promotion_banner = IndexPromotionBanner.objects.all().order_by('index')
    # 获取首页分类商品展示信息
    type_goods = IndexTypeGoods.objects.all()
    for i in goods_types:
        i.title_banner = IndexTypeGoods.objects.filter(type=i, display_type=0).order_by('index')
        # 查出i种类的文字展示信息,并添加给i的属性
        i.image_banner = IndexTypeGoods.objects.filter(type=i, display_type=1).order_by('index')
        # 查出i种类的图片展示信息,并添加给i的属性

    # 获取用户购物车商品数量
    user = request.user
    cart_count = 0
    if user.is_authenticated:
        # 连接redis数据库
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        cart_count = conn.hlen(key)
        # Redis hlen() 命令用于获取哈希表中字段的数量

    # print(locals())
    content = {'goods_types': goods_types,
               'goods_banner': goods_banner,
               'promotion_banner': promotion_banner,
               # 'type_goods': type_goods,
               'cart_count': cart_count,
               }

    if cache.get('key') is None:
        # 缓存中没有数据

        value = ''
        # 设置缓存
        # request不能写入cache 所以这里value不能使用locals()
        cache.set('key', content, 3600)

    # return HttpResponse('123')
    return render(request, 'index.html', locals())


def detail_view(request, sku_id):

    # 获取商品信息
    try:
        goods = GoodsSKU.objects.get(id=sku_id)
    except GoodsSKU.DoesNotExist:
        print('商品不存在')
        return HttpResponseRedirect(reverse('goods:index'))
    # 获取商品的分类信息
    types = GoodsType.objects.all()

    # 获取商品的评论信息 comment不为空的
    comment = OrdersGoods.objects.filter(sku=goods.id).exclude(comment='')
    # 获取新品信息 降序 只显示2条
    new_goods = GoodsSKU.objects.filter(type=goods.type).order_by('-create_time')[:2]

    # 获取同一spu的其他规格商品 排除当前sku_id的商品
    other_skus = GoodsSKU.objects.filter(spu=goods.spu).exclude(id=sku_id)

    # 获取用户购物车商品数量
    user = request.user
    cart_count = 0
    if user.is_authenticated:
        # 连接redis数据库
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        cart_count = conn.hlen(key)
        # Redis hlen() 命令用于获取哈希表中字段的数量

        # 添加到用户历史浏览记录
        history_key = 'history_%d' % user.id
        # 先移除用户浏览记录中当前商品的记录，防止在记录中出现重复商品
        conn.lrem(history_key, 0, sku_id)
        # 把商品id添加到列表最左侧
        conn.lpush(history_key, sku_id)
        # 历史记录只保存最新的5条(只保存列表最左侧5条)
        conn.ltrim(history_key, 0, 4)

    return render(request, 'detail.html', locals())


# 需要参数:种类id 页码 排序方式
# /list/种类id/页码?sort=排序方式
def list_view(request, type_id, page):
    # page = request.GET.get(page)

    # 获取种类信息
    try:
        goods_type = GoodsType.objects.get(id=type_id)
    except GoodsType.DoesNotExist:
        print('种类不存在')
        return HttpResponseRedirect(reverse('goods:index'))

    # 获取商品的分类信息
    # list.html 的父模板需要的变量
    types = GoodsType.objects.all()

    # 按排序方式获取分类商品的信息
    sort = request.GET.get('sort', 'default')
    """sort = default 按默认id排序
       sort = price   按商品价格排序
       sort = hot     按商品销量排序
       sort默认为default
    """
    if sort == 'default':
        skus = GoodsSKU.objects.filter(type=goods_type).order_by('-id')
    elif sort == 'price':
        skus = GoodsSKU.objects.filter(type=goods_type).order_by('-price')
    elif sort == 'hot':
        skus = GoodsSKU.objects.filter(type=goods_type).order_by('-sales')

    # 数据分页
    # 实例化Paginator对象
    paginator = Paginator(skus, 1)
    # 获取第page页的数据
    '''
    如果在视图中不执行       # page = request.GET.get(page)      
    直接使用变量 传进来的是str类型
    
    如果执行
    传进来的是'NoneType'类型    不能使用
    
    因为在urls中使用正则匹配整数，不是整数不会进入到这个视图中，
        所以这里不校验直接使用传进来的变量,type_id 也是同理
    
    以下代码不能使用------------
        # 尝试把page转换为整型，如果异常 page默认为1
        try:
            page = int(page)
        except Exception as e:
            print('page err -%s' % e)
            page = 1
    '''

    '''
    这段不需要了
        try:
            skus_page = paginator.page(page)
        except django.core.paginator.EmptyPage as e:
            print(e)
            return HttpResponseRedirect(reverse('goods:index'))
        # 如果页码没有数据302跳转到首页，用下面的方式代替
    '''
    if int(page) > paginator.num_pages:
        # 如果页码数大于数据分页的总页数,说明没有数据,将页数默认page=1
        page = 1
    # 实例化page对象
    skus_page = paginator.page(page)

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

    # 获取新品信息 降序 只显示2条
    new_goods = GoodsSKU.objects.filter(type=goods_type).order_by('-create_time')[:2]
    # 获取用户购物车商品数量
    user = request.user
    cart_count = 0
    if user.is_authenticated:
        # 连接redis数据库
        conn = get_redis_connection('default')
        key = 'cart_%d' % user.id
        cart_count = conn.hlen(key)
        # Redis hlen() 命令用于获取哈希表中字段的数量

    return render(request, 'list.html', locals())
