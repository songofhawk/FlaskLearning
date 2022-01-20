from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from flask_login import LoginManager
from flask_openid import OpenID
import os
from config import basedir, MAIL_USERNAME, MAIL_PASSWORD, MAIL_SERVER, MAIL_PORT, ADMINS

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

current_user = None
from app import views, models

if not app.debug:
    import logging
    from logging.handlers import SMTPHandler

    credentials = None
    if MAIL_USERNAME or MAIL_PASSWORD:
        credentials = (MAIL_USERNAME, MAIL_PASSWORD)
    mail_handler = SMTPHandler((MAIL_SERVER, MAIL_PORT), 'no-reply@' + MAIL_SERVER, ADMINS, 'microblog failure',
                               credentials)
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)

if not app.debug:
    import logging
    from logging.handlers import RotatingFileHandler
    '''os.path.join的时候，tmp前面不能有/，要不会被认为是从根目录开始的绝对路径，从而抛弃前面所有的参数'''
    file_handler = RotatingFileHandler(os.path.join(config.basedir, 'tmp/microblog.log'), 'a', 1 * 1024 * 1024, 10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('microblog startup')
