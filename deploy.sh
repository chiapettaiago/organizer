#!/bin/bash
# Script helper para deploy no Heroku com verificações

echo "🚀 ===== HEROKU DEPLOY HELPER ====="
echo ""

# Verificar se está no git
if [ ! -d ".git" ]; then
    echo "❌ Erro: Não está em um repositório git!"
    echo "Execute: git init"
    exit 1
fi

echo "✅ Repositório git encontrado"

# Verificar arquivos necessários
FILES=("Procfile" "migrate_db.py" "requirements.txt" "app.py")
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Erro: Arquivo $file não encontrado!"
        exit 1
    fi
    echo "✅ $file encontrado"
done

# Verificar se Procfile tem release phase
if ! grep -q "release:" Procfile; then
    echo "⚠️  Aviso: Procfile não tem fase 'release:'"
    echo "   Migração não será executada automaticamente!"
else
    echo "✅ Procfile configurado com release phase"
fi

echo ""
echo "📋 Resumo da configuração:"
echo "   - Procfile: $(cat Procfile)"
echo ""

# Verificar mudanças não commitadas
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Mudanças detectadas. Deseja commitá-las?"
    echo "   Arquivos modificados:"
    git status --short
    echo ""
    read -p "Commit automaticamente? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        read -p "Mensagem do commit: " commit_msg
        git add .
        git commit -m "$commit_msg"
        echo "✅ Commit realizado"
    else
        echo "⚠️  Prosseguindo sem commit"
    fi
else
    echo "✅ Nenhuma mudança pendente"
fi

echo ""
echo "🚀 Pronto para deploy!"
echo ""
echo "Comandos sugeridos:"
echo "   1. git push heroku main          # Deploy normal"
echo "   2. heroku logs --tail            # Ver logs em tempo real"
echo "   3. heroku run python migrate_db.py  # Executar migração manualmente"
echo "   4. heroku open                   # Abrir app no navegador"
echo ""

read -p "Executar deploy agora? (s/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "🚀 Executando deploy..."
    git push heroku main
    
    echo ""
    echo "✅ Deploy concluído!"
    echo ""
    read -p "Abrir logs? (s/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        heroku logs --tail
    fi
else
    echo "ℹ️  Deploy cancelado"
fi
