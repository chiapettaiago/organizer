#!/bin/bash
# Script executado após o build no Heroku

echo "Baixando dados do TextBlob..."
python -m textblob.download_corpora

echo "Configuração pós-build concluída!"
