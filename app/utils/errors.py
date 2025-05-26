from flask import Blueprint, render_template

errors = Blueprint('errors', __name__)

@errors.app_errorhandler(404)
def error_404(error):
    """Handler for 404 Not Found error."""
    return render_template('errors/404.html'), 404

@errors.app_errorhandler(403)
def error_403(error):
    """Handler for 403 Forbidden error."""
    return render_template('errors/403.html'), 403

@errors.app_errorhandler(500)
def error_500(error):
    """Handler for 500 Internal Server Error."""
    return render_template('errors/500.html'), 500
