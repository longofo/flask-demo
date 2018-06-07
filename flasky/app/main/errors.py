#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-04 16:05:04
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-15 16:31:57

from flask import render_template, request, jsonify, current_app
from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)  # 如果使用errorhandler修饰器,那么只有蓝本中的错误才能触发处理程序。要想在全局触发错误处理程序，必须使用app_errorhandler
def internal_server_error(e):
    current_app.logger.error(e, exc_info=True)
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'Internal Server Error'})
        response.status_code = 500
        return response
    return render_template('500.html'), 500
