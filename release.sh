#!/bin/bash
# Release phase - Executado antes do deploy no Heroku

echo "🔧 Executando migração do banco de dados..."
python migrate_db.py

echo "✅ Migração concluída!"
