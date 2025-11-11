# Gmail Organizer Pro 📬

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**Organize seus e-mails do Gmail automaticamente com Inteligência Artificial**

[Demo](#) | [Documentação](#como-usar) | [Deploy](#deploy-no-heroku)

</div>

---

## 🚀 Características

- ✅ **Classificação Inteligente** - IA classifica e-mails em 8 categorias
- ✅ **Remoção de Duplicatas** - Detecta e remove e-mails duplicados
- ✅ **Agendamento Automático** - Execute em intervalos personalizados
- ✅ **Interface Profissional** - Dashboard moderno e responsivo
- ✅ **Logs Detalhados** - Acompanhe cada etapa do processo
- ✅ **Métricas em Tempo Real** - Visualize estatísticas instantaneamente
- ✅ **Seguro** - Conexão SSL/TLS com Gmail

## 📋 Categorias

Os e-mails são organizados automaticamente em:

| Categoria | Ícone | Descrição |
|-----------|-------|-----------|
| Faturas | 💰 | Boletos, pagamentos, notas fiscais |
| Trabalho | 💼 | Projetos, relatórios, documentos |
| Pessoal | 👤 | Amigos, família, eventos |
| Marketing | 📢 | Promoções, newsletters, ofertas |
| Sistema | ⚙️ | Alertas, erros, notificações |
| Problemas | ⚠️ | E-mails com sentimento negativo |
| Positivos | 😊 | E-mails com sentimento positivo |
| Neutros | 📄 | Outros e-mails |

## 🎯 Como Usar

### 1️⃣ Configurar Credenciais

1. Acesse [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Gere uma senha de aplicativo para "E-mail"
3. Copie a senha gerada (16 caracteres)

### 2️⃣ Executar Localmente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/gmail-organizer-pro.git
cd gmail-organizer-pro

# Instale as dependências
pip install -r requirements.txt

# Execute o aplicativo
streamlit run organizador.py
```

### 3️⃣ Usar a Aplicação

1. Insira suas credenciais na barra lateral
2. Configure as opções de organização
3. Clique em "Organizar Agora"
4. Acompanhe o progresso em tempo real

## 🌐 Deploy no Heroku

### Opção 1: Via CLI

```bash
# Login no Heroku
heroku login

# Crie um novo app
heroku create gmail-organizer-pro

# Configure o buildpack
heroku buildpacks:set heroku/python

# Faça o deploy
git push heroku main

# Abra o app
heroku open
```

### Opção 2: Via GitHub

1. Fork este repositório
2. Acesse [Heroku Dashboard](https://dashboard.heroku.com)
3. Clique em "New" → "Create new app"
4. Conecte com seu repositório GitHub
5. Clique em "Deploy Branch"

### Opção 3: Via Botão Deploy

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 📦 Estrutura do Projeto

```
gmail-organizer-pro/
├── organizador.py          # Aplicação principal
├── requirements.txt        # Dependências Python
├── Procfile               # Configuração Heroku
├── setup.sh               # Script de setup
├── runtime.txt            # Versão do Python
└── README.md              # Este arquivo
```

## ⚙️ Configuração

### Variáveis de Ambiente (Opcional)

```bash
# Para maior segurança, use variáveis de ambiente
export GMAIL_USER="seu-email@gmail.com"
export GMAIL_PASSWORD="sua-senha-de-aplicativo"
```

### Personalizar Categorias

Edite a função `classificar_email()` em `organizador.py`:

```python
categorias = {
    "SuaCategoria": ["palavra1", "palavra2", "palavra3"],
    # Adicione mais categorias...
}
```

## 🔒 Segurança

- ✅ Conexão SSL/TLS com Gmail (IMAP)
- ✅ Não armazena credenciais em arquivos
- ✅ Senha de aplicativo (não senha principal)
- ✅ Código open-source auditável
- ✅ Processamento local/privado

## 🛠️ Tecnologias

- **Python 3.11** - Linguagem principal
- **Streamlit** - Framework web
- **TextBlob** - Análise de sentimento
- **IMAP** - Protocolo de e-mail
- **Heroku** - Plataforma de deploy

## 📊 Requisitos do Sistema

- Python 3.11+
- 512 MB RAM (mínimo)
- Conexão com internet

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se livre para:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 💬 Suporte

- 📧 E-mail: suporte@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/seu-usuario/gmail-organizer-pro/issues)
- 💬 Discussões: [GitHub Discussions](https://github.com/seu-usuario/gmail-organizer-pro/discussions)

## 🙏 Agradecimentos

- Gmail API Documentation
- Streamlit Community
- TextBlob Contributors

---

<div align="center">

**Desenvolvido com ❤️ por [Seu Nome]**

⭐ Se este projeto te ajudou, deixe uma estrela!

</div>
