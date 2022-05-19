from django.contrib.auth.decorators import login_required


# 登录验证mixin
class LoginRequiredMixin(object):
    # 重写as_view
    @classmethod
    def as_view(cls, **initkwargs):
        # 调用父类的as_view
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        # 返回时用login_required装饰
        return login_required(view)
