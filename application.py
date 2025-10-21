def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)
    return [b'{"message": "CuraNet Basic WSGI is working!", "status": "success"}']

# Try to import FastAPI app if possible
try:
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    sys.path.insert(0, os.path.join(current_dir, 'backend'))
    from backend.main import app
    application = app
except:
    pass  # Use the basic WSGI app above