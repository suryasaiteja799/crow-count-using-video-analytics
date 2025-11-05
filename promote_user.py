from app import create_app
from models import db, User
import sys

if len(sys.argv) < 2:
    print('Usage: python promote_user.py user@example.com')
    sys.exit(1)

email = sys.argv[1]
app = create_app()

with app.app_context():
    u = User.query.filter_by(email=email).first()
    if not u:
        print('User not found:', email)
        sys.exit(1)
    u.is_admin = True
    db.session.commit()
    print('User promoted to admin:', u.email)
