from flask import session, redirect, url_for, flash, render_template, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from . import auth, oauth        
from .. import db
from ..models import User, Role, Comment, Post
from .forms import RegistrationForm, ChangePasswordForm, ChangeEmailForm, LoginForm, PasswordResetRequestForm
from app.email import send_welcome_email
from ..email import send_email
from datetime import datetime, timezone
import os

google = None  # will be set in configure_oauth

def configure_oauth(app):
    global google
    oauth.init_app(app)
    google = oauth.register(
        name='google',
        client_id=os.getenv('FLASK_GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('FLASK_GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))
        if getattr(user, 'password', None) is None:
            flash('This account uses Google login. Try "Sign in with Google" instead.')
            return redirect(url_for('auth.login'))
        if not user.verify_password(form.password.data):
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.index'))
    return render_template('auth/login.html', form=form)

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            flash('Email is not registered.')
            return redirect(url_for('auth.reset_password_request'))

        # Generate token and send reset email
        token = user.generate_reset_token()
        reset_url = url_for('auth.reset_password', token=token, _external=True)

        reset_template = (
            "Hi {username},\n\n"
            "You requested a password reset for your Advancing AI account.\n\n"
            "Please click the link below to set a new password:\n\n"
            "{reset_url}\n\n"
            "If you did not request this, you can safely ignore this email.\n\n"
            "- Advancing AI Team"
        )

        send_email(
            user.email,
            'Reset Your Password',
            reset_template,
            username=user.username,
            reset_url=reset_url
        )
        flash('An email with instructions to reset your password has been sent.')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

@auth.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.reset_password(token, form.password.data)
        if user:
            db.session.commit()
            flash('Your password has been updated. You can now log in.')
            return redirect(url_for('auth.login'))
        else:
            flash('The password reset link is invalid or has expired.')
            return redirect(url_for('auth.reset_password_request'))

    return render_template('auth/reset_password_token.html', form=form)

@auth.route('/login/google')
def login_google():
    redirect_uri = url_for('auth.auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route('/auth/google/callback')
def auth_google_callback():
    try:
        token = google.authorize_access_token()
        userinfo_endpoint = google.server_metadata['userinfo_endpoint']
        resp = google.get(userinfo_endpoint)
        user_info = resp.json()

        email = user_info.get('email')
        name = user_info.get('name')
        sub = user_info.get('id') or user_info.get('sub')

        user = User.query.filter_by(email=email).first()

        is_new_user = False
        if user is None:
            user = User(
                email=email,
                username=name,
                google_id=sub,
                create_at=datetime.now(timezone.utc),
                role_id="3"
            )
            db.session.add(user)
            db.session.commit()
            is_new_user = True

        login_user(user, remember=False)
        session['user_email'] = user.email
        session['user_name'] = user.username

        if is_new_user:
            send_welcome_email(user)

        flash(f'Logged in as {user.username}', 'success')
        return redirect(url_for('main.index'))
    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'danger')
        return redirect(url_for('auth.login_google'))

@auth.route('/logout')
def logout():
    logout_user()
    session.pop('google_oauth_token', None)
    session.clear()
    response = redirect(url_for('main.index'))
    response.delete_cookie('remember_token')
    flash('You have been logged out.', 'info')
    return response
    
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now login.')
        token = user.generate_confirmation_token()
        confirm_url = url_for('auth.confirm', token=token, _external=True)

        confirm_template = (
            "Hi {username},\n\n"
            "Welcome to Advancing AI! Please confirm your account by clicking the link below:\n\n"
            "{confirm_url}\n\n"
            "If you did not sign up, you can ignore this email.\n\n"
            "- Advancing AI Team"
        )

        send_email(
            user.email,
            'Confirm Your Account',
            confirm_template,
            username=user.username,
            confirm_url=confirm_url
        )
        
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    confirm_url = url_for('auth.confirm', token=token, _external=True)

    confirm_template = (
        "Hi {username},\n\n"
        "Here is a new confirmation link for your Advancing AI account:\n\n"
        "{confirm_url}\n\n"
        "If you did not request this, you can ignore this email.\n\n"
        "- Advancing AI Team"
    )

    send_email(
        current_user.email,
        'Confirm Your Account',
        confirm_template,
        username=current_user.username,
        confirm_url=confirm_url
    )
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()

            notify_template = (
                "Hi {username},\n\n"
                "This is a confirmation that your Advancing AI password was just changed.\n\n"
                "If you did not make this change, please reset your password immediately "
                "or contact support.\n\n"
                "- Advancing AI Team"
            )
            send_email(
                current_user.email,
                'Your password was changed',
                notify_template,
                username=current_user.username
            )

            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password.')
    return render_template("auth/change_password.html", form=form)

@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            change_url = url_for('auth.change_email', token=token, _external=True)

            change_email_template = (
                "Hi {username},\n\n"
                "You requested to change your Advancing AI account email to {new_email}.\n\n"
                "Please confirm this change by clicking the link below:\n\n"
                "{change_url}\n\n"
                "If you did not request this change, please ignore this email.\n\n"
                "- Advancing AI Team"
            )

            send_email(
                new_email,
                'Confirm your email address',
                change_email_template,
                username=current_user.username,
                new_email=new_email,
                change_url=change_url
            )
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)