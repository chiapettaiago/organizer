# 📊 Sistema Completo de Persistência com SQLite

## Visão Geral

O sistema agora utiliza **SQLite** para persistência de **TODOS** os dados da aplicação, incluindo:
- ✅ **Usuários** - Credenciais, perfis e informações
- ✅ **Códigos de Convite** - Geração, uso e revogação
- ✅ **Logs de Atividade** - Histórico completo de ações

Todos os dados são mantidos permanentemente no banco de dados `organizer.db`.

## 🗄️ Estrutura do Banco de Dados

### Tabela: `users`

Armazena todos os usuários do sistema.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `user_id` | TEXT PRIMARY KEY | ID único do usuário (geralmente o email) |
| `password_hash` | TEXT NOT NULL | Hash SHA256 da senha |
| `name` | TEXT NOT NULL | Nome completo do usuário |
| `email` | TEXT | Endereço de e-mail |
| `is_admin` | INTEGER | 1 para admin, 0 para usuário normal |
| `created_at` | TIMESTAMP | Data/hora de criação da conta |
| `last_login` | TIMESTAMP | Data/hora do último login |

**Usuário padrão:**
- user_id: `admin`
- password: `admin123`
- is_admin: `1`

### Tabela: `invite_codes`

Gerencia códigos de convite para novos usuários.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `code` | TEXT PRIMARY KEY | Código único (12 caracteres) |
| `created_by` | TEXT NOT NULL | user_id de quem criou o código |
| `created_at` | TIMESTAMP | Data/hora de criação |
| `used` | INTEGER | 0 = disponível, 1 = usado |
| `used_by` | TEXT | user_id de quem usou (NULL se não usado) |
| `used_at` | TIMESTAMP | Data/hora de uso (NULL se não usado) |

**Foreign Key:** `created_by` → `users(user_id)`

### Tabela: `user_activities`

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id` | INTEGER PRIMARY KEY | ID único auto-incrementado |
| `user_id` | TEXT NOT NULL | ID do usuário que realizou a ação |
| `timestamp` | TEXT NOT NULL | Data/hora da ação (ISO 8601) |
| `action` | TEXT NOT NULL | Tipo de ação realizada |
| `details` | TEXT | Detalhes em formato JSON |
| `ip_address` | TEXT | Endereço IP do usuário |
| `user_agent` | TEXT | Navegador/sistema do usuário |
| `created_at` | TIMESTAMP | Timestamp de criação do registro |

### Índices

- `idx_user_id`: Índice em `user_id` para buscas rápidas por usuário
- `idx_timestamp`: Índice em `timestamp` para ordenação temporal
- `idx_action`: Índice em `action` para filtros por tipo de ação

## 📝 Ações Rastreadas

### Autenticação
- `login` - Login bem-sucedido
- `login_failed` - Tentativa de login falhada
- `logout` - Logout do usuário
- `invite_validated` - Validação de código de convite bem-sucedida
- `invite_failed` - Falha na validação de código de convite
- `account_created` - Nova conta criada via convite
- `first_login` - Primeiro login após registro

### Administração
- `invite_code_generated` - Geração de código de convite
- `invite_code_revoked` - Revogação de código de convite
- `activities_cleanup` - Limpeza de atividades antigas

### Operações de E-mail
- `email_organization_started` - Início da organização de e-mails
- `email_organization_completed` - Organização concluída com sucesso
- `email_organization_failed` - Falha na organização
- `duplicate_check_started` - Início da verificação de duplicatas
- `duplicate_check_completed` - Verificação concluída
- `duplicate_check_failed` - Falha na verificação

## 🔧 Funções Python

### Gerenciamento de Usuários

#### `criar_usuario(user_id, password, name, email=None, is_admin=False)`
Cria um novo usuário no banco de dados.

```python
criar_usuario(
    user_id='joao@email.com',
    password='senha123',
    name='João Silva',
    email='joao@email.com',
    is_admin=False
)
```

#### `obter_usuario(user_id)`
Obtém dados de um usuário do banco.

```python
usuario = obter_usuario('admin')
# Retorna: {'user_id', 'password', 'nome', 'email', 'is_admin', 'criado_em', 'last_login'}
```

#### `obter_todos_usuarios()`
Retorna todos os usuários do sistema.

```python
usuarios = obter_todos_usuarios()
# Retorna dicionário: {user_id: {nome, email, is_admin, criado_em, last_login}}
```

#### `validar_credenciais(user_id, password)`
Valida credenciais de login.

```python
if validar_credenciais('admin', 'admin123'):
    print('Login OK')
