#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

# Este comando garante que as tabelas sejam criadas no Postgres do Render
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"