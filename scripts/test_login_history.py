import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from models import User, LoginHistory
app = create_app()
with app.app_context():
    client = app.test_client()
    # perform a failed login
    client.post('/login', data={'email':'noone@example.com','password':'badpass'})
    # perform a successful admin login
    client.post('/admin-login', data={'email':'23kq1a6350@pace.ac.in','password':'Suryasaiteja'})
    # fetch admin page
    resp = client.get('/admin')
    data = resp.get_data(as_text=True)
    print('admin page length', len(data))
    # show a snippet where login history table appears
    idx = data.find('Login History')
    print('snippet:', data[idx:idx+400])
    print('login history rows count:', LoginHistory.query.count())
    for lh in LoginHistory.query.order_by(LoginHistory.timestamp.desc()).limit(5):
        print(lh.timestamp, lh.email, lh.success, lh.ip_address)
