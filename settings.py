import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "darwin":
    with open(os.path.join(BASE_DIR,'secret_dev.json'),'r') as f:
        d = json.load(f)
else:
    with open(os.path.join(BASE_DIR,'secret.json'),'r') as f:
        d = json.load(f)

if sys.platform == "darwin":
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': f"{d['db']}",
            'USER': f"{d['db_user']}",
            'PASSWORD': f"{d['db_pw']}",
            'HOST': 'localhost',
            'PORT': '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': f"{d['db']}",
            'USER': f"{d['db_user']}",
            'PASSWORD': f"{d['db_pw']}",
            'HOST': 'localhost',
            'PORT': '',
        }
    }

INSTALLED_APPS = (
    'db',
)

SECRET_KEY = 'REPLACE_ME'
USE_TZ=True