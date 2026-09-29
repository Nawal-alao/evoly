"""
Settings utilisés par pytest (voir pytest.ini : DJANGO_SETTINGS_MODULE).
Le nom ne doit pas correspondre à python_files de pytest.ini, sinon le fichier
serait collecté comme un module de test.

pytest-django charge django.conf.settings avant d'importer les conftest.py,
donc les variables d'environnement de test doivent être définies ici, pas dans
un conftest.py.
"""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "cle-de-test-insecure-uniquement-pour-pytest")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

from .settings import *
