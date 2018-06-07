#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-07 15:40:39
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-07 15:42:14
from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
