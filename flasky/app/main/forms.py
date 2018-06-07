#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-04 17:24:52
# @Last Modified by:   anchen
# @Last Modified time: 2017-08-01 15:09:21
from flask_wtf import FlaskForm
from wtforms.validators import Required, Length, Regexp, Email, EqualTo
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField, PasswordField
from flask_pagedown.fields import PageDownField
from ..models import User, Role
from wtforms import ValidationError
from flask_login import current_user


class EditProfileForm(FlaskForm):
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    location = StringField(u'位置', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我')
    submit = SubmitField(u'提交')


class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1, 64), Email()])

    username = StringField(u'用户名', validators=[Required(), Length(1, 64),
                                               Regexp('^[A-Za-z0-9_.]*$', 0, u'用户名只能包含字母数字点号和下划线')])

    confirmed = BooleanField(u'是否认证')
    role = SelectField(u'角色', coerce=int)  # WTFFor,s对HTML表单控件<select>进行SelectField包装,从而实现下拉列表,用来在这个表单中选择用户角色。
    name = StringField(u'真实姓名', validators=[Length(0, 64)])
    location = StringField(u'位置', validators=[Length(0, 64)])
    about_me = TextAreaField(u'关于我')
    submit = SubmitField(u'提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.user = user
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已经注册.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已经存在.')


class PostForm(FlaskForm):
    body = PageDownField(u"发表博客", validators=[Required()],render_kw={"placeholder": u"支持markdown格式 可拖动右下角缩放"})
    submit = SubmitField(u'提交')


class CommentForm(FlaskForm):
    body = PageDownField('', validators=[Required()],render_kw={"placeholder": u"支持markdown格式 可拖动右下角缩放"})
    submit = SubmitField(u'提交')
