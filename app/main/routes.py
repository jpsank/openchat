from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from sqlalchemy import func
from app.main.forms import EditProfileForm, PostForm, ChatForm, CommentForm
from app.models import User, Post, Image, Chat, Comment, followers
from app.main import bp
from app import Config, images
import os


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('index.html', title='Home',
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           include_chat=True)


@bp.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form = ChatForm()
    if form.validate_on_submit():
        name = form.name.data.replace(" ", "_")
        new_chat = Chat(name=name, about=form.about.data, creator=current_user)
        current_user.follow(new_chat)
        db.session.add(new_chat)
        db.session.commit()
        flash('Your chat is now live!')
        return redirect(url_for('main.chat', name=new_chat.name))

    page = request.args.get('page', 1, type=int)
    chats = Chat.query.paginate(page, current_app.config['CHATS_PER_PAGE'], False)
    chat_items = sorted(chats.items, key=lambda ch: ch.followed_by.count(), reverse=True)
    next_url = url_for('main.index', page=chats.next_num) if chats.has_next else None
    prev_url = url_for('main.index', page=chats.prev_num) if chats.has_prev else None
    return render_template('explore.html', title='Explore',
                           chats=chat_items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/chat/<name>', methods=['GET', 'POST'])
@login_required
def chat(name):
    the_chat = Chat.query.filter_by(name=name).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(chat=the_chat).order_by(Post.created_at.desc())\
        .paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.chat', name=name, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.chat', name=name, page=posts.prev_num) if posts.has_prev else None
    return render_template('chat.html', title=the_chat.name, chat=the_chat,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/make_post/<chat_name>', methods=['GET', 'POST'])
def make_post(chat_name):
    form = PostForm(chat_name=chat_name)
    if form.validate_on_submit():
        new_post = Post(title=form.title.data, body=form.body.data, author=current_user)
        new_post.chat = Chat.query.filter_by(name=chat_name).first()

        if request.files['image']:
            filename = images.save(request.files['image'])
            url = images.url(filename)
            image = Image(filename=filename, url=url)
            new_post.attachment = image

        db.session.add(new_post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.chat', name=chat_name))
    return render_template('make_post.html', title="New Post", form=form)


@bp.route('/post/<id>', methods=['GET', 'POST'])
@login_required
def post(id):
    the_post = Post.query.filter_by(id=id).first_or_404()

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user)
        comment.post = the_post
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('main.post', id=id))

    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at.desc())\
        .paginate(page, current_app.config['COMMENTS_PER_PAGE'], False)
    next_url = url_for('main.post', id=id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.chat', id=id, page=comments.prev_num) if comments.has_prev else None
    return render_template('post.html', title=the_post.title, post=the_post,
                           comments=comments.items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/user/<username>')
def user(username):
    u = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=u).order_by(Post.created_at.desc()) \
        .paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.user', username=username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=username, page=posts.prev_num) if posts.has_prev else None

    return render_template('user.html', user=u,
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           include_chat=True)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@bp.route('/follow/<name>')
@login_required
def follow(name):
    the_chat = Chat.query.filter_by(name=name).first()
    if the_chat is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    current_user.follow(the_chat)
    db.session.commit()
    flash('You are following {}!'.format(name))
    return redirect(url_for('main.chat', name=name))


@bp.route('/unfollow/<name>')
@login_required
def unfollow(name):
    the_chat = Chat.query.filter_by(name=name).first()
    if the_chat is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    current_user.unfollow(the_chat)
    db.session.commit()
    flash('You are not following {}.'.format(name))
    return redirect(url_for('main.chat', name=name))


@bp.route('/like/<post_id>')
@login_required
def like(post_id):
    the_post = Post.query.filter_by(id=post_id).first()
    if the_post is None:
        flash('Post {} not found.'.format(post_id))
        return redirect(url_for('main.index'))
    current_user.like(the_post)
    db.session.commit()
    flash('You liked the post!')
    return redirect(request.referrer or url_for('main.post', id=post_id))


@bp.route('/unlike/<post_id>')
@login_required
def unlike(post_id):
    the_post = Post.query.filter_by(id=post_id).first()
    if the_post is None:
        flash('Post {} not found.'.format(post_id))
        return redirect(url_for('main.index'))
    current_user.unlike(the_post)
    db.session.commit()
    flash('You unliked the post!')
    return redirect(request.referrer or url_for('main.post', id=post_id))