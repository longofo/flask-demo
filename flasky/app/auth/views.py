#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-07 15:42:44
# @Last Modified by:   anchen
# @Last Modified time: 2018-03-08 14:46:29
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import render_template, redirect, request, url_for, flash, make_response, session, send_from_directory, \
    current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import auth
from ..models import User
from .forms import LoginForm, LoginImgCodeForm, RegistrationForm, ChangePasswordForm, PasswordResetRequestForm, \
    PasswordResetForm, EmailChangeRequestForm, RecognitionForm
from .. import db
from ..email import send_mail
from ..utils_cn import generate_verification_cn_code
from ..utils_en import check_remote_login, check_is_locked, lift_ban
from datetime import datetime
import time


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        username = current_user.username
    else:
        username = '***'

    # 检测ip or session是否被封并记录日志
    ip_ban = False
    ip = request.headers.get('X-Real-IP') or request.remote_addr
    info_format = 'user {username} request {url} from {ip} referer {referer},islocked {lock}'
    if check_is_locked(ip, request.cookies.get('session')):
        ip_ban = True
        if request.endpoint not in ['main.download_file', 'auth.recognition', 'auth.get_verify_code']:
            current_app.logger.info(info_format.format(
                username=username, url=request.url, ip=ip,
                referer=request.referrer, lock=ip_ban))
            return redirect(url_for('auth.recognition'))
    current_app.logger.info(info_format.format(
        username=username, url=request.url, ip=ip,
        referer=request.referrer, lock=ip_ban))

    if current_user.is_authenticated:
        '''
        如果session中的login_token与数据库中的session不一致,
        说明在其他地方进行了登录,当前的login_token被覆盖了。
        '''
        if not current_user.check_status(session.get('login_token')):
            logout_user()
            flash(u'你已在其他地方登录')
            return redirect(url_for('auth.login'))

        current_user.ping()
        if not current_user.confirmed and request.endpoint and \
                request.endpoint[:5] != 'auth.' and request.endpoint != 'main.download_file':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/HumanOrMachineRecognition', methods=['GET', 'POST'])
def recognition():
    if not check_is_locked(request.headers.get('X-Real-IP') or request.remote_addr, request.cookies.get('session')):
        return redirect(url_for('main.index'))
    form = RecognitionForm()
    if form.validate_on_submit():
        if not session.get('code_text') or form.verification_code.data != session['code_text']:
            flash(u'验证码错误')
        else:
            lift_ban(request.headers.get('X-Real-IP'),
                     request.cookies.get('session'))
            return redirect(url_for(request.args.get('next') or 'main.index'))
    return render_template('auth/recognition.html', form=form)


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/VerifyCode')
def get_verify_code():
    # 把strs发给前端,或者在后台使用session保存
    # code_img, code_text = utils.generate_verification_code()
    code_img, code_text = generate_verification_cn_code()
    session['code_text'] = code_text
    response = make_response(code_img)
    response.headers['Content-Type'] = 'image/jpeg'
    return response


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # 发现这种方式验证不安全,所以取消了。如果要做到安全需要在数据库记录用户登录次数，然后结合js。
    # if "login_count" not in session:
    #     session['login_count'] = 0
    # else:
    #     session['login_count'] += 1

    # if session['login_count'] <= 3:
    #     form = LoginForm()
    # else:
    if current_user.is_authenticated:
        return redirect(request.args.get('next') or url_for('main.index'))

    form = LoginImgCodeForm()

    if form.validate_on_submit():
        if not session.get('code_text') or session.get('code_text') != form.verification_code.data:
            flash(u'验证码错误')
        else:
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.verify_password(form.password.data):
                login_user(user, form.remember_me.data)

                # 异地登录提醒
                if user.login_ip:
                    info = check_remote_login(
                        user.login_ip, request.headers.get('X-Real-IP'))
                    if info:
                        flash(info)
                # 保存token到session
                s = Serializer(current_app.config['SECRET_KEY'])
                login_token = s.dumps(
                    {'user_id': user.id, 'login_time': str(time.time()),
                     'login_ip': request.headers.get('X-Real-IP')}).decode()
                session['login_token'] = login_token
                # 更新用户登录的token
                user.login_token = login_token
                user.login_ip = request.headers.get('X-Real-IP')
                db.session.add(user)
                db.session.commit()

                return redirect(request.args.get('next') or url_for('main.index'))
            else:
                flash(u'用户名或密码错误')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'你已经登出')
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        # keyDict = {
        #     'username':user.username,
        #     'token':token
        # }
        send_mail(user.email, 'Confirm Your Account',
                  'auth/email/confirm', user=user, token=token)
        flash(u'认证连接已经发送到你的邮箱,请注意查看.认证前请先登录')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash(u'你已经认证了你的账户,感谢!')
    else:
        flash(u'认证链接错误或已经过期.')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confiremation():
    token = current_user.generate_confirmation_token()
    # keyDict = {
    #         'username':user.username,
    #         'token':token
    #     }
    send_mail(current_user.email, 'Confirm Your Account',
              'auth/email/confirm', user=current_user, token=token)
    flash(u'新的认证链接已经发送到你的邮箱.')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = form.newPassword.data
        db.session.add(current_user)
        db.session.commit()
        flash(u'你的密码已经修改!')
        return redirect(url_for('main.index'))
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset-password', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_confirmation_token()
            #     keyDict = {
            #     'username':user.username,
            #     'token':token,
            #     'next':request.args.get('next')
            # }
            send_mail(user.email, 'reset your password', 'auth/email/reset_password',
                      user=user, token=token, next=request.args.get('next'))
            flash(u'重置密码链接已经发送到你的邮箱.')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.reset_password(token, form.newPassword.data):
                flash(u'你的密码已经更新.')
                return redirect(url_for('auth.login'))
            else:
                flash(u'token 错误!')
                return redirect(url_for('auth.password_reset', token=token))
        return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = EmailChangeRequestForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data
            token = current_user.generate_email_change_token(
                new_email=new_email)
            # keyDict = {
            #     'username':current_user.username,
            #     'token':token
            # }
            send_mail(new_email, 'Confirm your email address',
                      'auth/email/change_email', user=current_user, token=token)
            flash(u'修改邮箱链接已经发送到你的新邮箱.')
        else:
            flash(u'密码错误.')
        return redirect(url_for('main.index'))
    return render_template('auth/change_email.html', form=form)


@auth.route('/change-email/<token>', methods=['GET', 'POST'])
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash(u'你的邮箱已经修改.')
    else:
        flash(u'错误的请求.')
    return redirect(url_for('main.index'))
