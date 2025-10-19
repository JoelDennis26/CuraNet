import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from backend.main import app

# WSGI application
application = app