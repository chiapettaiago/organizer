# 🚀 Deploy Rápido no Heroku

## Método 1: Script Automático (Recomendado)

### Windows:
```bash
deploy_heroku.bat
```

### Linux/Mac:
```bash
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

## Método 2: Manual

### 1. Login
```bash
heroku login
```

### 2. Criar App
```bash
heroku create mailnest-organizer
```

### 3. Deploy
```bash
git init
git add .
git commit -m "Deploy inicial"
git push heroku main
```

### 4. Escalar
```bash
heroku ps:scale web=1
```

### 5. Abrir
```bash
heroku open
```

## 📋 Checklist Pré-Deploy

- [x] Procfile configurado com Gunicorn
- [x] requirements.txt atualizado
- [x] runtime.txt com Python 3.11.10
- [x] app.json configurado
- [x] .gitignore criado
- [x] .slugignore para otimização

## 🔍 Comandos Úteis

```bash
# Ver logs
heroku logs --tail

# Reiniciar
heroku restart

# Status
heroku ps

# Configurar variável
heroku config:set DEBUG=False

# Ver variáveis
heroku config

# Abrir dashboard
heroku dashboard
```

## ⚡ Deploy via GitHub (Alternativa)

1. Faça push para GitHub
2. No Heroku Dashboard:
   - Deploy → GitHub
   - Conecte repositório
   - Enable Automatic Deploys

## 🎯 URL Final

Seu app estará em:
```
https://nome-do-seu-app.herokuapp.com
```

## 📞 Problemas?

Veja [DEPLOY_HEROKU.md](DEPLOY_HEROKU.md) para troubleshooting completo.
