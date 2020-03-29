from flask import render_template, flash, redirect, request, url_for, current_app, abort
from flask_login import current_user, login_required

from app.blueprints.main import bp
from app import db
from app.models import Post, Comment


# ------------------------------ VOTES ------------------------------

def vote_post(post_id, liked):
    """ Vote on a post """
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return None
    vote = current_user.vote(post, liked)
    db.session.merge(vote)
    db.session.commit()
    return post


def vote_comment(comment_id, liked):
    """ Vote on a comment """
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is None:
        return None
    vote = current_user.vote(comment, liked)
    db.session.merge(vote)
    db.session.commit()
    return comment


@bp.route('/upvote/<post_id>')
@login_required
def upvote(post_id):
    """ Page to upvote a post """
    found = vote_post(post_id, True)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You upvoted the post!')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/downvote/<post_id>')
@login_required
def downvote(post_id):
    """ Page to downvote a post """
    found = vote_post(post_id, False)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You downvoted the post!')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/upvote_comment/<comment_id>')
@login_required
def upvote_comment(comment_id):
    """ Page to upvote a comment """
    found = vote_comment(comment_id, True)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You voted on the comment!')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))


@bp.route('/downvote_comment/<comment_id>')
@login_required
def downvote_comment(comment_id):
    """ Page to downvote a comment """
    found = vote_comment(comment_id, False)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You voted on the comment!')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))


# ------------------------------ WITHDRAW VOTES ------------------------------

def withdraw_vote_post(post_id):
    """ Withdraw vote from a post """
    post = Post.query.filter_by(id=post_id).first()
    if post is None:
        return None
    current_user.withdraw_vote(post)
    db.session.commit()
    return post


def withdraw_vote_comm(comment_id):
    """ Withdraw vote from a comment """
    comment = Comment.query.filter_by(id=comment_id).first()
    if comment is None:
        return None
    current_user.withdraw_vote(comment)
    db.session.commit()
    return comment


@bp.route('/withdraw_vote/<post_id>')
@login_required
def withdraw_vote(post_id):
    """ Page to withdraw your vote from a post """
    found = withdraw_vote_post(post_id)
    if found is None:
        flash('Post not found.')
        return redirect(url_for('main.index'))
    flash('You withdrew your vote.')
    return redirect(request.referrer or url_for('main.show_post', post_id=post_id))


@bp.route('/withdraw_vote_comment/<comment_id>')
@login_required
def withdraw_vote_comment(comment_id):
    """ Page to withdraw your vote from a comment """
    found = withdraw_vote_comm(comment_id)
    if found is None:
        flash('Comment not found.')
        return redirect(url_for('main.index'))
    flash('You withdrew your vote.')
    return redirect(request.referrer or url_for('main.show_post', post_id=found.post_id, comment_id=comment_id))

