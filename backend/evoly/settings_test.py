"""
Settings utilisés par pytest (voir pytest.ini : DJANGO_SETTINGS_MODULE).
Le nom ne doit pas correspondre à python_files de pytest.ini, sinon le fichier
serait collecté comme un module de test.

pytest-django charge django.conf.settings avant d'importer les conftest.py,
donc les variables d'environnement de test doivent être définies ici, pas dans
un conftest.py.
"""

import os
import tempfile

os.environ.setdefault("DJANGO_SECRET_KEY", "cle-de-test-insecure-uniquement-pour-pytest")
os.environ.setdefault("DEBUG", "False")
os.environ.setdefault("DB_ENGINE", "django.db.backends.sqlite3")

from .settings import *

# Hachage MD5 : beaucoup plus rapide que pbkdf2. Sans cela, chaque
# create_user / check_password coûte ~1 s et la suite devient inutilisable.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# WhiteNoise avertit si STATIC_ROOT n'existe pas. Les tests n'utilisent jamais
# les fichiers statiques, on pointe donc vers un dossier temporaire qui, lui,
# existe : plus de UserWarning à chaque requête.
STATIC_ROOT = tempfile.mkdtemp(prefix="evoly-staticfiles-test-")
