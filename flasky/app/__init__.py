#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-03 23:23:20
# @Last Modified by:   anchen
# @Last Modified time: 2017-08-04 23:50:07

from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_session import Session
from config import config, Config
from celery import Celery
import logging
import redis

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy(use_native_unicode="utf8")
pagedown = PageDown()

login_manager = LoginManager()
# 这个属性可以设置None、basic、strong,提供不同的安全等级防止用户会话遭篡改。设置为strong时，Flask_login会记录客户端IP地址和浏览器的用户代理信息，发现异常就登出用户
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'  # 设置登录页面的端点,由于登录路由在蓝本中定义,所以要加上蓝本名字

# celery
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)

# logger access
handler = logging.FileHandler(
    'access.log', mode='a', encoding='UTF-8', delay=0)
handler.setLevel(logging.INFO)
logging_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(logging_format)
# logger error
error_handler = logging.FileHandler(
    'error.log', mode='a', encoding='UTF-8', delay=0)
error_handler.setLevel(logging.ERROR)
logging_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
error_handler.setFormatter(logging_format)


# redis连接池
pool = redis.ConnectionPool(
    host=Config.SESSION_STORAGE_HOST, port=Config.SESSION_STORAGE_PORT)

# Session
sess = Session()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    app.config['SESSION_REDIS'] = redis.Redis(connection_pool=pool)
    config[config_name].init_app(app)

    # logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.addHandler(error_handler)

    # 插件初始化
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    sess.init_app(app)

    celery.conf.update(app.config, accept_content=['json', 'pickle'])

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    '''注册蓝本时使用的url_prefix是可选参数。如果使用了这个参数，注册后蓝本中定义的所有路由都会加指定的前缀，即这个例子中的/auth。例如，/login路由会注册成/auth/login，在开发Web服务器中，完整的
    URL就变成了http://localhost:5000/auth/login。
    '''
    # from .api_1_0 import api as api_1_0_blueprint
    # app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    # 安全HTTP配置,在生产环境中使用,如果使用了nginx这样的反向代理,不要使用如下配置
    # if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
    #     from flask_sslify import SSLify
    #     sslify = SSLify(app)

    #     from werkzeug.contrib.fixers import ProxyFix
    #     app.wsgi_app = ProxyFix(app.wsgi_app)

    return app
