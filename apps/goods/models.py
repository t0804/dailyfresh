from django.db import models
from tinymce.models import HTMLField
from db.base_model import BaseModel


# Create your models here.

class GoodsType(BaseModel):
    # 商品种类表
    name = models.CharField(verbose_name='种类名称', max_length=20)
    logo = models.CharField(verbose_name='种类标识', max_length=20)
    image = models.ImageField(verbose_name='种类图片', upload_to='goods_type')

    class Meta:
        db_table = 'df_goods_type'
        verbose_name = '商品种类表'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSPU(BaseModel):
    # 商品SPU表
    name = models.CharField(verbose_name='商品SPU名称', max_length=20)
    detail = HTMLField(blank=True, verbose_name='商品详情')
    # TODO 待解决 admin后台不能编辑

    class Meta:
        db_table = 'df_goods_spu'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsSKU(BaseModel):
    # 商品SKU表
    STATUS_CHOICE = (
        (0, '下线'),
        (1, '上线')
    )
    name = models.CharField(verbose_name='商品名称', max_length=20)
    description = models.CharField(verbose_name='商品简介', max_length=256)
    price = models.DecimalField(verbose_name='商品单价', max_digits=10, decimal_places=2)
    unite = models.CharField(verbose_name='商品单位', max_length=10)
    image = models.ImageField(verbose_name='商品图片', upload_to='goods_sku')
    stock = models.IntegerField(verbose_name='商品库存', default=1)
    sales = models.IntegerField(verbose_name='商品销量', default=0)
    status = models.SmallIntegerField(verbose_name='商品状态', default=1, choices=STATUS_CHOICE)

    type = models.ForeignKey(to='GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    spu = models.ForeignKey(to='GoodsSPU', verbose_name='商品SPU', on_delete=models.CASCADE)

    class Meta:
        db_table = 'df_goods_sku'
        verbose_name = '商品SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsImage(BaseModel):
    # 商品图片表
    image = models.ImageField(upload_to='goods_sku', verbose_name='商品图片')

    sku = models.ForeignKey(to='GoodsSKU', verbose_name='商品图片', on_delete=models.CASCADE)

    class Meta:
        db_table = 'df_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name


class IndexGoodsBanner(BaseModel):
    # 首页轮播商品表
    image = models.ImageField(upload_to='banner', verbose_name='商品图片')
    index = models.SmallIntegerField(default=0, verbose_name='轮播顺序')

    sku = models.ForeignKey(to='GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)

    class Meta:
        db_table = 'df_index_banner'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name


class IndexTypeGoods(BaseModel):
    # 首页分类商品展示表
    DISPLAY_TYPE_CHOICE = ((0, '标题'), (1, '图片'))
    display_type = models.SmallIntegerField(verbose_name='展示类型', default=0, choices=DISPLAY_TYPE_CHOICE)
    index = models.SmallIntegerField(default=0, verbose_name='展示顺序')

    sku = models.ForeignKey(to='GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    type = models.ForeignKey(to='GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)

    class Meta:
        db_table = 'df_index_type_goods'
        verbose_name = '首页分类商品展示'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.sku.name + str(self.display_type)


class IndexPromotionBanner(BaseModel):
    # 首页促销活动表
    name = models.CharField(verbose_name='活动名称', max_length=20)
    image = models.ImageField(verbose_name='商品图片', upload_to='banner')
    # url = models.URLField(verbose_name='活动URL')
    url = models.CharField(max_length=256, verbose_name='活动URL')
    index = models.SmallIntegerField(verbose_name='展示顺序', default=0)

    class Meta:
        db_table = 'df_index_promotion'
        verbose_name = '主页促销活动'
        verbose_name_plural = verbose_name

