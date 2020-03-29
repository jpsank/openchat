from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required

from app.blueprints.main import bp
from app import db
from app.models import Post, Chat
from app.blueprints.main.forms import NewChatForm, EditChatForm

from . import paginate


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


# ------------------------------ SUBSCRIBING ------------------------------

def set_subscribed(name, sub):
    chat = Chat.get_by_name(name)
    if chat is None:
        return None
    current_user.set_subscribed(chat, sub)
    db.session.commit()
    return chat


@bp.route('/subscribe/<name>')
@login_required
def subscribe(name):
    found = set_subscribed(name, True)
    if found is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    flash('You subscribed to chat/{}!'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))


@bp.route('/unsubscribe/<name>')
@login_required
def unsubscribe(name):
    found = set_subscribed(name, False)
    if found is None:
        flash('Chat {} not found.'.format(name))
        return redirect(url_for('main.index'))
    flash('You unsubscribed from chat/{}!'.format(name))
    return redirect(request.referrer or url_for('main.show_chat', name=name))
