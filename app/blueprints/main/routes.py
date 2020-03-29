from datetime import datetime
from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required
import sqlalchemy as sa
from sqlalchemy import func

from app.blueprints.main import bp
from app import db, images
from app.models import User, Post, Vote, Image, Chat, Sub, Comment
from app.blueprints.main.forms import EditProfileForm, NewPostForm, NewCommentForm, NewChatForm, EditChatForm, SearchForm


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


# ------------------------------ FUNCTIONAL ENDPOINTS ------------------------------

class Control:

    @staticmethod
    def set_subscribed(name, sub):
        chat = Chat.get_by_name(name)
        if chat is None:
            return None
        current_user.set_subscribed(chat, sub)
        db.session.commit()
        return chat

    @staticmethod
    def vote_post(post_id, liked):
        post = Post.query.filter_by(id=post_id).first()
        if post is None:
            return None
        vote = current_user.vote(post, liked)
        db.session.merge(vote)
        db.session.commit()
        return post

    @staticmethod
    def vote_comment(comment_id, liked):
        comment = Comment.query.filter_by(id=comment_id).first()
        if comment is None:
            return None
        vote = current_user.vote(comment, liked)
        db.session.merge(vote)
        db.session.commit()
        return comment

    @staticmethod
    def withdraw_vote_post(post_id):
        post = Post.query.filter_by(id=post_id).first()
        if post is None:
            return None
        current_user.withdraw_vote(post)
        db.session.commit()
        return post

    @staticmethod
    def withdraw_vote_comment(comment_id):
        comment = Comment.query.filter_by(id=comment_id).first()
        if comment is None:
            return None
        current_user.withdraw_vote(comment)
        db.session.commit()
        return comment


# ------------------------------ USERS ------------------------------

@bp.route('/user/<username>')
def show_user(username):
    user = User.get_by_username(username)
    if user is None:
        return abort(404)

    posts = Post.query.filter_by(author=user).order_by(Post.created_at.desc())
    posts, next_url, prev_url = paginate(posts, current_app.config['POSTS_PER_PAGE'])

    return render_template('main/user.html', user=user,
                           posts=posts.items, next_url=next_url, prev_url=prev_url,
                           include_chat=True)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.show_user', username=current_user.username))
    elif request.method == 'GET':
        form.about_me.data = current_user.about_me
    return render_template('main/edit_profile.html', title='Edit Profile',
                           form=form)


# ------------------------------ CHATS ------------------------------

@bp.route('/chat/<name>', methods=['GET', 'POST'])
def show_chat(name):
    chat = Chat.get_by_name(name)
    if chat is None:
        return abort(404)

    posts = Post.query.filter_by(chat=chat).order_by(Post.created_at.desc())
    posts, next_url, prev_url = paginate(posts, current_app.config['POSTS_PER_PAGE'])

    return render_template('main/chat.html', title=chat.name, chat=chat,
                           posts=posts.items, next_url=next_url, prev_url=prev_url)


@bp.route('/create_chat', methods=['GET', 'POST'])
@login_required
def create_chat():
    form = NewChatForm()

    if form.validate_on_submit():
        new_chat = Chat(name=form.name.data, about=form.about.data, creator=current_user)
        current_user.subscribe(new_chat)
        db.session.add(new_chat)
        db.session.commit()
        flash('Your new chat is now live!')
        return redirect(url_for('main.show_chat', name=new_chat.name))

    return render_template('main/create_chat.html', title="New Chat", form=form)


@bp.route('/edit_chat/<name>', methods=['GET', 'POST'])
@login_required
def edit_chat(name):
    chat = Chat.get_by_name(name)
    if chat is None:
        return abort(404)
    if chat not in current_user.chats:
        flash('You cannot edit this chat.')
        return redirect(url_for('show_chat', name=name))
    form = EditChatForm()
    if form.validate_on_submit():
        chat.about = form.about.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.show_chat', name=chat.name))
    elif request.method == 'GET':
        form.about.data = chat.about
    return render_template('main/edit_chat.html', title='Edit chat/{}'.format(chat.name), chat=chat,
                           form=form)


@bp.route('/subscribe/<name>')
@login_required
def subscribe(name):
    found = Control.set_subscribed(name, True)
    if found is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    flash('You subscribed to chat/{}!'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))


@bp.route('/unsubscribe/<name>')
@login_required
def unsubscribe(name):
    found = Control.set_subscribed(name, False)
    if found is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    flash('You unsubscribed from chat/{}!'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))


# ------------------------------ POSTS ------------------------------

@bp.route('/post/<post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()

    form = NewCommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author=None if current_user.is_anonymous else current_user)
        comment.post = post
        db.session.add(comment)
        db.session.commit()
        flash('Your comment is now live!')
        return redirect(url_for('main.show_post', post_id=post_id))

    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc())
    comments, next_url, prev_url = paginate(comments, current_app.config['COMMENTS_PER_PAGE'])

    return render_template('main/post.html', title=post.title, post=post,
                           comments=comments.items, next_url=next_url, prev_url=prev_url,
                           form=form)


@bp.route('/make_post', methods=['GET', 'POST'], defaults={'chat_name': None})
@bp.route('/make_post/<chat_name>', methods=['GET', 'POST'])
@login_required
def make_post(chat_name):
    form = NewPostForm(chat_name=chat_name)
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
        flash('Your new post is now live!')
        return redirect(url_for('main.show_chat', name=chat_name))
    return render_template('main/make_post.html', title="New Post", form=form)


@bp.route('/delete_post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        flash('The post you are trying to delete does not exist.')
        return redirect(request.referrer or url_for('main.index'))
    chat_name = post.chat.name

    db.session.delete(post)
    db.session.commit()
    flash('You deleted the post.')
    return redirect(request.referrer or url_for('main.show_chat', name=chat_name))


# ------------------------------ VOTES ------------------------------


@bp.route('/upvote/<post_id>')
@login_required
def upvote(post_id):
    found = Control.vote_post(post_id, True)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You upvoted the post!')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/downvote/<post_id>')
@login_required
def downvote(post_id):
    found = Control.vote_post(post_id, False)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You downvoted the post!')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/withdraw_vote/<post_id>')
@login_required
def withdraw_vote(post_id):
    found = Control.withdraw_vote_post(post_id)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You withdrew your vote.')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/upvote_comment/<comment_id>')
@login_required
def upvote_comment(comment_id):
    found = Control.vote_comment(comment_id, True)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You voted on the comment!')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))


@bp.route('/downvote_comment/<comment_id>')
@login_required
def downvote_comment(comment_id):
    found = Control.vote_comment(comment_id, False)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You voted on the comment!')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))


@bp.route('/withdraw_vote_comment/<comment_id>')
@login_required
def withdraw_vote_comment(comment_id):
    found = Control.withdraw_vote_comment(comment_id)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You withdrew your vote.')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))

