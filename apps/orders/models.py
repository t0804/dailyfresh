from django.db import models
from db.base_model import BaseModel


# Create your models here.

class OrdersInfo(BaseModel):
    PAY_METHOD = {
        '0': '货到付款',
        '1': '微信支付',
        '2': '支付宝支付',
        '3': '银联支付',
    }
    ORDER_STATUS = {
        '0': '待支付',
        '1': '待发货',
        '2': '待收货',
        '3': '待评价',
        '4': '已完成',
    }
    PAY_METHOD_CHOICE = (
        (0, '货到付款'), (1, '微信支付'), (2, '支付宝支付'), (3, '银联支付')
    )
    ORDER_STATUS_CHOICE = (
        (0, '待支付'), (1, '待发货'), (2, '待收货'), (3, '待评价'), (4, '已完成')
    )

    # 订单信息表
    order_id = models.CharField(verbose_name='订单号', max_length=128, primary_key=True)
    # 订单号设置为主键
    pay_method = models.SmallIntegerField(verbose_name='支付方式', default=0, choices=PAY_METHOD_CHOICE)
    total_count = models.IntegerField(verbose_name='商品数量', default=1)
    total_price = models.DecimalField(verbose_name='总金额', decimal_places=2, max_digits=10)
    transit_price = models.DecimalField(verbose_name='运费', decimal_places=2, max_digits=10)
    order_status = models.SmallIntegerField(verbose_name='支付状态', default=0, choices=ORDER_STATUS_CHOICE)
    trade_no = models.CharField(verbose_name='支付单号', null=True, default=None, max_length=128)

    user = models.ForeignKey('user.User', on_delete=models.CASCADE, verbose_name='用户')
    address = models.ForeignKey(to='user.Address', on_delete=models.CASCADE, verbose_name='地址')

    class Meta:
        db_table = 'orders_info'
        verbose_name = '订单信息表'
        verbose_name_plural = verbose_name


class OrdersGoods(BaseModel):
    # 订单商品表
    count = models.IntegerField(default=1, verbose_name='商品数量')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='商品价格')
    comment = models.CharField(max_length=256, verbose_name='评论', default='')

    order = models.ForeignKey(to='OrdersInfo', verbose_name='订单号', on_delete=models.CASCADE)
    sku = models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)

    class Meta:
        db_table = 'orders_goods'
        verbose_name = '订单商品表'
        verbose_name_plural = verbose_name
