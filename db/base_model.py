from django.db import models


class BaseModel(models.Model):
    # 模型抽象基类
    create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name='更新时间', auto_now=True)
    is_delete = models.BooleanField(verbose_name='是否删除', default=False)

    class Meta:
        # 定义该类是抽象基类不会生成数据表，其他类继承此类后会拥有该基类的字段
        abstract = True

