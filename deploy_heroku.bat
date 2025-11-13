@echo off
echo ========================================
echo   Deploy MailNest para Heroku
echo ========================================
echo.

REM Verificar se Heroku CLI está instalado
where heroku >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Heroku CLI nao encontrado!
    echo Por favor, instale: https://devcenter.heroku.com/articles/heroku-cli
    pause
    exit /b 1
)

echo [1/6] Verificando login no Heroku...
heroku whoami >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Fazendo login no Heroku...
    heroku login
)

echo.
echo [2/6] Inicializando repositorio Git (se necessario)...
if not exist .git (
    git init
    echo Repositorio Git inicializado!
) else (
    echo Repositorio Git ja existe!
)

echo.
echo [3/6] Adicionando arquivos ao Git...
git add .
git commit -m "Deploy: MailNest Flask App com WebSocket"

echo.
echo [4/6] Criando app no Heroku (se necessario)...
set /p APP_NAME="Digite o nome do app (ou pressione Enter para nome automatico): "

if "%APP_NAME%"=="" (
    heroku create
) else (
    heroku create %APP_NAME%
)

echo.
echo [5/6] Fazendo deploy para o Heroku...
git push heroku main
if %ERRORLEVEL% NEQ 0 (
    echo Tentando push da branch master...
    git push heroku master
)

echo.
echo [6/6] Escalando dyno...
heroku ps:scale web=1

echo.
echo ========================================
echo   Deploy Concluido!
echo ========================================
echo.
echo Abrindo app no navegador...
heroku open

echo.
echo Para ver logs: heroku logs --tail
echo Para reiniciar: heroku restart
echo.
pause
