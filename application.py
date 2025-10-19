import sys
import os

# Add current directory and backend to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'backend'))

try:
    # Try importing the FastAPI app
    from backend.main import app
    application = app
except Exception as e:
    # Fallback: create a simple WSGI app that shows the error
    def application(environ, start_response):
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [f'Import Error: {str(e)}'.encode('utf-8')]