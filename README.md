###dailyfresh
###Django-天天生鲜项目

使用了用户内建系统

使用celery异步处理发送激活邮件和生成静态页面
仅支持支付宝支付，且是沙箱环境，正是环境需要更改连接为https://openapi.alipay.com/gateway.do



####server
    
    mysql-server    192.168.47.131:3306
    
    nginx-fdfs      192.168.47.131:8888
    
    redis-server    192.168.47.131:6379
    redis_cache     192.168.47.131:6379/3
    redis_celery_borker     192.168.47.131:6379/5
    
    fdfs_trackerd   192.168.47.131:22122
    /etc/fdfs/tracker.conf
    fdfs_storaged
    /etc/fdfs/storage.conf
    
    celery_worker   192.168.47.131
    uwsgi 192.168.47.131:8080

###admin superuser
    
    admin   
    123456

###mysql
    
    root
    123456

###nginx静态页面
192.168.47.131/
###nginx
192.168.47.131

