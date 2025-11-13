# 🚀 Deploy no Heroku - MailNest

## 📋 Pré-requisitos

1. Conta no Heroku: https://signup.heroku.com/
2. Heroku CLI instalado: https://devcenter.heroku.com/articles/heroku-cli
3. Git instalado

## 🔧 Passo a Passo

### 1. Login no Heroku

```bash
heroku login
```

### 2. Criar App no Heroku

```bash
# Navegar até a pasta do projeto
cd c:\Users\078463\organizer

# Criar novo app (escolha um nome único)
heroku create mailnest-organizer

# Ou deixar o Heroku gerar um nome aleatório
heroku create
```

### 3. Configurar Git (se ainda não estiver configurado)

```bash
git init
git add .
git commit -m "Initial commit - MailNest Flask App"
```

### 4. Adicionar Remote do Heroku

```bash
# Se você criou o app manualmente
heroku git:remote -a nome-do-seu-app

# Ou se usou heroku create, o remote já foi adicionado
```

### 5. Deploy para o Heroku

```bash
git push heroku main
```

Se sua branch principal for `master`:
```bash
git push heroku master
```

### 6. Abrir o App

```bash
heroku open
```

## 🔍 Verificar Logs

```bash
# Ver logs em tempo real
heroku logs --tail

# Ver últimos logs
heroku logs --tail -n 200
```

## ⚙️ Configurações Adicionais

### Escalar Dynos

```bash
# Garantir que pelo menos 1 dyno está rodando
heroku ps:scale web=1
```

### Verificar Status

```bash
heroku ps
```

### Reiniciar App

```bash
heroku restart
```

## 🐛 Troubleshooting

### Erro: "No web processes running"

```bash
heroku ps:scale web=1
```

### Erro de Build

```bash
# Ver logs detalhados do build
heroku logs --tail

# Verificar se o Procfile está correto
cat Procfile
```

### App não responde

```bash
# Verificar logs
heroku logs --tail

# Reiniciar
heroku restart
```

## 📊 Monitoramento

### Acessar Dashboard

```bash
heroku dashboard
```

Ou acesse: https://dashboard.heroku.com/apps

### Métricas

```bash
heroku logs --ps web --tail
```

## 💰 Planos

- **Free**: Grátis, mas o app "dorme" após 30 min de inatividade
- **Hobby**: $7/mês, sem sleep, SSL grátis
- **Standard**: A partir de $25/mês, mais recursos

## 🔐 Variáveis de Ambiente (Opcional)

Se precisar adicionar variáveis de ambiente:

```bash
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=sua-chave-secreta
```

Ver variáveis:
```bash
heroku config
```

## 🌐 Custom Domain (Opcional)

```bash
heroku domains:add www.seudominio.com
```

## 📱 Deploy Automático via GitHub

1. Acesse o Dashboard do Heroku
2. Vá em "Deploy" > "Deployment method"
3. Selecione "GitHub"
4. Conecte seu repositório
5. Ative "Automatic Deploys" na branch desejada

## ✅ Checklist de Deploy

- [ ] Procfile configurado corretamente
- [ ] requirements.txt atualizado
- [ ] runtime.txt com versão Python suportada
- [ ] .gitignore configurado
- [ ] Git repositório inicializado
- [ ] Commit feito
- [ ] App criado no Heroku
- [ ] Deploy realizado
- [ ] App acessível via URL
- [ ] Logs sem erros críticos

## 🎉 Seu app estará disponível em:

```
https://nome-do-seu-app.herokuapp.com
```

## 📞 Suporte

- Documentação Heroku: https://devcenter.heroku.com/
- Stack Overflow: https://stackoverflow.com/questions/tagged/heroku
