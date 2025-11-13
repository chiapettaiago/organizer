# 🚀 Guia Rápido - MailNest Flask

## ⚡ Início Rápido

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Executar a Aplicação

```bash
python app.py
```

### 3. Acessar no Navegador

```
http://localhost:5000
```

## 🎯 Como Usar

### Passo 1: Configure suas Credenciais

Na **sidebar esquerda**, preencha:
- **E-mail**: Seu e-mail do Gmail
- **Senha de App**: Senha de aplicativo gerada no Google

### Passo 2: Escolha a Operação

Na aba **Executar**, clique em:
- **📧 Organizar Agora** - Organiza todos os e-mails
- **🔍 Verificar Duplicatas** - Remove e-mails duplicados

### Passo 3: Acompanhe o Progresso

- Barra de progresso mostra o percentual em tempo real
- Logs aparecem automaticamente durante a execução
- Métricas no topo são atualizadas ao final

## 📊 Interface

### Dashboard (Topo)
- **E-mails Organizados** - Total processado
- **Duplicatas Removidas** - Quantidade de duplicatas
- **Categorias Criadas** - Número de categorias
- **Status** - Estado atual da operação

### Tabs
- **⚡ Executar** - Execute operações
- **📋 Logs** - Histórico completo
- **❓ Ajuda** - Documentação e ajuda

## 🔐 Senha de Aplicativo

### Como Gerar:

1. Acesse: https://myaccount.google.com/security
2. Clique em "Verificação em duas etapas"
3. Role até "Senhas de app"
4. Selecione "Outro (nome personalizado)"
5. Digite "MailNest"
6. Copie a senha gerada (16 caracteres)
7. Cole no campo "Senha de App"

## 🎨 Recursos

### Tempo Real
- ✅ WebSocket para comunicação instantânea
- ✅ Logs aparecem conforme a execução
- ✅ Barra de progresso atualiza automaticamente

### Interface Responsiva
- ✅ Funciona em desktop, tablet e mobile
- ✅ Design moderno com gradientes
- ✅ Sidebar recolhível em telas pequenas

### Categorias Inteligentes
- 📁 **Faturas** - Boletos, pagamentos
- 💼 **Trabalho** - Projetos, reuniões
- 👥 **Pessoal** - Família, amigos
- 📢 **Marketing** - Promoções, ofertas
- ⚙️ **Sistema** - Alertas, notificações
- 😊 **Positivos** - Sentimento positivo
- ⚠️ **Problemas** - Sentimento negativo
- 📮 **Neutros** - Outros

## ⚙️ Configurações Opcionais

### Remover da INBOX
- ✅ Marcado: Move e remove da INBOX
- ❌ Desmarcado: Apenas copia para categoria

### Limite de E-mails
- Padrão: 2000 e-mails mais recentes
- Duplicatas: 1000 e-mails mais recentes

## 🐛 Solução de Problemas

### Erro de Autenticação
- Verifique se a senha de app está correta
- Confirme que a verificação em 2 etapas está ativa

### Servidor não Inicia
```bash
# Reinstale as dependências
pip install --upgrade -r requirements.txt

# Execute novamente
python app.py
```

### Porta 5000 em Uso
```bash
# Use outra porta
PORT=8000 python app.py
```

### WebSocket não Conecta
- Verifique se o servidor está rodando
- Recarregue a página (F5)
- Limpe o cache do navegador

## 🔄 Diferenças do Streamlit

### Melhorias:
- ✅ Interface mais rápida
- ✅ WebSocket para tempo real
- ✅ Melhor controle de estado
- ✅ Logs mais detalhados
- ✅ Design mais profissional

### Mantido:
- ✅ Todas as funcionalidades
- ✅ Análise de sentimento
- ✅ Detecção de duplicatas
- ✅ Categorização automática
- ✅ Progresso em tempo real

## 📱 Atalhos de Teclado

- **Ctrl + R** - Recarregar página
- **Tab** - Navegar entre campos
- **Enter** - Confirmar operação

## 🌐 URLs Úteis

- **Local**: http://localhost:5000
- **Logs API**: http://localhost:5000/api/logs
- **GitHub**: Seu repositório

## 💡 Dicas

1. **Primeira Execução**: Faça backup do Gmail
2. **Grande Volume**: Seja paciente, pode levar minutos
3. **Teste Pequeno**: Comece com poucos e-mails
4. **Monitore**: Acompanhe os logs em tempo real
5. **Backup**: Sempre tenha backup antes de organizar

## 📞 Suporte

- **Issues**: Abra uma issue no GitHub
- **Documentação**: Leia o README.md completo
- **Logs**: Consulte a aba de logs para detalhes

---

**MailNest v2.0** - Organização inteligente de e-mails com Flask
