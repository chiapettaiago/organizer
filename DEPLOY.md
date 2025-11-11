# 🚀 Guia de Deploy - Gmail Organizer Pro

Este guia contém instruções detalhadas para fazer deploy da aplicação em diferentes plataformas.

## 📋 Índice

1. [Deploy no Heroku](#deploy-no-heroku)
2. [Deploy no Streamlit Cloud](#deploy-no-streamlit-cloud)
3. [Deploy no Railway](#deploy-no-railway)
4. [Deploy no Render](#deploy-no-render)
5. [Execução Local](#execução-local)

---

## 🟣 Deploy no Heroku

### Pré-requisitos
- Conta no [Heroku](https://heroku.com)
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) instalado
- Git instalado

### Método 1: Via Heroku CLI

```bash
# 1. Login no Heroku
heroku login

# 2. Crie um novo app (escolha um nome único)
heroku create gmail-organizer-pro-seu-nome

# 3. Adicione o buildpack Python
heroku buildpacks:set heroku/python

# 4. Configure o Git remote (se necessário)
heroku git:remote -a gmail-organizer-pro-seu-nome

# 5. Faça o deploy
git add .
git commit -m "Deploy inicial"
git push heroku main

# 6. Abra o app
heroku open

# 7. Visualize os logs (opcional)
heroku logs --tail
```

### Método 2: Via Dashboard Heroku

1. Acesse [dashboard.heroku.com](https://dashboard.heroku.com)
2. Clique em **"New"** → **"Create new app"**
3. Digite o nome do app e escolha a região
4. Na aba **"Deploy"**:
   - Conecte com GitHub (recomendado)
   - Ou use Heroku Git
5. Clique em **"Deploy Branch"**
6. Aguarde o build completar
7. Clique em **"Open app"**

### Método 3: Deploy Automático com GitHub

1. Fork este repositório
2. No Heroku Dashboard, conecte com GitHub
3. Selecione o repositório
4. Ative **"Automatic Deploys"**
5. Cada push no branch main fará deploy automático

### Troubleshooting Heroku

**Erro: "Application Error"**
```bash
# Verifique os logs
heroku logs --tail

# Reinicie o dyno
heroku restart
```

**Erro: Port já em uso**
- O Heroku define a porta automaticamente via $PORT
- Não é necessário configurar manualmente

---

## ☁️ Deploy no Streamlit Cloud

### Pré-requisitos
- Conta no [Streamlit Cloud](https://streamlit.io/cloud)
- Repositório no GitHub

### Passo a Passo

1. **Prepare o Repositório**
   ```bash
   # Certifique-se de ter estes arquivos:
   # - organizador.py
   # - requirements.txt
   # - .streamlit/config.toml
   ```

2. **Faça o Deploy**
   - Acesse [share.streamlit.io](https://share.streamlit.io)
   - Clique em **"New app"**
   - Conecte com GitHub
   - Selecione o repositório
   - Branch: `main`
   - Main file: `organizador.py`
   - Clique em **"Deploy"**

3. **Configure Secrets (Opcional)**
   - No dashboard, vá em **"Settings"** → **"Secrets"**
   - Adicione:
   ```toml
   [gmail]
   email = "seu-email@gmail.com"
   password = "sua-senha-de-aplicativo"
   ```

4. **Acesse o App**
   - URL: `https://seu-app.streamlit.app`

### Vantagens Streamlit Cloud
- ✅ Deploy gratuito
- ✅ SSL/HTTPS automático
- ✅ Integração com GitHub
- ✅ Auto-deploy em commits
- ✅ Gerenciamento de secrets

---

## 🚂 Deploy no Railway

### Pré-requisitos
- Conta no [Railway](https://railway.app)

### Passo a Passo

1. **Prepare o Projeto**
   ```bash
   # Crie um arquivo railway.json (opcional)
   {
     "build": {
       "builder": "NIXPACKS"
     },
     "deploy": {
       "startCommand": "streamlit run organizador.py --server.port=$PORT"
     }
   }
   ```

2. **Deploy**
   - Acesse [railway.app](https://railway.app)
   - Clique em **"New Project"**
   - Selecione **"Deploy from GitHub repo"**
   - Escolha o repositório
   - Railway detectará automaticamente como Python app

3. **Configure Variáveis**
   - Vá em **"Variables"**
   - Adicione `PORT=8501` (se necessário)

4. **Acesse o App**
   - Railway gerará um domínio automático
   - Você pode adicionar domínio customizado

---

## 🎨 Deploy no Render

### Pré-requisitos
- Conta no [Render](https://render.com)

### Passo a Passo

1. **Crie o Web Service**
   - Acesse [dashboard.render.com](https://dashboard.render.com)
   - Clique em **"New +"** → **"Web Service"**
   - Conecte com GitHub
   - Selecione o repositório

2. **Configure o Service**
   - **Name**: gmail-organizer-pro
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run organizador.py --server.port=$PORT --server.address=0.0.0.0`

3. **Configure Variáveis de Ambiente**
   ```
   PYTHON_VERSION=3.11.0
   STREAMLIT_SERVER_HEADLESS=true
   ```

4. **Deploy**
   - Clique em **"Create Web Service"**
   - Aguarde o build completar

---

## 💻 Execução Local

### Desenvolvimento

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/gmail-organizer-pro.git
cd gmail-organizer-pro

# 2. Crie um ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute o app
streamlit run organizador.py

# 6. Acesse no navegador
# http://localhost:8501
```

### Produção Local (com Docker)

```bash
# 1. Crie um Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "organizador.py", "--server.port=8501", "--server.address=0.0.0.0"]

# 2. Build a imagem
docker build -t gmail-organizer-pro .

# 3. Execute o container
docker run -p 8501:8501 gmail-organizer-pro

# 4. Acesse
# http://localhost:8501
```

---

## 🔧 Configurações Avançadas

### Otimização para Produção

**requirements.txt** (adicione para melhor performance):
```txt
streamlit==1.31.0
textblob==0.17.1
python-dotenv==1.0.0
# Otimizações
gunicorn==21.2.0
```

### Monitoramento

**Heroku**:
```bash
# Adicione logs estruturados
heroku addons:create papertrail

# Monitore métricas
heroku addons:create newrelic
```

**Streamlit Cloud**:
- Métricas automáticas no dashboard

### Escalabilidade

Para processar muitos e-mails simultaneamente:

```python
# Adicione ao código
import concurrent.futures

def processar_email_paralelo(emails):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        resultados = executor.map(classificar_email, emails)
    return list(resultados)
```

---

## 📊 Comparação de Plataformas

| Plataforma | Gratuito | Facilidade | Performance | SSL | Domínio Custom |
|------------|----------|------------|-------------|-----|----------------|
| Heroku | ⚠️ Limitado | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ✅ (pago) |
| Streamlit Cloud | ✅ Sim | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | ❌ |
| Railway | ⚠️ Limitado | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | ✅ |
| Render | ⚠️ Limitado | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ | ✅ |

---

## 🆘 Suporte

Problemas com deploy? 

1. Verifique os logs da plataforma
2. Confira os arquivos de configuração
3. Abra uma [Issue no GitHub](https://github.com/seu-usuario/gmail-organizer-pro/issues)

---

**Bom deploy! 🚀**
