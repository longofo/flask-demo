#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-07 15:27:53
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-09 22:45:41
import unittest
import time
from app import create_app,db
from app.models import User,AnonymousUser,Permission,Role

class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    def test_password_setter(self):
        u = User(password='test')
        self.assertTrue(u.password_hash is not None)
    def test_password_verifycation(self):
        u = User(password='test')
        self.assertTrue(u.verify_password('test'))
        self.assertFalse(u.verify_password('test1'))
    def test_password_salts_are_random(self):
        u = User(password='test')
        u1 = User(password='test')
        self.assertTrue(u.password_hash != u1.password_hash)
    def test_roles_and_permissions(self):
        u = User(email='wu@example.com',password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARITICLES))
        self.assertFalse(u.can(Permission.MODFRATE_COMMENTS))
    def test_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))