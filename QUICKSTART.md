# ⚡ Início Rápido - Gmail Organizer Pro

## 🎯 Em 5 Minutos

### 1️⃣ Gere uma Senha de Aplicativo

1. Acesse: https://myaccount.google.com/apppasswords
2. Faça login na sua conta Google
3. Selecione "E-mail" como app
4. Selecione "Outro" como dispositivo
5. Digite "Gmail Organizer"
6. Clique em "Gerar"
7. **Copie a senha de 16 caracteres**

### 2️⃣ Execute Localmente

```bash
# Instale as dependências
pip install -r requirements.txt

# Execute o app
streamlit run organizador.py
```

### 3️⃣ Use o App

1. Abra http://localhost:8501
2. Cole suas credenciais na sidebar
3. Clique em "Organizar Agora"
4. Pronto! 🎉

---

## 🚀 Deploy em 1 Clique

### Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Streamlit Cloud
1. Fork este repo
2. Acesse https://share.streamlit.io
3. Clique em "New app"
4. Selecione o repo
5. Deploy! ✅

---

## 🎓 Próximos Passos

- 📖 Leia a [Documentação Completa](README.md)
- 🚀 Veja o [Guia de Deploy](DEPLOY.md)
- 💡 Personalize as categorias
- ⏰ Configure o agendador

---

## ❓ Problemas Comuns

**"Invalid credentials"**
- Certifique-se de usar uma senha de aplicativo, não sua senha normal

**"IMAP not enabled"**
- Ative IMAP no Gmail: Configurações → Encaminhamento e POP/IMAP

**"App não carrega"**
- Verifique se instalou todas as dependências
- Teste com: `pip list | grep streamlit`

---

**Precisa de ajuda?** Abra uma [Issue](https://github.com/seu-usuario/gmail-organizer-pro/issues)
