#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-03 23:28:13
# @Last Modified by:   anchen
# @Last Modified time: 2017-09-17 23:49:46


# 在启动manager.py前,需要启动mysql,redis,消息队列服务
# redis的启动方法：cd到redis目录下,执行redis-server redis.windows.conf
# 启动消息队列celery -A manager.celery worker --loglevel=info
# 所有服务都准备好后,再启动manager.py


'''
markrandom示例：
# 一级标题
## 二级标题
### 三级标题 
*单星号* => 单星号
_单下划线_ => 单下划线
**双星号** => 双星号
__双下划线__ => 双下划线

* item1
* item2
* item3 




* item1
+ item1.1
* item2
+ item2.1 

> 这是一段文字
> 第二行
> 第三行

This is [an example](http://example.com/ “Title”) inline link.
[This link](http://example.net/) has no title attribute. 

![GitHub Mark](http://github.global.ssl.fastly.net/images/modules/logos_page/GitHub-Mark.png "GitHub Mark")

```python
print('Hello!!!')
```



'''

import os
from app import create_app, db, celery
from app.models import User, Role
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


@manager.command
def test():
    """run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def profile(length=25, profile_dir=None):
    """Start the application under the code profile.
        监控哪个函数调用花了多少时间
        源码监控一般在开发环境下使用,生产环境一般不使用,因为这会是程序运行 变慢
    """
    # print 'in profile'
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[
        length], profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """run deployment tasks."""
    from flask_migrate import upgrade
    # 把数据库迁移到最新修订版
    upgrade()
    # 创建用户角色
    Role.insert_roles()
    # 让所有用户都关注此用户
    User.add_self_follows()
    # 生成模拟用户
    User.generate_fake()


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
