# 🔐 Sistema de Credenciais Gmail

## Visão Geral

O sistema agora permite que os usuários **salvem suas credenciais do Gmail** (e-mail e senha de aplicativo) no banco de dados SQLite para reutilização automática.

## Funcionalidades

### 1. **Salvar Credenciais**
- Usuário digita e-mail e senha do Gmail
- Clica no botão "💾 Salvar Credenciais"
- Credenciais são criptografadas (Base64) e salvas no banco
- Mensagem de confirmação é exibida

### 2. **Carregar Credenciais Automáticas**
- Ao fazer login, o sistema carrega automaticamente as credenciais salvas
- Campo de e-mail é preenchido automaticamente
- Campo de senha mostra placeholder "••••••••••••••••" indicando que existe senha salva
- Usuário não precisa digitar novamente

### 3. **Remover Credenciais**
- Botão "🗑️ Remover" aparece quando há credenciais salvas
- Remove permanentemente as credenciais do banco
- Limpa os campos da interface

### 4. **Uso Automático**
- Ao clicar em "Organizar Agora" ou "Verificar Duplicatas":
  - Se os campos estão vazios, usa as credenciais salvas automaticamente
  - Se os campos estão preenchidos, usa os valores digitados
  - Não é necessário salvar as credenciais para usá-las uma vez

## Estrutura do Banco de Dados

### Tabela `users`
```sql
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    gmail_email TEXT,        -- NOVO: E-mail do Gmail
    gmail_password TEXT      -- NOVO: Senha criptografada
);
```

## API Endpoints

### GET `/api/gmail/credenciais`
Retorna as credenciais salvas do usuário (sem expor a senha).

**Resposta:**
```json
{
    "success": true,
    "gmail_email": "usuario@gmail.com",
    "has_password": true
}
```

### POST `/api/gmail/credenciais`
Salva novas credenciais do Gmail.

**Body:**
```json
{
    "gmail_email": "usuario@gmail.com",
    "gmail_password": "senha_de_aplicativo"
}
```

**Resposta:**
```json
{
    "success": true,
    "message": "Credenciais salvas com sucesso"
}
```

### DELETE `/api/gmail/credenciais`
Remove as credenciais salvas.

**Resposta:**
```json
{
    "success": true,
    "message": "Credenciais removidas com sucesso"
}
```

## Funções Python

### `salvar_credenciais_gmail(user_id, gmail_email, gmail_password)`
Salva as credenciais do Gmail com criptografia Base64.

### `obter_credenciais_gmail(user_id)`
Retorna as credenciais descriptografadas.

### `remover_credenciais_gmail(user_id)`
Remove as credenciais do banco de dados.

## Segurança

### ⚠️ Implementação Atual (Base64)
- **Criptografia:** Base64 (reversível, não é segura)
- **Objetivo:** Evitar visualização casual em texto puro
- **Limitação:** Base64 é facilmente decodificável

### 🔒 Recomendações para Produção

1. **Use Cryptography (Fernet)**
```python
from cryptography.fernet import Fernet

# Gerar chave (salvar em variável de ambiente)
key = Fernet.generate_key()
cipher = Fernet(key)

# Criptografar
encrypted = cipher.encrypt(password.encode())

# Descriptografar
decrypted = cipher.decrypt(encrypted).decode()
```

2. **Use Keyring do Sistema**
```python
import keyring

# Salvar
keyring.set_password("mailnest", user_id, gmail_password)

# Obter
password = keyring.get_password("mailnest", user_id)
```

3. **Use Variáveis de Ambiente**
- Não salve a chave de criptografia no código
- Use `.env` com `python-dotenv`
- Configure `SECRET_KEY` no ambiente de produção

4. **Implemente Expiração**
- Adicionar coluna `credentials_expires_at`
- Forçar re-autenticação periódica
- Limpar credenciais antigas automaticamente

## Logs de Atividade

O sistema registra:
- ✅ `gmail_credentials_saved` - Quando credenciais são salvas
- ✅ `gmail_credentials_removed` - Quando credenciais são removidas
- ✅ `email_organization_started` - Quando organização é iniciada (registra qual conta Gmail)
- ✅ `duplicate_check_started` - Quando verificação de duplicatas é iniciada

## Migração de Banco Existente

Se você já tem um banco de dados `organizer.db`, execute:

```bash
python migrate_db.py
```

Isso adicionará as colunas `gmail_email` e `gmail_password` à tabela `users`.

## Interface do Usuário

### Antes de Salvar
```
🔐 Credenciais do Gmail
E-mail: [         ]
Senha:  [         ]
[💾 Salvar Credenciais]
```

### Depois de Salvar
```
🔐 Credenciais do Gmail
E-mail: [usuario@gmail.com]
Senha:  [••••••••••••••••]
[💾 Salvar Credenciais] [🗑️ Remover]
```

## Fluxo de Uso

1. **Primeira Vez:**
   - Usuário faz login no MailNest
   - Digita e-mail e senha do Gmail
   - Clica em "Salvar Credenciais"
   - Credenciais são salvas

2. **Próximos Usos:**
   - Usuário faz login no MailNest
   - Campos são preenchidos automaticamente
   - Clica diretamente em "Organizar Agora"
   - Sistema usa credenciais salvas

3. **Atualizar Credenciais:**
   - Usuário altera os campos
   - Clica em "Salvar Credenciais" novamente
   - Credenciais são atualizadas

4. **Remover Credenciais:**
   - Usuário clica em "Remover"
   - Confirma a ação
   - Credenciais são removidas do banco

## Compatibilidade

- ✅ Funciona com contas existentes
- ✅ Não quebra fluxo atual (campos podem ser preenchidos manualmente)
- ✅ Migração automática no `init_database()`
- ✅ Totalmente retrocompatível

## Testes

Execute o script de teste:
```bash
python test_db.py
```

Verifique se:
- Tabela `users` tem colunas `gmail_email` e `gmail_password`
- Credenciais são salvas corretamente
- Credenciais são recuperadas descriptografadas
- Remoção funciona corretamente
