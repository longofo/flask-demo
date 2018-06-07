#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-15 16:18:42
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-16 15:13:45
from .errors import forbidden
from functools import wraps
from flask import g


def permission_required(permission):
    def decorator(f):
        @wraps(f)  # wraps的作用是保持原来f的属性
        def decorator_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permission')
            return f(*args, **kwargs)

        return decorator_function

    return decorator
