from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.forms import LoginForm
from werkzeug.security import check_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    """Redirect to appropriate page based on authentication status"""
    if current_user.is_authenticated:
        if current_user.role == 'team_leader':
            return redirect(url_for('team_leader.data_entry'))
        else:
            return redirect(url_for('data_analyst.campaign_filter'))
    else:
        return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password) or user.role != role:
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        
        if user.role == 'team_leader':
            return redirect(url_for('team_leader.data_entry'))
        else:
            return redirect(url_for('data_analyst.campaign_filter'))
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))