import sys
from app import create_app
from models import db, User

def run_test():
    app = create_app()
    import time
    test_email = f'testuser_{int(time.time())}@example.com'
    test_name = 'Test User'
    test_password = 'TestPass123'

    with app.app_context():
        # ensure tables exist
        db.create_all()
        # remove existing test user
        existing = User.query.filter_by(email=test_email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()

        client = app.test_client()
        resp = client.post('/register', data={
            'name': test_name,
            'email': test_email,
            'password': test_password
        }, follow_redirects=True)

        user = User.query.filter_by(email=test_email).first()
        if user:
            print('SUCCESS: User registered in DB:', user.email)
            return 0
        else:
            print('FAIL: User not found in DB after registration')
            print('Response code:', resp.status_code)
            print(resp.data.decode('utf-8')[:1000])
            return 2

if __name__ == '__main__':
    sys.exit(run_test())