```

#### `atualizar_ultimo_login(user_id)`
Atualiza timestamp do último login.

```python
atualizar_ultimo_login('admin')
```

### Gerenciamento de Códigos de Convite

#### `gerar_codigo_convite(created_by)`
Gera um novo código de convite.

```python
codigo = gerar_codigo_convite('admin')
# Retorna: 'ABC123DEF456'
```

#### `obter_codigo_convite(code)`
Obtém informações de um código.

```python
convite = obter_codigo_convite('ABC123DEF456')
# Retorna: {'code', 'created_by', 'created_at', 'used', 'used_by', 'used_at'}
```

#### `obter_todos_convites()`
Retorna todos os códigos de convite.

```python
convites = obter_todos_convites()
```

#### `validar_codigo_convite(code)`
Valida se código existe e está disponível.

```python
if validar_codigo_convite('ABC123DEF456'):
    print('Código válido')
```

#### `marcar_convite_usado(code, used_by)`
Marca um código como usado.

```python
marcar_convite_usado('ABC123DEF456', 'joao@email.com')
```

#### `revogar_codigo_convite(code)`
Remove um código do banco.

```python
revogar_codigo_convite('ABC123DEF456')
```

### Logs de Atividade

#### `registrar_atividade(user_id, action, details=None, ip_address=None)`
Registra uma nova atividade no banco de dados.

```python
registrar_atividade(
    user_id='admin',
    action='login',
    details={'method': 'credentials'},
    ip_address='192.168.1.1'
)
```

#### `obter_historico_usuario(user_id, limit=100)`
Retorna as últimas N atividades de um usuário.

```python
historico = obter_historico_usuario('admin', limit=50)
```

#### `obter_total_atividades_usuario(user_id)`
Retorna o total de atividades registradas de um usuário.

```python
total = obter_total_atividades_usuario('admin')
```

#### `obter_todas_atividades(limit=1000)`
Retorna todas as atividades de todos os usuários.

```python
todas = obter_todas_atividades(limit=500)
```

#### `limpar_atividades_antigas(dias=90)`
Remove atividades mais antigas que X dias.

```python
deletados = limpar_atividades_antigas(dias=90)
print(f"Removidos {deletados} registros")
```

#### `exportar_atividades_csv(user_id=None)`
Exporta atividades para formato CSV.

```python
# Exportar de um usuário específico
csv_data = exportar_atividades_csv('admin')

