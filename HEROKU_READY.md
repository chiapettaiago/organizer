# ✅ App Pronto para Heroku!

## 📦 Arquivos Configurados

### Essenciais do Heroku
- ✅ `Procfile` - Configurado com Gunicorn + Eventlet
- ✅ `requirements.txt` - Todas as dependências incluídas
- ✅ `runtime.txt` - Python 3.11.10 (versão suportada pelo Heroku)
- ✅ `app.json` - Metadados do app

### Otimização
- ✅ `.gitignore` - Arquivos ignorados no Git
- ✅ `.slugignore` - Arquivos ignorados no deploy (reduz tamanho)

### Scripts de Deploy
- ✅ `deploy_heroku.bat` - Deploy automático (Windows)
- ✅ `deploy_heroku.sh` - Deploy automático (Linux/Mac)

### Documentação
- ✅ `HEROKU_QUICKSTART.md` - Guia rápido
- ✅ `DEPLOY_HEROKU.md` - Guia completo

## 🚀 Como Fazer Deploy

### Opção 1: Script Automático (FÁCIL)

**Windows:**
```bash
deploy_heroku.bat
```

**Linux/Mac:**
```bash
chmod +x deploy_heroku.sh
./deploy_heroku.sh
```

### Opção 2: Comandos Manuais

```bash
# 1. Login
heroku login

# 2. Criar app (escolha um nome único ou deixe vazio)
heroku create nome-do-seu-app

# 3. Inicializar Git (se ainda não tiver)
git init
git add .
git commit -m "Deploy inicial MailNest"

# 4. Deploy
git push heroku main
# OU se sua branch for master:
git push heroku master

# 5. Garantir que está rodando
heroku ps:scale web=1

# 6. Abrir no navegador
heroku open
```

### Opção 3: Deploy via GitHub (SEM COMANDOS)

1. Faça push do código para GitHub
2. Acesse https://dashboard.heroku.com
3. Crie novo app
4. Vá em "Deploy" → "GitHub"
5. Conecte seu repositório
6. Clique em "Deploy Branch"
7. Pronto! 🎉

## 🔧 Mudanças Feitas no Código

### 1. Procfile
```
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```
- Usa Gunicorn (servidor WSGI para produção)
- Worker class Eventlet (necessário para WebSocket)
- Bind na porta fornecida pelo Heroku

### 2. requirements.txt
Adicionado:
- `gunicorn==21.2.0` - Servidor WSGI
- `dnspython==2.4.2` - Dependência do eventlet

### 3. app.py
```python
# Debug mode baseado em variável de ambiente
debug = os.environ.get('DEBUG', 'False').lower() == 'true'
socketio.run(app, debug=debug, host='0.0.0.0', port=port)
```

### 4. Tratamento de Erro TextBlob
Adicionado try-except para não quebrar se dados do TextBlob não estiverem disponíveis.

### 5. Timeout de Conexão
```python
imap = imaplib.IMAP4_SSL(SERVIDOR_IMAP, timeout=30)
```

## 📊 Especificações Técnicas

- **Framework**: Flask 3.0.0
- **WebSocket**: Flask-SocketIO 5.3.5
- **Servidor**: Gunicorn com Eventlet
- **Python**: 3.11.10
- **IA**: TextBlob para análise de sentimento

## 🌐 Após Deploy

Seu app estará disponível em:
```
https://nome-do-seu-app.herokuapp.com
```

## 📝 Comandos Úteis Pós-Deploy

```bash
# Ver logs em tempo real
heroku logs --tail

# Reiniciar app
heroku restart

# Ver status
heroku ps

# Abrir dashboard
heroku dashboard

# Configurar variável de ambiente
heroku config:set NOME=VALOR

# Ver todas as variáveis
heroku config
```

## 🐛 Troubleshooting

### "Application Error"
```bash
heroku logs --tail
```
Veja os logs para identificar o erro.

### App não inicia
```bash
# Verificar se dyno está rodando
heroku ps

# Escalar dyno
heroku ps:scale web=1

# Reiniciar
heroku restart
```

### WebSocket não funciona
Verifique se:
- Gunicorn está usando `--worker-class eventlet`
- Eventlet está instalado
- Flask-SocketIO está configurado corretamente

## 💰 Planos do Heroku

- **Free**: Grátis, mas app "dorme" após 30min inativo
- **Eco**: $5/mês, sem sleep
- **Basic**: $7/mês
- **Standard**: $25+/mês

Para free tier, o app pode demorar ~10s para "acordar" na primeira requisição.

## ✅ Checklist Final

- [x] Procfile configurado
- [x] requirements.txt completo
- [x] runtime.txt atualizado
- [x] Debug mode configurável
- [x] Timeouts adicionados
- [x] Tratamento de erros robusto
- [x] WebSocket funcionando
- [x] Scripts de deploy criados
- [x] Documentação completa

## 🎉 Pronto!

Seu app está 100% configurado para rodar no Heroku!

Execute `deploy_heroku.bat` (Windows) ou `./deploy_heroku.sh` (Linux/Mac) para fazer o deploy automaticamente.

Ou siga os passos em [HEROKU_QUICKSTART.md](HEROKU_QUICKSTART.md) para deploy manual.

---

**Dúvidas?** Consulte [DEPLOY_HEROKU.md](DEPLOY_HEROKU.md) para guia detalhado.
