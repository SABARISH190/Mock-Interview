import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect, generate_csrf

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class='config.DevelopmentConfig'):
    """Application factory function to create and configure the Flask app."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure logging
    if not app.debug and not app.testing:
        # Ensure the log directory exists
        log_dir = os.path.join(app.root_path, '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Set log level
        log_level = logging.INFO
        
        # Configure root logger
        logging.basicConfig(level=log_level)
        
        # Create a file handler for logs with a larger maxBytes and delay=True
        log_file = os.path.join(log_dir, 'app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=5,
            encoding='utf-8',
            delay=True  # Delay file opening until first write
        )
        
        # Create formatter and add to handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # Clear any existing handlers and add our file handler
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        
        # Add the file handler to the root logger
        logging.root.addHandler(file_handler)
        
        # Also add to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        
        # Log application startup
        app.logger.info('Application startup')
        app.logger.info(f'Logging to: {os.path.abspath(log_file)}')
    else:
        # In debug mode, just log to console
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(logging.StreamHandler())
        app.logger.info('Application started in debug mode')
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Register custom template filters
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['datetimeformat'] = datetimeformat
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    
    # Add CSRF token to all templates
    @app.after_request
    def set_csrf_cookie(response):
        if response.status_code < 400:
            response.set_cookie('X-CSRFToken', generate_csrf())
        return response
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth as auth_blueprint
    from app.routes.main import main as main_blueprint
    from app.routes.interview import interview as interview_blueprint
    from app.routes.admin import admin as admin_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(interview_blueprint, url_prefix='/interview')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # Register admin_questions blueprint directly with the app
    from app.routes.admin_questions import admin_questions
    app.register_blueprint(admin_questions, url_prefix='/admin/questions')
    
    # Add CSRF token to all templates
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf()}
    
    # Error handlers
    from app.utils.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User}
    
    return app

# Import filters first to avoid circular imports
from app.filters import time_ago, datetimeformat

# Import models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.resume import Resume
from app.models.interview import Interview, Question, Response
from app.models.analysis import Analysis
from app.models.question_bank import QuestionBank
