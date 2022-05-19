from django.contrib import admin
from .models import *
from django.core.cache import cache

# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    """
    自定义admin管理类继承原本的类
    重写增加修改删除时的类方法增加发送celery任务函数
    发送任务让celery worker重新生成静态首页

    """
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 发出celery任务
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        # 清除数据缓存以便让view重新缓存首页数据
        cache.delete('key')

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()
        cache.delete('key')


admin.site.register(GoodsType, BaseModelAdmin)
admin.site.register(GoodsSKU, BaseModelAdmin)
admin.site.register(GoodsSPU, BaseModelAdmin)
admin.site.register(IndexTypeGoods, BaseModelAdmin)
admin.site.register(IndexGoodsBanner, BaseModelAdmin)
admin.site.register(IndexPromotionBanner, BaseModelAdmin)
