from celery import Celery
from django.core import mail
from django.conf import settings
import time




# 任务处理端需要添加这些代码

import os
# if not os.getenv('DJANGO_SETTINGS_MODULE'):
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dailyfresh.settings')
django.setup()
# celery初始化settings配置
# 初始化django

from django.template import loader
from goods.models import *


# 实例化celery
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/5')


@app.task
def send_register_active_mail(email, username, token):
    subject = '天天生鲜-用户激活'
    message = ''
    email = [email]
    html_message = '<h1>%s，欢迎您注册天天生鲜</h1><br />' \
                   '请点击下面链接激活您的账户<br />' \
                   '<a href="http://127.0.0.1:8000/user/active/%s">' \
                   'http://127.0.0.1:8000/user/active/%s</a>' % (username, token, token)
    mail.send_mail(subject, message, settings.EMAIL_FROM, email, html_message=html_message)
    time.sleep(5)


@app.task
def generate_static_index_html():
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

    # 产生首页静态页面
    temp = loader.get_template('static_index.html')
    static_index_html = temp.render(locals())
    # 生成首页静态页面
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    print(save_path, static_index_html)
    with open(save_path, 'w') as f:
        f.write(static_index_html)

    print('---task is success')

