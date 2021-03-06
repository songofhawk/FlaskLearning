from flask import render_template, flash, redirect, url_for, session, request, g
from flask_login import login_user, logout_user, current_user, login_required
from app import app, lm, oid, db
from config import POSTS_PER_PAGE
from .forms import LoginForm, EditForm, PostForm
from .models import User, Post
from datetime import datetime


@app.before_request
def before_request():
    # g.user = app.current_user
    print('before_request')
    if hasattr(app, 'current_user'):
        app.current_user.last_seen = datetime.utcnow()
        # app.current_user.update()
        # print('update')
        # User.update(app.current_user)
        # db.session.flush()
        # print('flush')
        '''
        session.add的含义，是把这个数据对象交给db session来管理
        每一个请求，都有自己的db session，这是由Flash-Sqlalchemy插件来维护的
        '''
        db.session.add(app.current_user)
        db.session.commit()


@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@app.route('/index/<int:page>', methods = ['GET', 'POST'])
# @login_required
def index(page=1):
    # user = g.user
    user = app.current_user if hasattr(app, 'current_user') else None
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    posts = user.followed_posts().paginate(page, POSTS_PER_PAGE, False) if user is not None else None

    return render_template('index.html',
                           title='Home',
                           form=form,
                           posts=posts,
                           user=user)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    # if g.user is not None and g.user.is_authenticated:
    #     return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        user_fill_id = form.openid.data
        user = User.query.filter_by(email=user_fill_id).first()
        if user:
            app.current_user = user
            return redirect(url_for('index'))
        else:
            flash('Invalid login. Please try again.')
            return redirect(url_for('login'))
        # return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=app.config['OPENID_PROVIDERS'],
                           app=app)


@app.route('/logout')
def logout():
    app.current_user = None
    return redirect(url_for('index'))


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email=resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname=nickname, email=resp.email)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/user/<nickname>')
def user(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        flash('User ' + nickname + ' not found.')
        return redirect(url_for('index'))
    posts = user.posts.all()

    return render_template('user.html',
                           user=user,
                           posts=posts,
                           app=app)


@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = EditForm(app.current_user)
    if not hasattr(app, 'current_user'):
        return redirect(url_for('index'))
    user = app.current_user
    if form.validate_on_submit():
        user.nickname = form.nickname.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = user.nickname
        form.about_me.data = user.about_me
    return render_template('edit.html', form=form)


@app.errorhandler(404)
def internal_error(error):
    print('404 handler')
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    print('500 handler')
    '''如果项目启动时，配置了FlaskDebug=True参数，那么这个handler不会执行'''
    db.session.rollback()
    return render_template('500.html'), 500
