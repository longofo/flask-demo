#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-04 17:49:21
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-09 22:21:31
import unittest
from flask import current_app
from app import create_app,db

class BasicTestCase(unittest.TestCase):
    '''
    这个测试使用python标准库中的unittest包编写。setUp()和tearDown()方法分别在各测试前后运行,并且名字以test_开头的函数都作为测试执行。
    '''
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    def test_app_exists(self):
        self.assertFalse(current_app is None)
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])