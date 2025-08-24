import os

class Config:
    SECRET_KEY = 'PASSWORD'
    APP_NAME = 'HTSS Payments'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/collections.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True  # Set to False in production