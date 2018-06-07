#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-03 23:22:54
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-11 01:21:45

from flask import Blueprint

# 蓝本的构造函数有两个必须的参数,蓝本的名字和蓝本所在包或模块。大多数情况下第二个参数使用python的__name__即可
main = Blueprint('main', __name__)

# 导入这两个模块就能把路由和错误处理程序关联起来。注意:这些模块在app/main/__init__.py的末尾导入,这是为了避免循环导入依赖,因为在views.py和errors.py中还要导入蓝本main
from . import views, errors
from ..models import Permission

'''这个函数使得Permission中的常量在模板中全局可用'''


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
