from app import create_app

app = create_app()
client = app.test_client()

import time
email = f"test_ui_{int(time.time())}@example.com"
print('Testing with email:', email)
# register
resp = client.post('/register', data={'name':'UI Tester','email':email,'password':'secret123'}, follow_redirects=False)
print('register', resp.status_code, 'location=', resp.headers.get('Location'))
# login with remember
resp2 = client.post('/login', data={'email':email,'password':'secret123','remember':'on'}, follow_redirects=False)
print('login', resp2.status_code, 'location=', resp2.headers.get('Location'))
# access dashboard
# follow redirects to observe final content
resp3 = client.get('/dashboard', follow_redirects=False)
print('dashboard access', resp3.status_code)

print('Cookies:', resp2.headers.get('Set-Cookie'))
print('Done')
