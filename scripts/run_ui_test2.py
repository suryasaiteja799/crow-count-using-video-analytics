import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
app=create_app()
with app.app_context():
	client=app.test_client()
	# test actions below will run inside app context
	import time
	email=f"ui2_{int(time.time())}@example.com"
	print('email', email)
	print('register ->', client.post('/register', data={'name':'UI Test','email':email,'password':'abc12345'}).status_code)
	print('login ->', client.post('/login', data={'email':email,'password':'abc12345'}).status_code)
