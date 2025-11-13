# Script PowerShell para deploy no Heroku com verificações
# Uso: .\deploy.ps1

Write-Host "🚀 ===== HEROKU DEPLOY HELPER =====" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no git
if (-not (Test-Path ".git")) {
    Write-Host "❌ Erro: Não está em um repositório git!" -ForegroundColor Red
    Write-Host "Execute: git init" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Repositório git encontrado" -ForegroundColor Green

# Verificar arquivos necessários
$files = @("Procfile", "migrate_db.py", "requirements.txt", "app.py")
foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Erro: Arquivo $file não encontrado!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ $file encontrado" -ForegroundColor Green
}

# Verificar se Procfile tem release phase
$procfileContent = Get-Content "Procfile" -Raw
if ($procfileContent -notmatch "release:") {
    Write-Host "⚠️  Aviso: Procfile não tem fase 'release:'" -ForegroundColor Yellow
    Write-Host "   Migração não será executada automaticamente!" -ForegroundColor Yellow
} else {
    Write-Host "✅ Procfile configurado com release phase" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Resumo da configuração:" -ForegroundColor Cyan
Write-Host "   - Procfile: $procfileContent"
Write-Host ""

# Verificar mudanças não commitadas
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Mudanças detectadas. Deseja commitá-las?" -ForegroundColor Yellow
    Write-Host "   Arquivos modificados:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    
    $commitChoice = Read-Host "Commit automaticamente? (s/N)"
    if ($commitChoice -eq "s" -or $commitChoice -eq "S") {
        $commitMsg = Read-Host "Mensagem do commit"
        git add .
        git commit -m "$commitMsg"
        Write-Host "✅ Commit realizado" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Prosseguindo sem commit" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ Nenhuma mudança pendente" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Pronto para deploy!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Comandos sugeridos:" -ForegroundColor Cyan
Write-Host "   1. git push heroku main                # Deploy normal" -ForegroundColor White
Write-Host "   2. heroku logs --tail                  # Ver logs em tempo real" -ForegroundColor White
Write-Host "   3. heroku run python migrate_db.py     # Executar migração manualmente" -ForegroundColor White
Write-Host "   4. heroku open                         # Abrir app no navegador" -ForegroundColor White
Write-Host ""

$deployChoice = Read-Host "Executar deploy agora? (s/N)"
if ($deployChoice -eq "s" -or $deployChoice -eq "S") {
    Write-Host "🚀 Executando deploy..." -ForegroundColor Cyan
    git push heroku main
    
    Write-Host ""
    Write-Host "✅ Deploy concluído!" -ForegroundColor Green
    Write-Host ""
    
    $logsChoice = Read-Host "Abrir logs? (s/N)"
    if ($logsChoice -eq "s" -or $logsChoice -eq "S") {
        heroku logs --tail
    }
} else {
    Write-Host "ℹ️  Deploy cancelado" -ForegroundColor Yellow
}
