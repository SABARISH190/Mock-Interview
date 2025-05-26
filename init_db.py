"""
Database initialization script for Mock Interview Platform.
This creates initial users, including an admin user.
"""

import os
from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash
from datetime import datetime

def init_db():
    """Initialize the database with initial data."""
    app = create_app(os.getenv('FLASK_CONFIG') or 'config.DevelopmentConfig')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@mockinterview.com').first()
        if not admin:
            # Create admin user
            # Create admin user with all required attributes
            admin = User(
                username='admin',
                email='admin@mockinterview.com',
                password='admin12345',  # This will be hashed by the password setter
                first_name='Admin',
                last_name='User',
                phone='1234567890',
                is_admin=True,  # Ensure admin flag is set
                is_active=True,
                is_verified=True,  # Explicitly set to True
                email_verified=True,  # For backward compatibility
                otp=None,  # No OTP needed for admin
                otp_expires_at=None,
                created_at=datetime.utcnow()
            )
            # Force admin privileges
            admin.is_admin = True
            admin.is_verified = True
            admin.email_verified = True
            db.session.add(admin)
            
            # Create demo user with all required attributes
            demo_user = User(
                username='demouser',
                email='demo@mockinterview.com',
                password='demo12345',  # This will be hashed by the password setter
                first_name='Demo',
                last_name='User',
                phone='9876543210',
                is_admin=False,
                is_active=True,
                is_verified=True,  # Explicitly set to True
                email_verified=True,  # For backward compatibility
                otp=None,  # No OTP needed for demo user
                otp_expires_at=None,
                created_at=datetime.utcnow()
            )
            db.session.add(demo_user)
            
            db.session.commit()
            print("Admin and demo users created successfully!")
        else:
            print("Admin user already exists!")

if __name__ == '__main__':
    init_db()
    print("Database initialization completed!")
