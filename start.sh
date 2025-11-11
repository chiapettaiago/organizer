#!/bin/bash

# Script de inicialização para ambiente de produção

echo "🚀 Iniciando Gmail Organizer Pro..."

# Cria diretório .streamlit se não existir
mkdir -p ~/.streamlit/

# Configura credenciais do Streamlit
echo "\
[general]\n\
email = \"\"\n\
" > ~/.streamlit/credentials.toml

# Configura servidor
echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = ${PORT:-8501}\n\
address = \"0.0.0.0\"\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
serverAddress = \"0.0.0.0\"\n\
serverPort = ${PORT:-8501}\n\
\n\
[theme]\n\
primaryColor = \"#667eea\"\n\
backgroundColor = \"#FFFFFF\"\n\
secondaryBackgroundColor = \"#f0f2f6\"\n\
textColor = \"#262730\"\n\
font = \"sans serif\"\n\
" > ~/.streamlit/config.toml

echo "✅ Configuração concluída!"
echo "🌐 Servidor iniciará na porta ${PORT:-8501}"
