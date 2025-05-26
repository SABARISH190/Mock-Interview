from datetime import datetime
import hashlib
from app import db, login_manager, bcrypt
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app, request

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_created_at = db.Column(db.DateTime, nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    resumes = db.relationship('Resume', backref='user', lazy=True, cascade='all, delete-orphan')
    interviews = db.relationship('Interview', backref='user', lazy=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], salt='password-reset-salt')
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')
    
    @staticmethod
    def gravatar(self, size=100, default='identicon', rating='g'):
        if self.email:
            email = self.email.lower().encode('utf-8')
            hash = hashlib.md5(email).hexdigest()
            return f'https://www.gravatar.com/avatar/{hash}?s={size}&d={default}&r={rating}'
        return f'https://www.gravatar.com/avatar/?s={size}&d={default}&r={rating}'

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'], salt='password-reset-salt')
        try:
            user_id = s.loads(token, max_age=1800)['user_id']
        except:
            return None
        return User.query.get(user_id)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username
    
    def gravatar(self, size=100, default='identicon', rating='g'):
        """Return the Gravatar URL for the user's email with a local fallback."""
        import hashlib
        from urllib.parse import urlencode
        
        # Create the hash for the email
        email = self.email.lower().encode('utf-8')
        hash_value = hashlib.md5(email).hexdigest()
        
        # Build the URL with a fallback to a local avatar if Gravatar is blocked
        params = {
            'd': 'mp',  # Use a simple, consistent default avatar
            's': str(size),
            'r': rating
        }
        
        # Return a data URL with a simple SVG avatar as fallback
        fallback_avatar = f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='40' r='20' fill='%236c757d'/%3E%3Ccircle cx='50' cy='100' r='40' fill='%236c757d'/%3E%3C/svg%3E"
        
        # Return both Gravatar URL and fallback as a data attribute
        return {
            'url': f"https://www.gravatar.com/avatar/{hash_value}?{urlencode(params)}",
            'fallback': fallback_avatar,
            'alt': f"Avatar for {self.username}"
        }
    
    def __repr__(self):
        return f"<User {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
