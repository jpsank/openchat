from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required

from app.blueprints.main import bp
from app import db, images
from app.models import Post, Image, Chat, Comment
from app.blueprints.main.forms import NewPostForm, NewCommentForm

from . import paginate


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

