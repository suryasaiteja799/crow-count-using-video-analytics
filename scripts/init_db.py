import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from models import create_app_db, User, LoginHistory
app = create_app()
with app.app_context():
    create_app_db(app)
    print('users:', User.query.count())
    print('login history:', LoginHistory.query.count())
