from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    # Whether the user account is active; super-admins can block accounts by setting this False
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def role(self):
        if self.is_super_admin:
            return 'super_admin'
        elif self.is_admin:
            return 'admin'
        return 'user'

class VideoRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    filename = db.Column(db.String(300), nullable=False)
    total_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(32), default='pending')
    error_message = db.Column(db.String(500), nullable=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    zones = db.Column(db.Text, nullable=True)  # JSON string containing zone coordinates
    grid_size = db.Column(db.Text, nullable=True)  # JSON string containing grid dimensions

    user = db.relationship('User', backref=db.backref('records', lazy=True))


class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(200))
    success = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(100))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('login_history', lazy=True))


def create_app_db(app):
    # Ensure tables exist. db should be initialized by caller via db.init_app(app).
    with app.app_context():
        # Drop existing tables and create new ones
        db.drop_all()
        db.create_all()
        
        # Create default super admin (change credentials here)
        super_admin_email = 'suryasaiteja799@gmail.com'
        super_admin_pw = 'Lucky@799'
        if not User.query.filter_by(email=super_admin_email).first():
            super_admin = User(
                name='Super Admin',
                email=super_admin_email,
                password_hash=generate_password_hash(super_admin_pw),
                is_admin=True,
                is_super_admin=True
            )
            db.session.add(super_admin)
            db.session.commit()

        # Create default admin
        admin_email = '23kq1a6350@pace.ac.in'
        admin_pw = 'Teja@6350'
        if not User.query.filter_by(email=admin_email).first():
            admin = User(name='Admin', email=admin_email, password_hash=generate_password_hash(admin_pw), is_admin=True)
            db.session.add(admin)
            db.session.commit()


def hash_password(password: str) -> str:
    return generate_password_hash(password)
