# settings.py

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'app',

]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # 你可以加自訂 templates 路徑
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


BASE_DIR = Path(__file__).resolve().parent.parent


# 只顯示與資料庫相關部分，使用 SQLite 預設即可

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]  # 你可以加自訂 static 路徑
STATIC_ROOT = BASE_DIR / "staticfiles"  # 用於收集靜態檔案的路徑
ROOT_URLCONF = "config.urls"
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TEMPLATES[0]['DIRS'] = [BASE_DIR / "templates"]
