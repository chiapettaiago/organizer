# MailNest - Organizador de E-mails com Flask

![MailNest](https://img.shields.io/badge/MailNest-v2.0-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📮 Sobre o MailNest

MailNest é um organizador inteligente de e-mails do Gmail que utiliza análise de sentimento e categorização automática para organizar sua caixa de entrada. Agora com interface web moderna em Flask!

## ✨ Funcionalidades

- 🤖 **Categorização Automática** - Classifica e-mails em 8 categorias inteligentes
- 🧠 **Análise de Sentimento** - Usa TextBlob para identificar e-mails positivos e negativos
- 🔍 **Detecção de Duplicatas** - Identifica e remove e-mails duplicados
- 📊 **Dashboard em Tempo Real** - Acompanhe o progresso com WebSocket
- 📱 **Interface Responsiva** - Design moderno que funciona em qualquer dispositivo
- 📋 **Logs Detalhados** - Histórico completo de todas as operações
- ⚡ **Processamento em Background** - Não trava a interface durante a execução

## 📁 Categorias Automáticas

- **Faturas** - Boletos, pagamentos, notas fiscais
- **Trabalho** - Projetos, relatórios, reuniões
- **Pessoal** - Convites, eventos, família
- **Marketing** - Promoções, newsletters, ofertas
- **Sistema** - Alertas, erros, notificações
- **Positivos** - E-mails com sentimento positivo
- **Problemas** - E-mails com sentimento negativo
- **Neutros** - Outros e-mails

## 🚀 Instalação Local

### Pré-requisitos

- Python 3.11+
- Conta Gmail com senha de aplicativo

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/mailnest.git
cd mailnest
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**

Windows:
```bash
venv\Scripts\activate
```

Linux/Mac:
```bash
source venv/bin/activate
```

4. **Instale as dependências**
```bash
pip install -r requirements.txt
```

5. **Execute a aplicação**
```bash
python app.py
```

6. **Acesse no navegador**
```
http://localhost:5000
```

## 🔐 Configuração do Gmail

1. Acesse [Configurações de Segurança do Google](https://myaccount.google.com/security)
2. Ative a **Verificação em duas etapas**
3. Acesse **Senhas de app**
4. Crie uma nova senha para "MailNest"
5. Use essa senha no campo "Senha de App"

## 🎨 Interface

A interface Flask conta com:

- **Sidebar** - Configurações e credenciais
- **Dashboard** - Métricas em tempo real
- **Tabs** - Execute, Logs e Ajuda
- **Progress Bar** - Acompanhamento visual
- **Live Logs** - Logs em tempo real via WebSocket

## 📦 Estrutura do Projeto

```
mailnest/
├── app.py                 # Aplicação Flask principal
├── templates/
│   └── index.html        # Template HTML
├── static/
│   ├── style.css         # Estilos CSS
│   └── script.js         # JavaScript + WebSocket
├── requirements.txt      # Dependências Python
├── Procfile             # Configuração Heroku
├── runtime.txt          # Versão do Python
└── README.md            # Este arquivo
```

## 🌐 Deploy

### Heroku

```bash
heroku create seu-app-mailnest
git push heroku main
```

### Render

1. Conecte seu repositório
2. Configure o comando: `python app.py`
3. Deploy automático

### Railway

1. Conecte seu repositório
2. Configure a porta 5000
3. Deploy automático

## 🔧 Tecnologias

- **Flask 3.0** - Framework web
- **Flask-SocketIO** - WebSocket para tempo real
- **TextBlob** - Análise de sentimento
- **IMAP** - Conexão com Gmail
- **JavaScript** - Interface interativa
- **CSS3** - Design responsivo

## ⚙️ Variáveis de Ambiente

Para deploy, configure:

```env
FLASK_SECRET_KEY=sua-chave-secreta
```

## 📝 Changelog

### v2.0.0 (2025-01-11)
- ✅ Migração completa de Streamlit para Flask
- ✅ WebSocket para comunicação em tempo real
- ✅ Interface responsiva moderna
- ✅ Dashboard com métricas
- ✅ Sistema de tabs
- ✅ Logs ao vivo

### v1.0.0 (2024)
- ✅ Versão inicial com Streamlit
- ✅ Organização automática
- ✅ Análise de sentimento
- ✅ Detecção de duplicatas

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Fazer fork do projeto
2. Criar uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abrir um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## ⚠️ Avisos Importantes

- Nunca compartilhe sua senha de aplicativo
- Faça backup antes da primeira execução
- O processo pode levar alguns minutos
- Verificação de duplicatas limitada a 1000 e-mails

## 📧 Suporte

Problemas ou dúvidas? Abra uma [issue](https://github.com/seu-usuario/mailnest/issues)

---

Feito com ❤️ por MailNest Team
