from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "CuraNet is working!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Simple WSGI application
application = app