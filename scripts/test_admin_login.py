import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
app = create_app()
client = app.test_client()
resp = client.post('/admin-login', data={'email':'admin@local','password':'adminpass'}, follow_redirects=False)
print('admin-login status', resp.status_code, 'location', resp.headers.get('Location'))
resp2 = client.get('/admin', follow_redirects=False)
print('admin page access status', resp2.status_code)
