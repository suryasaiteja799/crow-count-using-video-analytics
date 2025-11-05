from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@local').first():
        admin = User(name='Admin', email='admin@local', password_hash='adminpass', is_admin=True)
        # if you prefer hashed password, import helper
        try:
            from werkzeug.security import generate_password_hash
            admin.password_hash = generate_password_hash('adminpass')
        except Exception:
            pass
        db.session.add(admin)
        db.session.commit()
        print('Default admin created: admin@local / adminpass')
    else:
        print('Default admin already exists')
    users = User.query.all()
    print('Users:')
    for u in users:
        print(u.id, u.email, 'admin' if u.is_admin else 'user')
