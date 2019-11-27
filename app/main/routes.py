from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app
from flask_login import current_user, login_required
from app import db
from sqlalchemy import func
from app.main.forms import EditProfileForm, PostForm, ChatForm, CommentForm, EditChatForm, SearchForm
from app.models import User, Post, Image, Chat, Comment, followers, Like
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
        return redirect(url_for('main.show_chat', name=new_chat.name))

    page = request.args.get('page', 1, type=int)
    # chats = Chat.query.paginate(page, current_app.config['CHATS_PER_PAGE'], False)
    # chat_items = sorted(chats.items, key=lambda ch: ch.followed_by.count(), reverse=True)
    chats = db.session.query(Chat).join(followers).group_by(Chat.id).order_by(func.count().desc())
    chats = chats.paginate(page, current_app.config['CHATS_PER_PAGE'], False)

    next_url = url_for('main.index', page=chats.next_num) if chats.has_next else None
    prev_url = url_for('main.index', page=chats.prev_num) if chats.has_prev else None
    return render_template('explore.html', title='Explore',
                           chats=chats.items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/popular', methods=['GET', 'POST'])
@login_required
def popular():
    searchForm = SearchForm()
    posts = db.session.query(Post)

    if searchForm.validate_on_submit():
        posts = posts.filter(Post.title.like('%' + searchForm.search.data + '%') |
                             Post.body.like('%' + searchForm.search.data + '%'))

    posts = posts.join(Like).group_by(Post.id).order_by(func.count().desc())
    page = request.args.get('page', 1, type=int)
    posts = posts.paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None
    return render_template('popular.html', title='Popular',
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           form=searchForm)


@bp.route('/chat/<name>', methods=['GET', 'POST'])
@login_required
def show_chat(name):
    chat = Chat.query.filter_by(name=name).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(chat=chat).order_by(Post.created_at.desc())\
        .paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.show_chat', name=name, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.show_chat', name=name, page=posts.prev_num) if posts.has_prev else None
    return render_template('chat.html', title=chat.name, chat=chat,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/make_post', methods=['GET', 'POST'], defaults={'chat_name': None})
@bp.route('/make_post/<chat_name>', methods=['GET', 'POST'])
@login_required
def make_post(chat_name):
    form = PostForm(chat_name=chat_name)
    if form.validate_on_submit():
        chat_name = form.chat_name.data

        new_post = Post(title=form.title.data, body=form.body.data, author=current_user)
        new_post.chat = Chat.query.filter_by(name=chat_name).first()

        if 'image' in request.files and request.files['image']:
            filename = images.save(form.image.data)
            url = images.url(filename)
            image = Image(filename=filename, url=url)
            new_post.attachment = image

        db.session.add(new_post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('main.show_chat', name=chat_name))
    return render_template('make_post.html', title="New Post", form=form)


@bp.route('/post/<id>', methods=['GET', 'POST'])
@login_required
def show_post(id):
    post = Post.query.filter_by(id=id).first_or_404()

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, author=current_user)
        comment.post = post
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('main.show_post', id=id))

    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at.desc())\
        .paginate(page, current_app.config['COMMENTS_PER_PAGE'], False)
    next_url = url_for('main.show_post', id=id, page=comments.next_num) if comments.has_next else None
    prev_url = url_for('main.show_chat', id=id, page=comments.prev_num) if comments.has_prev else None
    return render_template('post.html', title=post.title, post=post,
                           comments=comments.items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/user/<username>')
def show_user(username):
    user = User.query.filter_by(username=username).first_or_404()

    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(author=user).order_by(Post.created_at.desc()) \
        .paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.show_user', username=username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.show_user', username=username, page=posts.prev_num) if posts.has_prev else None

    return render_template('user.html', user=user,
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
        return redirect(url_for('main.show_user', username=current_user.username))
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
    flash('You followed chat/{}!'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))


@bp.route('/unfollow/<name>')
@login_required
def unfollow(name):
    the_chat = Chat.query.filter_by(name=name).first()
    if the_chat is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    current_user.unfollow(the_chat)
    db.session.commit()
    flash('You stopped following chat/{}.'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))


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
    return redirect(request.referrer or url_for('main.show_post', id=post_id))


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
    return redirect(request.referrer or url_for('main.show_post', id=post_id))


# Editing chats

@bp.route('/edit_chat/<name>', methods=['GET', 'POST'])
@login_required
def edit_chat(name):
    chat = current_user.chats.filter_by(name=name).first_or_404()
    form = EditChatForm()
    if form.validate_on_submit():
        chat.about = form.about.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.show_chat', name=chat.name))
    elif request.method == 'GET':
        form.about.data = chat.about
    return render_template('edit_chat.html', title='Edit chat/{}'.format(chat.name), chat=chat,
                           form=form)
