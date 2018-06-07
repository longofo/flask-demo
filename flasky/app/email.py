#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-03 23:24:13
# @Last Modified by:   anchen
# @Last Modified time: 2017-08-12 12:52:22
from flask import current_app, render_template
from flask_mail import Message
from . import mail, celery, create_app


# 启动消息服务,在manager.py所在目录下启动
# celery -A manager.celery worker --loglevel=info


@celery.task(serializer='pickle')
def send_async_email(msg):
    app = create_app('default' or 'development')
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, **kwargs):
    # 这里调用send_email.delay()时参数如果报错对象不能json,那么可以使用如下几种方法:
    # 1.
    # @celery.task
    # def send_async_email(message_details):
    #     with app.app_context():
    #         msg = Message(message_details['subject'],
    #                       message_details['recipients'])
    #         msg.body = message_details['body']
    #         print type(msg)
    #         print dir(msg)
    #         print 'msg.send'
    #         print msg.send
    #         print 'msg'
    #         print msg
    #         mail.send(msg)
    # 2.
    # app.config.update(
    # accept_content=['json','pickle']
    # )

    # then,

    # @celery.task(serializer='pickle')
    # def send_async_email(msg):
    #      pass
    # 3.
    # pip uninstall Flask-Mail
    # pip install Flask-Mail==0.9.0
    app = current_app._get_current_object()
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' ' + subject, sender=app.config['FLASKY_MAIL_SENDER'],
                  recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)

    send_async_email.delay(msg)
    # 直接用多线程并发不高
    # thr = Thread(target=send_async_email,args=(app,msg))
    # thr.start()
