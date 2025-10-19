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
    # Fallback: use simple working app
    from simple_app import application