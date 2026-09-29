# Évoly

Plateforme éducative : cours, mentorat, évaluations et communauté.
Monorepo en deux parties indépendantes :

```
evoly/
├── backend/          # API Django + Django REST Framework
│   ├── evoly/        # Configuration du projet (settings, urls, wsgi)
│   ├── comptes/      # Élèves, mentors, authentification
│   ├── pedagogie/    # Cours, séquences, matières
│   ├── evaluations/  # Examens, questions, résultats, progression
│   ├── communaute/   # Groupes d'étude, conversations
│   ├── abonnements/  # Plans et abonnements premium
│   ├── api/          # Routage API agrégé
│   ├── templates/    # Templates Django (admin, vues serveur)
│   ├── static/       # Fichiers statiques Django
│   ├── manage.py
│   └── requirements.txt
├── frontend/         # SPA React (Vite)
│   ├── src/
│   └── public/
└── render.yaml       # Blueprint de déploiement Render (backend)
```

## Développement local

Prérequis : Python ≥ 3.12 (+ venv), Node.js, PostgreSQL.

### Backend (port 8000)

```bash
cd backend
cp .env.example .env            # puis renseigner les valeurs
python -m venv ../.venv && source ../.venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver      # http://127.0.0.1:8000
```

La base est configurée via les variables `DB_*` du `.env`
(PostgreSQL par défaut ; `DB_ENGINE='django.db.backends.sqlite3'` pour
retomber sur SQLite en dev).

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

En développement, le proxy Vite transmet `/api` vers `http://127.0.0.1:8000`
: aucune variable d'environnement n'est nécessaire. En production,
`VITE_API_URL` pointe vers le backend déployé (voir `frontend/.env.example`).

### Tests et qualité (backend)

Les outils de développement sont dans `backend/requirements-dev.txt`
(`pip install -r requirements-dev.txt`).

```bash
cd backend
pytest                    # suite de tests (settings dédiés : evoly/settings_test.py)
pytest --collect-only -q   # lister les tests
ruff check .               # lint
ruff check . --fix         # corrections automatiques
```

La configuration du lint est dans `backend/ruff.toml`. Les migrations sont
exclues du lint : elles sont générées par Django et ne sont jamais retouchées.

## Déploiement

| Composant | Hébergeur | Rôle |
|---|---|---|
| Frontend React | Vercel | Site statique (`rootDir: frontend`) |
| API Django | Render (plan gratuit) | Serveur d'application (gunicorn) |
| PostgreSQL | Supabase (plan gratuit) | Base de données managée uniquement |
| Médias uploadés | Supabase Storage (S3) | Images des cours — disque Render éphémère |

Le fichier `render.yaml` décrit le service Render. Les secrets (clé API,
mots de passe base de données, clés S3) ne sont jamais commités : ils se
configurent dans les dashboards respectifs (Render, Vercel).
