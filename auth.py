from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
import re

auth = Blueprint('auth', __name__)


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validation
        errors = []
        
        if not email or not is_valid_email(email):
            errors.append('Valid email is required')
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        
        if errors:
            if request.is_json:
                return jsonify({'error': ', '.join(errors)}), 400
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(email=email, username=username)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful'}), 200
        
        flash('Registration successful! Welcome!', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        # Redirect admin users to admin dashboard
        if getattr(current_user, 'is_admin', False):
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=data.get('remember', False))
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'username': user.username,
                    'is_admin': getattr(user, 'is_admin', False),
                    'redirect_url': '/admin' if getattr(user, 'is_admin', False) else '/',
                    'videos_processed': user.get_video_count(),
                    'can_process': user.can_process_video()
                }), 200
            
            flash(f'Welcome back, {user.username}!', 'success')
            # Redirect admin to admin dashboard
            if getattr(user, 'is_admin', False):
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        
        error_message = 'Invalid email or password'
        
        if request.is_json:
            return jsonify({'error': error_message}), 401
        
        flash(error_message, 'error')
    
    return render_template('login.html')


@auth.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/user/status')
@login_required
def user_status():
    """Get current user status"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'videos_processed': current_user.get_video_count(),
        'videos_remaining': 2 - current_user.get_video_count() if not current_user.is_premium else 'unlimited',
        'is_premium': current_user.is_premium,
        'can_process': current_user.can_process_video()
    })
