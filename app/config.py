import os

SECRET_KEY = os.getenv('SECRET_KEY', 'secret-key')

# Для локальной проверки используется SQLite. На хостинге можно заменить DATABASE_URL
# на строку подключения к MySQL университета.
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///project.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')
