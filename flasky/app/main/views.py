#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: anchen
# @Date:   2017-07-04 16:04:18
# @Last Modified by:   anchen
# @Last Modified time: 2017-09-23 22:42:33

from datetime import datetime
from flask import render_template, session, redirect, url_for, current_app, flash, request, abort, make_response, \
    send_from_directory
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Role, Permission, Post, Comment
from ..decorators import admin_required, permission_required
from flask_sqlalchemy import get_debug_queries
from sqlalchemy import or_
import os
from ..utils_en import Pagination


@main.before_request
def main_bofore_request():
    # 改为在nginx上面进行检测
    # user-agent检测
    # user_agent = request.user_agent
    # if not check_user_agent(user_agent.platform, user_agent.browser, user_agent.version):
    #     abort(403)

    if request.args.get('page', 1, type=int) >= 2:
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))


# 有的浏览器会默认发出get /favicon.ico的请求,没有对应的view会404
@main.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(
        current_app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


# 防盗链
@main.route("/static/<filepath>", methods=['GET'])
def download_file(filepath):
    # print u'static文件'
    # 此处的filepath是文件的路径，但是文件必须存储在static文件夹下
    if not request.referrer or current_app.config['SITE_DOMAIN'] not in request.referrer:
        return current_app.send_static_file("403.jpg"), 403
    return current_app.send_static_file(filepath)  # 或者send_file


@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    show = request.cookies.get('show', 1, type=int)

    if show in [2] and not current_user.is_authenticated or int(show) > 3 or int(show) < 1:
        show = 1

    # 为了分页显示记录,要把all()换成Flask-SQLAlchemy提供的paginate()方法。页数是paginate()方法的第一个参数，也是唯一必须的参数。可选参数per_page用来指定每一页显示的记录数量;没指定默认20个记录。error_out,当为True时(默认),如果请求页数超出范围,则会返回404错误;如果为False,超出时返回空列表。
    # 这样修改之后,首页只会显示有限数量的文章。若想查看第二页,则要在浏览器地址中的url之后加上查询字符串?page=2
    # 也可以使用自定义的分页

    if show == 1:
        query = Post.query.order_by(Post.timestamp.desc())
        pagination = query.paginate(
            page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
    elif show == 2:
        query = current_user.followed_posts.order_by(Post.timestamp.desc())
        pagination = query.paginate(
            page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
    elif show == 3:
        posts, count = Post.get_click_top(page)
        pagination = Pagination(
            page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], count=count)
    return render_template('index.html', form=form, posts=posts,
                           show=show, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)

    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts, pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash(u'你的信息已经更新.')
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.name
    form.about_me.data = current_user.about_me
    form.location.data = current_user.location
    return render_template('edit_profile.html', form=form)


@main.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash(u'用户信息已经更新.')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    post.inc_click()
    form = CommentForm()
    if form.validate_on_submit() and current_user.can(Permission.COMMENT):
        comment = Comment(body=form.body.data, post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash(u'你的评论已经发表.')
        return redirect(url_for('main.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    resp = make_response(render_template('post.html', posts=[
        post], form=form, comments=comments, pagination=pagination))
    resp.set_cookie('moderate', '', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash(u'博客已经更新.')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'错误的用户.')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash(u'你已经关注了这个用户.')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash(u'你关注了 %s.' % username)
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'错误的用户')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash(u'你没有关注此用户.')
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    flash(u'你已取消关注 %s.' % username)
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, titile="Followers of",
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'错误的用户.')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title='Followed by',
                           endpoint='main.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/post/all')
def show_all():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show', '1', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/post/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show', '2', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/post/post_click_top')
def post_click_top():
    resp = make_response(redirect(url_for('main.index')))
    resp.set_cookie('show', '3', max_age=30 * 24 * 60 * 60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    resp = make_response(render_template(
        'moderate.html', comments=comments, pagination=pagination))
    resp.set_cookie('moderate', '1', 30 * 24 * 60 * 60)
    return resp


@main.route('/moderate-enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    if request.cookies.get('moderate'):
        return redirect(url_for('main.moderate', page=request.args.get('page', 1, type=int)))
    return redirect(url_for('main.post', id=comment.post.id, page=request.args.get('page', 1, type=int)))


@main.route('/moderate-disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    if request.cookies.get('moderate'):
        return redirect(url_for('main.moderate', page=request.args.get('page', 1, type=int)))
    return redirect(url_for('main.post', id=comment.post.id, page=request.args.get('page', 1, type=int)))


@main.route('/my-post/', methods=['GET', 'POST'])
@login_required
def my_post():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.my_post'))
    page = request.args.get('page', 1, type=int)
    query = Post.query.filter_by(author_id=current_user.id)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('mypost.html', form=form, posts=posts,
                           pagination=pagination)


@main.route('/search/')
def search():
    q = request.args.get('q')
    questions = '' if not q else q.split(' ')
    contain_any = []
    user_contain_lst = [User.username.contains(q) for q in questions]
    post_contain_lst = [Post.body.contains(q) for q in questions]
    contain_any.extend(post_contain_lst)
    contain_any.extend(user_contain_lst)
    condition = or_(*contain_any)
    page = request.args.get('page', 1, int)
    # pagination = Post.query.filter(condition).order_by(Post.timestamp.desc()).paginate(page=page,\
    #                                 per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],\
    #                                 error_out=False)
    pagination = Post.query.join(User, User.id == Post.author_id).filter(condition).order_by(
        Post.timestamp.desc()).paginate(page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                        error_out=False)
    posts = pagination.items
    return render_template('search_result.html', posts=posts, pagination=pagination, q=q)


@main.route('/delete_post/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    post.delete_post_click()
    if current_user != post.author and not current_user.is_administrator():
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash(u'文章已删除.')
    return redirect(request.args.get('next') or url_for('main.index'))


@main.after_app_request
def after_request(response):
    # print 'after request'
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_DB_QUERY_TIMEOUT']:
            current_app.logger.warning('Slow query:%s\nParamenters:%s\nDuration:%fs\nContext:%s\n' % (
                query.statement, query.parameters, query.duration, query.context))
    return response
