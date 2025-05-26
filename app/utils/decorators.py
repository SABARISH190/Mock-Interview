from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    """
    Decorator for routes that require admin privileges.
    If the current user is not an admin, they will be redirected with an error message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: admin_required - User {current_user.id} is_admin={current_user.is_admin}")
        if not current_user.is_authenticated:
            print("DEBUG: User not authenticated")
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            print("DEBUG: User is not an admin")
            abort(403)  # Forbidden
        print("DEBUG: User is admin, allowing access")
        return f(*args, **kwargs)
    return decorated_function
