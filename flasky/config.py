#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-03 23:28:13
# @Last Modified by:   anchen
# @Last Modified time: 2018-03-03 15:35:51
import os
import datetime


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'

    # 每次请求结束后会自动db.session.commit()写入数据库
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # 如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存， 如果不必要的可以禁用它。
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 邮箱配置信息
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = '465'
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # 第三方授权码,不是邮箱密码,需要在第三方开启邮箱服务,第三方会提供一个授权码
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = os.environ.get('FLASKY_ADMIN')
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    FLASKY_POSTS_PER_PAGE = int(os.environ.get('FLASKY_POSTS_PER_PAGE') or 20)
    FLASKY_FOLLOWERS_PER_PAGE = int(os.environ.get(
        'FLASKY_FOLLOWERS_PER_PAGE') or 20)
    FLASKY_COMMENTS_PER_PAGE = int(os.environ.get(
        'FLASKY_COMMENTS_PER_PAGE') or 20)

    # 可以用于显式地禁用或者启用查询记录,在调试或者测试时可以开启
    SQLALCHEMY_RECORD_QUERIES = True

    # 查询超时的记录
    FLASKY_DB_QUERY_TIMEOUT = 0.5
    PROFILE = True

    # 默认关闭SSL
    SSL_DISABLE = True

    # Session配置
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    # Whether sign the session cookie sid or not, if set to True, you have to set flask.Flask.secret_key, default to be False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'session:'
    # the lifetime of a permanent session as datetime.timedelta object. Starting with Flask 0.8 this can also be an integer representing seconds.
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(seconds=30 * 60)
    SESSION_STORAGE_HOST = os.environ.get(
        'SESSION_STORAGE_HOST') or 'localhost'
    SESSION_STORAGE_PORT = 6379

    # 后台任务处理框架celery的配置
    CELERY_BROKER_NAME = os.environ.get('CELERY_BROKER_NAME') or 'localhost'
    CELERY_BROKER_URL = 'redis://{0}:6379/0'.format(CELERY_BROKER_NAME)
    CELERY_RESULT_BACKEND = 'redis://{0}:6379/0'.format(CELERY_BROKER_NAME)

    # 网站域名
    SITE_DOMAIN = os.environ.get('SITE_DOMAIN') or 'localhost'

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql://root:123456@127.0.0.1:3306/test?charset=utf8mb4'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'mysql://root:123456@127.0.0.1:3306/test1?charset=utf8mb4'


class ProductionConfig(Config):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE')) or False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql://root:123456@127.0.0.1:3306/test?charset=utf8mb4'  # 这里mysql数据库使用的和Dev里面是同一个,只是为了方便，因为在做Dev是里面有些数据，拿来测试用。可以设施为其他的

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 把错误通过电子邮件发送给管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_SSL', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + 'Application Error',
            credentials=credentials,
            secure=secure
        )
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
