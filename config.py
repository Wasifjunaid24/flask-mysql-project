import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a_random_secret_key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///recipe.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

