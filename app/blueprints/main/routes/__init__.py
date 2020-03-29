from datetime import datetime
from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required
import sqlalchemy as sa
from sqlalchemy import func

from app.blueprints.main import bp
from app import db
from app.models import User, Post, Vote, Image, Chat, Sub, Comment
from app.blueprints.main.forms import SearchForm


def paginate(items, per_page=None):
    if per_page is None:
        per_page = current_app.config['DEFAULT_PER_PAGE']

    page = request.args.get('page', 1, type=int)
    items = items.paginate(page, per_page, False)

    next_url = url_for(request.endpoint, page=items.next_num) if items.has_next else None
    prev_url = url_for(request.endpoint, page=items.prev_num) if items.has_prev else None
    return items, next_url, prev_url


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# ------------------------------ FRONT PAGES ------------------------------

@bp.route('/')
@bp.route('/index')
def index():
    return render_template('main/home.html', title='Home')


@bp.route('/feed')
@login_required
def feed():
    posts = current_user.subscribed_posts().order_by(Post.created_at.desc())

    posts, next_url, prev_url = paginate(posts, current_app.config['POSTS_PER_PAGE'])

    return render_template('main/feed.html', title='Your Feed', posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/popular', methods=['GET', 'POST'])
def popular():
    search_form = SearchForm()
    posts = db.session.query(Post)

    if search_form.validate_on_submit():
        posts = posts.filter(Post.title.like('%' + search_form.search.data + '%') |
                             Post.body.like('%' + search_form.search.data + '%'))

    posts = posts.order_by(sa.desc(Post.score))
    posts, next_url, prev_url = paginate(posts, current_app.config['POSTS_PER_PAGE'])

    return render_template('main/popular.html', title='Popular',
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           form=search_form, include_chat=True)


@bp.route('/explore_chats', methods=['GET', 'POST'])
def explore_chats():
    form = SearchForm()
    chats = db.session.query(Chat)

    if form.validate_on_submit():
        chats = chats.filter(Chat.name.like('%' + form.search.data + '%') |
                             Chat.about.like('%' + form.search.data + '%'))

    chats = chats.outerjoin(Sub).group_by(Chat.id).order_by(func.count().desc())
    chats, next_url, prev_url = paginate(chats, current_app.config['CHATS_PER_PAGE'])

    return render_template('main/explore_chats.html', title='Explore',
                           chats=chats.items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/leaderboard', methods=['GET', 'POST'])
def leaderboard():
    search_form = SearchForm()
    users = db.session.query(User)

    if search_form.validate_on_submit():
        users = users.filter(User.username.like('%' + search_form.search.data + '%'))

    users = users.order_by(sa.desc(User.score))
    users, next_url, prev_url = paginate(users, current_app.config['USERS_PER_PAGE'])

    return render_template('main/leaderboard.html', title='Leaderboard',
                           users=users.items, next_url=next_url, prev_url=prev_url,
                           form=search_form)


# ------------------------------ FUNCTIONAL PAGES ------------------------------

from .users import *
from .chats import *
from .posts import *
from .votes import *