# Exportar todas
csv_data = exportar_atividades_csv()
```

## 🌐 Endpoints da API

### GET `/api/admin/usuarios`
Lista todos os usuários do sistema.

**Requer:** Autenticação de administrador

**Resposta:**
```json
{
  "success": true,
  "usuarios": [
    {
      "id": "admin",
      "nome": "Administrador",
      "email": "admin@example.com",
      "is_admin": true,
      "criado_em": "2025-01-01T00:00:00"
    }
  ],
  "total": 1
}
```

### GET `/api/admin/atividades/<user_id>?limit=100`
Obtém histórico de atividades de um usuário.

**Parâmetros:**
- `limit` (opcional): Número máximo de registros (padrão: 100)

**Resposta:**
```json
{
  "success": true,
  "user_id": "admin",
  "nome": "Administrador",
  "email": "admin@example.com",
  "total_atividades": 150,
  "atividades": [...]
}
```

### GET `/api/admin/atividades/exportar/<user_id>`
Exporta atividades de um usuário em CSV.

**Requer:** Autenticação de administrador

**Resposta:** Arquivo CSV para download

### GET `/api/admin/atividades/exportar-todas`
Exporta todas as atividades do sistema em CSV.

**Requer:** Autenticação de administrador

**Resposta:** Arquivo CSV para download

### POST `/api/admin/atividades/limpar`
Remove atividades antigas.

**Body:**
```json
{
  "dias": 90
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "150 registros removidos",
  "deletados": 150
}
```

### GET `/api/admin/estatisticas`
Retorna estatísticas gerais do sistema.

**Resposta:**
```json
{
  "success": true,
  "total_atividades": 1500,
  "total_usuarios": 10,
  "atividades_7_dias": 250,
  "atividades_por_usuario": [...],
  "atividades_por_tipo": [...]
}
```

## 💻 Interface Web

### Página de Atividades (`/admin/atividades`)

**Funcionalidades:**

1. **Dashboard de Estatísticas**
   - Total de atividades no sistema
   - Total de usuários cadastrados
   - Atividades nos últimos 7 dias

2. **Lista de Usuários**
   - Cards clicáveis com nome e e-mail
   - Badge para administradores
   - Indicador visual de seleção

3. **Visualização de Atividades**
   - Histórico completo de ações do usuário
   - Badges coloridos por tipo de ação
   - Detalhes formatados (Gmail, contadores, erros)
   - Informações de IP e navegador

4. **Exportação de Dados**
   - Botão para exportar atividades do usuário selecionado
   - Botão para exportar todas as atividades do sistema
   - Formato CSV com cabeçalhos

## 🔐 Segurança

- Todas as rotas de administração requerem autenticação
- Decorador `@admin_required` protege endpoints sensíveis
- Logs isolados por usuário (sem acesso cruzado)
- IP e User-Agent registrados para auditoria
- Banco de dados SQLite com permissões apropriadas

## 📁 Arquivos do Sistema

- `organizer.db` - Banco de dados SQLite único com todas as tabelas (ignorado pelo Git)
- `.gitignore` - Configurado para não commitar arquivos `.db`
- `app.py` - Todas as funções de persistência e rotas
- `templates/admin_atividades.html` - Interface de visualização de atividades
- `templates/admin_convites.html` - Interface de gerenciamento de convites

## 🚀 Boas Práticas

1. **Backup Regular**
   ```bash
   # Backup do banco completo
   cp organizer.db organizer_backup_$(date +%Y%m%d).db
   
   # Backup com SQLite
   sqlite3 organizer.db ".backup organizer_backup.db"
   ```

2. **Limpeza Periódica**
   - Execute a limpeza de logs antigos mensalmente
   - Mantenha apenas os últimos 90 dias (ou conforme necessário)

3. **Monitoramento**
   - Verifique o tamanho do banco de dados regularmente
   - Use as estatísticas para identificar padrões de uso

4. **Exportação Preventiva**
   - Exporte dados importantes antes de limpezas
   - Mantenha backups em formato CSV

## ⚠️ Notas Importantes

- O banco de dados é criado automaticamente na primeira execução
- **Não commite** o arquivo `organizer.db` para o Git
- Usuário admin padrão: `admin` / `admin123`
- Altere a senha do admin após primeiro login em produção
- Em produção, considere usar PostgreSQL ou MySQL para maior performance
- Para ambientes com múltiplos workers, use um banco de dados externo

## 🔄 Migração de Dados Antigos

Se você tem dados em memória (dicionários USERS/INVITE_CODES) de versões anteriores, eles serão substituídos pelo banco SQLite. Para migrar:

1. **Backup dos dados antigos** (se existirem)
2. **Atualize o código** (já feito)
3. **Inicie a aplicação** (banco será criado automaticamente)
4. **Use as funções de criação** para importar dados antigos

Exemplo de script de migração:

```python
# Exemplo: migrar usuários antigos
OLD_USERS = {
    'user1': {'password': 'hash...', 'name': 'User 1', ...}
}

