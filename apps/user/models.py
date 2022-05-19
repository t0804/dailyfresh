from django.db import models
from db.base_model import BaseModel
from django.contrib.auth.models import AbstractUser


# Create your models here.

class User(AbstractUser, BaseModel):
    # 用户表
    # 使用django内建用户系统并继承BaseModel

    class Meta:
        db_table = 'df_user'    # 定义表名
        verbose_name = '用户'     # admin后台显示的表名称
        verbose_name_plural = verbose_name      # admin后台显示的表名称_复数


class AddressManager(models.Manager):
    # 地址模型管理器类
    def get_default_address(self, user):
        # 自定义模型管理器方法-获取默认地址
        # 如果获取到返回address对象
        # 如果获取不到返回None
        try:
            address_obj = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            address_obj = None
        return address_obj


class Address(BaseModel):
    # 用户地址表

    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='所属用户')
    receiver = models.CharField(verbose_name='收件人', max_length=20)
    address = models.CharField(verbose_name='收件地址', max_length=256)
    zip_code = models.CharField(verbose_name='邮编', max_length=6, null=True)  # 该列可以为空
    phone = models.CharField(verbose_name='联系方式', max_length=11)
    is_default = models.BooleanField(verbose_name='是否默认', default=False)

    objects = AddressManager()

    class Meta:
        db_table = 'df_user_address'
        verbose_name = '用户地址表'
        verbose_name_plural = verbose_name
