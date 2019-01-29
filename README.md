## 说明

博客是根据*《Flask Web开发：基于Python的Web应用开发实战》*开发的,并在此基础上添加一些新功能功能和安全措施:
* 添加了搜索功能
* 文章点击量排行功能
* 添加了反爬虫措施
    * User-Agent检测
    * Referer检测
    * ip请求频率过快封ip
    * session请求频率过快封session
    * 验证码
* 增加了某些页面或者需要访问更多页面必须登录的限制
* 异地登录提醒
* 如果已经登录没退出,再登录会使前面已经登录的退出
* session过期提醒,及时保存当前页面工作
* 使用openssl生成自签名证书,用https加密传输
* 其他...


## 使用docker搭建

### Setp1:

安装docker

### Setp2:

git clone [https://github.com/



/flask-demo.git](https://github.com/longofo/flask-demo.git)

### Step3:

在项目根目录下运行:
docker-compose up -d
        
### Step4:

可以在主机上配置nginx作为反向代理,配置看手动搭建相关部分

## 手动搭建

### Step1

安装
* mysql: 5.7.13
* redis: 3.2.100
* python环境: 2.7
* centos: 7.4
注：使用virtualenv创建python隔离环境更好

运行以下命令为安装某些python库做准备:
```bash
yum update
yum install -y libevent-dev
yum install -y python-dev
yum install MySQL-python
```

### Step2

* git clone https://github.com/longofo/flask-demo.git
* 切换到flasky目录下
* 在项目requirements文件夹下 pip install -r prod.txt
* 添加以下环境变量:
    * SECRET_KEY:应用密钥
    * MAIL_USERNAME:邮箱账户
    * MAIL_PASSWORD:第三方授权码,对于qq用户需要开启smtp服务,第三方会给一个授权码
    * FLASKY_ADMIN:应用管理员账号
    * FLASKY_POSTS_PER_PAGE:每一页显示多少文章,默认20
    * FLASKY_FOLLOWERS_PER_PAGE:每一页显示多少跟随着,默认20
    * FLASKY_COMMENTS_PER_PAGE:每一页显示多少评论,默认20
    * SESSION_STORAGE_HOST:session存储的host,默认localhost
    * CELERY_BROKER_NAME:celery异步处理时存储的host,默认localhost
    * SITE_DOMAIN:网站域名,默认localhost
    * DATABASE_URL:数据库连接url,默认'mysql://root:123456@localhost:3306/flask?charset=utf8'
    * FLASK_CONFIG:配置环境,默认default(开发环境)

### 数据表E-R关系图及数据库的创建

#### E-R图
![](https://github.com/longofo/flask-demo/blob/master/flasky/app/static/%E6%95%B0%E6%8D%AE%E5%BA%93%E8%AE%BE%E8%AE%A1.png)

### 数据库的创建

* python manager.py db init  (创建迁移仓库)
* python manager.py db migrate -m "initial migration"  (自动创建迁移脚本)
* python manager.py db upgrade  (将更新应用到数据库)
* python manager.py deploy
注：如果运行上诉四个命令出错，先删掉migrations文件夹

### 运行项目

#### Step1

* 项目根目录下执行 celery -A manager.celery worker --loglevel=info
* python manager.py runserver 启动项目

### 部署

#### 以nginx + gunicorn + flask为例

#### 使用openssl生成自签名证书

自己选择路径,使用以下命令生成证书:
```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

#### gunicorn配置

项目根目录下运行以下脚本:
```bash
pkill -f gunicorn
gunicorn --worker-class gevent --timeout 30 --graceful-timeout 20 --max-requests-jitter 2000 --max-requests 1500 -w 6 --log-level DEBUG --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log -D --bind 127.0.0.1:5000 manager:app
echo "gunicorn start!!!"
```

#### nginx上的配置

使用的是openresty

nginx.conf:
```nginx
#user  nobody;
worker_processes  1;

#error_log  logs/error.log;
#error_log  logs/error.log  notice;
error_log  logs/error.log  info;

pid        logs/nginx.pid;


events {
    worker_connections  1024;
}


http {
    include       mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

    access_log  logs/access.log  main;

    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    server_tokens   off;
    #keepalive_timeout  0;
    keepalive_timeout  65;
    fastcgi_intercept_errors on;

    gzip  on;

    server {
        listen     443 ssl;
        server_name  _;

        #charset koi8-r;

        #access_log  logs/host.access.log  main;
        ssl on;
        ssl_certificate /your-path/self-csrt/120.77.202.221.crt;
        ssl_certificate_key /your-path/self-csrt/120.77.202.221.key;

        include agent_deny.conf;

        location / {
            set $business "USER";
            access_by_lua_file /usr/local/openresty/nginx/conf/lua/access.lua;
            proxy_pass      http://127.0.0.1:5000;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            root   html;
            index  index.html index.htm;
        }

        error_page  404              /404.html;

        # redirect server error pages to the static page /50x.html
        #
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }
    }

    server {
        listen 80;
        server_name _;
        location / {
            return 301 https://$host$request_uri;
        }
    }
}
```
注：证书路径需要填写自己的路径

agent_deny.conf:
```nginx
#禁止Scrapy等工具的抓取
if ($http_user_agent ~* (Scrapy|Curl|HttpClient)) {
     return 403 '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
                 <head>
                    <title>403 forbinden!</title>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                 <body>
                    <h1><strong></strong></h1>
                    <div class="content" style="text-align: center">
                        <h3>403 FORBINDEN!!!</h3>
                    </div>
                 </body>
                 </html>
                ';
}

#禁止指定UA及UA为空的访问
if ($http_user_agent ~* "WinHttp|WebZIP|FetchURL|node-superagent|java/|FeedDemon|Jullo|JikeSpider|Indy Library|Alexa Toolbar|AskTbFXTV|AhrefsBot|CrawlDaddy|Java|Feedly|Apache-HttpAsyncClient|UniversalFeedParser|ApacheBench|Microsoft URL Control|Swiftbot|ZmEu|oBot|jaunty|Python-urllib|lightDeckReports Bot|YYSpider|DigExt|HttpClient|MJ12bot|heritrix|EasouSpider|Ezooms|BOT/0.1|YandexBot|FlightDeckReports|Linguee Bot|python-requests|^$" ) {
     return  403 '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
                  <head>
                    <title>403 forbinden!</title>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                  </head>
                  <body>
                    <h1><strong></strong></h1>
                    <div class="content" style="text-align: center">
                        <h3>403 FORBINDEN!!!</h3>
                    </div>
                  </body>
                  </html>
                 ';
}

#禁止非GET|HEAD|POST方式的抓取
if ($request_method !~ ^(GET|HEAD|POST)$) {
     return 403 '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
                 <head>
                    <title>403 forbinden!</title>
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                 </head>
                 <body>
                    <h1><strong></strong></h1>
                    <div class="content" style="text-align: center">
                        <h3>403 FORBINDEN!!!</h3>
                    </div>
                 </body>
                 </html>
                ';
}

```

lua脚本配置
```lua
local time_out=30    --指定访问频率时间段（秒）
local max_count=50 --指定访问频率计数最大值（秒）
local BUSINESS = ngx.var.business

local redis = require "resty.redis"
local conn = redis:new()
ok, err = conn:connect("127.0.0.1", 6379)
conn:set_timeout(2000) --超时时间2秒


if not ok then
    goto FLAG
end

if ngx.var.remote_addr == nil and ngx.var.cookie_session == nil  then
    goto FLAG
end

if ngx.var.remote_addr ~= nil then
    ip_is_block, err = conn:get(BUSINESS.."-BLOCK-"..ngx.var.remote_addr)
else
    ip_is_block = '0'
end

if ngx.var.cookie_session ~= nil then
    session_is_block, err = conn:get(BUSINESS.."-BLOCK-"..ngx.var.cookie_session)
else
    session_is_block = '0'
end

if ip_is_block == '1' or session_is_block == '1' then
    goto FLAG
end

if ngx.var.remote_addr ~= nil then
    ip_count, err = conn:get(BUSINESS.."-COUNT-"..ngx.var.remote_addr)

    if ip_count == ngx.null then
        res, err = conn:set(BUSINESS.."-COUNT-"..ngx.var.remote_addr, 1)
        res, err = conn:expire(BUSINESS.."-COUNT-"..ngx.var.remote_addr, time_out)
    else
        ip_count = ip_count + 1
        if ip_count >= max_count then
            res, err = conn:set(BUSINESS.."-BLOCK-"..ngx.var.remote_addr, 1)
        else
            res, err = conn:set(BUSINESS.."-COUNT-"..ngx.var.remote_addr,ip_count)
            res, err = conn:expire(BUSINESS.."-COUNT-"..ngx.var.remote_addr, time_out)
        end
    end
end


if ngx.var.cookie_session ~= nil then
    session_count, err = conn:get(BUSINESS.."-COUNT-"..ngx.var.cookie_session)

    if session_count == ngx.null then
        res, err = conn:set(BUSINESS.."-COUNT-"..ngx.var.cookie_session, 1)
        res, err = conn:expire(BUSINESS.."-COUNT-"..ngx.var.cookie_session, time_out)
    else
        session_count = session_count + 1

        if session_count >= max_count then
            res, err = conn:set(BUSINESS.."-BLOCK-"..ngx.var.cookie_session, 1)
        else
            res, err = conn:set(BUSINESS.."-COUNT-"..ngx.var.cookie_session,session_count)
            res, err = conn:expire(BUSINESS.."-COUNT-"..ngx.var.cookie_session, time_out)
        end
    end
end


::FLAG::
local ok, err = conn:close()

```
nginx及几条命令:
* /your-path/openresty/nginx/sbin/nginx -t (检测配置是否正确)
* /your-path/openresty/nginx/sbin/nginx -s reload (平滑启动)

## demo地址

[https://120.77.202.221](https://120.77.202.221)

浏览器会提示不安全，因为这是自签名证书，没有第三方认证机构的信任，浏览器也不会信任