for user_id, data in OLD_USERS.items():
    criar_usuario(
        user_id=user_id,
        password='senha_temporaria',  # Usuário precisa resetar
        name=data['name'],
        email=data.get('email'),
        is_admin=data.get('is_admin', False)
    )
```

## 📊 Exemplo de Análise

```python
import sqlite3
import pandas as pd

# Conectar ao banco
conn = sqlite3.connect('organizer.db')

# Análise de usuários mais ativos
df_users = pd.read_sql_query("""
    SELECT 
        u.name,
        COUNT(a.id) as total_atividades,
        MAX(a.timestamp) as ultima_atividade
    FROM users u
    LEFT JOIN user_activities a ON u.user_id = a.user_id
    GROUP BY u.user_id
    ORDER BY total_atividades DESC
""", conn)

print(df_users)

# Análise de convites
df_invites = pd.read_sql_query("""
    SELECT 
        created_by,
        COUNT(*) as total_gerados,
        SUM(used) as total_usados
    FROM invite_codes
    GROUP BY created_by
""", conn)

print(df_invites)

conn.close()
```

## 🎯 Próximos Passos Sugeridos

1. ✅ **Migração completa para SQLite** - CONCLUÍDO
2. Adicionar filtros avançados na interface (por data, tipo de ação)
3. Gráficos de visualização de dados (Chart.js)
4. Alertas automáticos para atividades suspeitas
5. Exportação em formato JSON além de CSV
6. Paginação para grandes volumes de dados
7. API de consulta com filtros complexos
8. Implementar reset de senha via e-mail
9. Sistema de roles e permissões mais granular
10. Auditoria de mudanças em usuários

## 🔐 Segurança Adicional

### Recomendações de Produção:

1. **Senhas Fortes**
   ```python
   # Adicione validação de complexidade de senha
   import re
   
   def validar_senha_forte(senha):
       if len(senha) < 8:
           return False
       if not re.search(r'[A-Z]', senha):
           return False
       if not re.search(r'[0-9]', senha):
           return False
       return True
   ```

2. **Limite de Tentativas de Login**
   ```python
   # Implementar rate limiting
   from functools import wraps
   from time import time
   
   login_attempts = {}
   
   def rate_limit(max_attempts=5, window=300):
       # Bloquear após 5 tentativas em 5 minutos
       pass
   ```

3. **Tokens de Sessão**
   - Considere usar JWT tokens
   - Implemente refresh tokens
   - Rotação automática de sessões

4. **Criptografia**
   - Use bcrypt em vez de SHA256 para senhas
   - Criptografe dados sensíveis no banco
   - Use HTTPS em produção

5. **Backup Automatizado**
   ```bash
   # Cron job para backup diário
   0 2 * * * /usr/bin/sqlite3 /path/to/organizer.db ".backup /path/to/backups/organizer_$(date +\%Y\%m\%d).db"
   ```

## 📈 Performance e Otimização

### Índices Criados

- `idx_user_id` - Atividades por usuário
- `idx_timestamp` - Ordenação temporal
- `idx_action` - Filtros por tipo
- `idx_invite_created_by` - Convites por criador
- `idx_invite_used` - Convites disponíveis/usados

### Dicas de Performance

1. **Vacuum periódico**
   ```sql
   VACUUM;
   ```

2. **Analyze para estatísticas**
   ```sql
   ANALYZE;
   ```

3. **Limitar queries**
   - Sempre use LIMIT em queries grandes
   - Implemente paginação

4. **Connection pooling**
   - Em produção, use connection pooling
   - Considere SQLAlchemy para ORM
