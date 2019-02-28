FROM python:2.7

RUN apt-get -y update && \
            apt-get -y install libevent-dev && \
            apt-get -y install build-essential && \
            apt-get -y install python-dev && \
            apt-get -y install supervisor && \
            apt-get -y install python-mysqldb && \
            apt-get -y install mysql-client && \
            apt-get -y clean && \
            apt-get -y autoclean && \
            rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


WORKDIR /flask

COPY ./flasky /flask

COPY Songti.ttc /usr/share/fonts

COPY docker-entrypoint.sh /usr/local/bin

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ADD supervisord.conf /etc/supervisord.conf

RUN pip install --upgrade pip && \
            pip install -r ./requirements/prod.txt

# SECRET_KEY:应用密钥
# MAIL_USERNAME:邮箱账户
# MAIL_PASSWORD:第三方授权码,对于qq用户需要开启smtp服务,第三方会给一个授权码
# FLASKY_ADMIN:应用管理员账号
# FLASKY_POSTS_PER_PAGE:每一页显示多少文章,默认20
# FLASKY_FOLLOWERS_PER_PAGE:每一页显示多少跟随着,默认20
# FLASKY_COMMENTS_PER_PAGE:每一页显示多少评论,默认20
# SESSION_STORAGE_HOST:session存储的host,默认localhost
# CELERY_BROKER_NAME:celery异步处理时存储的host,默认localhost
# SITE_DOMAIN:网站域名,默认localhost
# DATABASE_URL:数据库连接url,默认'mysql://root:123456@localhost:3306/flask?charset=utf8'
# FLASK_CONFIG:配置环境,默认default(开发环境)
ENV SECRET_KEY='hard to guess string' \
          MAIL_USERNAME='' \
          MAIL_PASSWORD='' \
          FLASKY_ADMIN='' \
          FLASKY_POSTS_PER_PAGE=20 \
          FLASKY_FOLLOWERS_PER_PAGE=20 \
          FLASKY_COMMENTS_PER_PAGE=20 \
          SESSION_STORAGE_HOST='redis' \
          CELERY_BROKER_NAME='redis' \
          SITE_DOMAIN='120.77.202.221' \
          DATABASE_URL='mysql://root:123456@mysql:3306/flask?charset=utf8mb4' \
          FLASK_CONFIG='production' \
          C_FORCE_ROOT='true'

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
