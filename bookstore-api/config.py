import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_timeout": 30,
    "max_overflow": 5
}

CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer'
}

# Allow requests from your frontend origin
CORS_ORIGINS = [
    'http://localhost:3000',  # React app
    'http://127.0.0.1:3000'
]

class Config:
    DB_USERNAME = os.getenv("DB_USERNAME", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "ledung04gmailcom")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "bookstore")
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key_please_change")
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    JWT_ALGORITHM = 'HS256'
    
    API_TITLE = "BookStore API"
    API_VERSION = "v1"
    API_PREFIX = "/api/v1"