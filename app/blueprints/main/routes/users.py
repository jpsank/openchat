from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required

from app.blueprints.main import bp
from app import db, images
from app.models import User, Post
from app.blueprints.main.forms import EditProfileForm

from . import paginate


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
