#!/bin/bash

echo "========================================"
echo "  Deploy MailNest para Heroku"
echo "========================================"
echo ""

# Verificar se Heroku CLI está instalado
if ! command -v heroku &> /dev/null; then
    echo "[ERRO] Heroku CLI não encontrado!"
    echo "Por favor, instale: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "[1/6] Verificando login no Heroku..."
if ! heroku whoami &> /dev/null; then
    echo "Fazendo login no Heroku..."
    heroku login
fi

echo ""
echo "[2/6] Inicializando repositório Git (se necessário)..."
if [ ! -d .git ]; then
    git init
    echo "Repositório Git inicializado!"
else
    echo "Repositório Git já existe!"
fi

echo ""
echo "[3/6] Adicionando arquivos ao Git..."
git add .
git commit -m "Deploy: MailNest Flask App com WebSocket"

echo ""
echo "[4/6] Criando app no Heroku (se necessário)..."
read -p "Digite o nome do app (ou pressione Enter para nome automático): " APP_NAME

if [ -z "$APP_NAME" ]; then
    heroku create
else
    heroku create "$APP_NAME"
fi

echo ""
echo "[5/6] Fazendo deploy para o Heroku..."
if ! git push heroku main; then
    echo "Tentando push da branch master..."
    git push heroku master
fi

echo ""
echo "[6/6] Escalando dyno..."
heroku ps:scale web=1

echo ""
echo "========================================"
echo "  Deploy Concluído!"
echo "========================================"
echo ""
echo "Abrindo app no navegador..."
heroku open

echo ""
echo "Para ver logs: heroku logs --tail"
echo "Para reiniciar: heroku restart"
echo ""
