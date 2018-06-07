#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-07 16:08:31
# @Last Modified by:   anchen
# @Last Modified time: 2017-07-28 23:08:21
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from ..models import User
from wtforms import ValidationError
from flask_login import current_user


class LoginForm(FlaskForm):
    '''
    登录表单
    一个邮件地址文本字段,一个密码字段,一个"记住我"复选框,一个提交按钮
    PasswordField类表示属性为type="password"的<input>元素
    '''
    email = StringField('Email', validators=[
        Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class LoginImgCodeForm(FlaskForm):
    '''
    登录表单
    一个邮件地址文本字段,一个密码字段,一个"记住我"复选框,一个提交按钮
    PasswordField类表示属性为type="password"的<input>元素
    '''
    email = StringField('Email', validators=[
        Required(), Length(1, 64), Email()])
    password = PasswordField(u'密码', validators=[Required()])
    verification_code = StringField(
            u'验证码', validators=[Required(message=u'需填验证码'), Length(4, 4, message=u'填写4位验证码')])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField(u'登录')


class RegistrationForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email()])
    username = StringField(u'用户名', validators=[Required(), Length(
            1, 64), Regexp('^[A-Za-z0-9_.]*$', 0, u'用户名只能包含字母数字点号和下划线')])
    password = PasswordField(
            u'密码', validators=[Required(), EqualTo('password2', message=u'两次输入必须相同.')])
    password2 = PasswordField(u'重复密码', validators=[Required()])
    submit = SubmitField(u'注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已经存在.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(u'用户已经存在.')

    '''
    如果表单类定义了以validate_开头的且后面跟着字段名的方法,这个方法就和常规的验证函数一起调
    用。如果想表示验证失败，可以抛出ValidationError异常，参数就是错误消息。
    '''


class ChangePasswordForm(FlaskForm):
    oldPassword = StringField(u'旧密码', validators=[Required()])

    newPassword = PasswordField(
            u'新密码', validators=[Required(), EqualTo('newPassword2', message=u'两次输入必须相同.')])
    newPassword2 = PasswordField(u'重复密码', validators=[Required
                                                      ()])
    submit = SubmitField(u'提交')

    def validate_oldPassword(self, field):
        if not current_user.verify_password(field.data):
            raise ValidationError(u'旧密码错误')


class PasswordResetRequestForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField(u'提交')


class PasswordResetForm(FlaskForm):
    email = StringField(u'邮箱', validators=[Required(), Length(1, 64), Email()])
    newPassword = PasswordField(
            u'新密码', validators=[Required(), EqualTo('newPassword2', message=u'两次输入必须相同.')])
    newPassword2 = PasswordField(u'重复密码', validators=[Required()])
    submit = SubmitField(u'提交')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱错误!')


class EmailChangeRequestForm(FlaskForm):
    email = StringField(u'新邮箱', validators=[
        Required(), Length(1, 64), Email()])
    password = PasswordField(u'你现在的密码', validators=[Required()])
    submit = SubmitField(u'提交')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(u'邮箱已经注册.')


class RecognitionForm(FlaskForm):
    verification_code = StringField(
            u'验证码', validators=[Required(message=u'需填验证码'), Length(4, 4, message=u'填写4位验证码')])
    submit = SubmitField(u'提交')
