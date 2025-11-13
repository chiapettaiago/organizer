# 🚀 Deploy no Heroku com Migração Automática

## Configuração Implementada

### 1. **Procfile**
O `Procfile` agora contém duas fases:

```procfile
release: python migrate_db.py
web: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app
```

- **`release`**: Executado **antes** do deploy, ideal para migrações
- **`web`**: Executado para iniciar o servidor web

### 2. **migrate_db.py**
Script de migração que:
- ✅ Adiciona colunas `gmail_email` e `gmail_password` se não existirem
- ✅ Cria tabela `user_statistics` se não existir
- ✅ Inicializa estatísticas para usuários existentes
- ✅ Trata graciosamente o caso de banco inexistente

### 3. **release.sh** (alternativa)
Script bash para release phase (opcional).

## Como Funciona no Heroku

### Primeiro Deploy (Banco Novo)
```
1. Heroku recebe código
2. Instala dependências (requirements.txt)
3. Executa: release: python migrate_db.py
   → Banco não existe, migração pula
4. Inicia app: web: gunicorn ...
   → app.py cria banco via init_database()
   → Tabelas criadas com estrutura atualizada
5. ✅ App rodando com banco atualizado
```

### Deploys Subsequentes (Banco Existente)
```
1. Heroku recebe código atualizado
2. Instala dependências
3. Executa: release: python migrate_db.py
   → Banco existe
   → Verifica colunas/tabelas faltantes
   → Adiciona apenas o que não existe
   → ✅ Migração concluída
4. Inicia app: web: gunicorn ...
5. ✅ App rodando com banco migrado
```

## Comandos de Deploy

### Deploy Normal
```bash
git add .
git commit -m "feat: adiciona migrações automáticas"
git push heroku main
```

### Verificar Logs da Migração
```bash
heroku logs --tail
```

Procure por:
```
🔧 MIGRAÇÃO DO BANCO DE DADOS
✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!
```

### Executar Migração Manualmente (se necessário)
```bash
heroku run python migrate_db.py
```

### Verificar Banco no Heroku
```bash
# Acessar console Python no Heroku
heroku run python

# Depois executar:
>>> import sqlite3
>>> conn = sqlite3.connect('organizer.db')
>>> cursor = conn.cursor()
>>> cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
>>> print(cursor.fetchall())
>>> cursor.execute("SELECT * FROM user_statistics")
>>> print(cursor.fetchall())
```

## Persistência do Banco de Dados no Heroku

⚠️ **IMPORTANTE**: O Heroku usa **sistema de arquivos efêmero**!

### Problema
- Heroku reinicia dynos periodicamente (a cada 24h ou após deploy)
- Arquivos locais (incluindo `organizer.db`) são **perdidos**

### Soluções

#### Opção 1: Heroku Postgres (Recomendado para Produção)
```bash
# Adicionar addon Postgres
heroku addons:create heroku-postgresql:mini

# Modificar app.py para usar PostgreSQL
# Usar SQLAlchemy ou psycopg2
```

#### Opção 2: Amazon S3 para Persistência
```bash
# Salvar/carregar organizer.db do S3 antes/depois de cada operação
```

#### Opção 3: Heroku Redis (Para Sessões)
```bash
# Usar Redis para dados temporários
heroku addons:create heroku-redis:mini
```

#### Opção 4: Renderização Local + Deploy (Desenvolvimento)
```bash
# Aceitar que dados serão perdidos no Heroku
# Usar apenas para testes
```

## Migrando para PostgreSQL (Produção)

### 1. Instalar Dependências
```bash
pip install psycopg2-binary sqlalchemy
pip freeze > requirements.txt
```

### 2. Modificar app.py
```python
import os
from sqlalchemy import create_engine

# Detectar ambiente
if os.environ.get('DATABASE_URL'):
    # Heroku PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    engine = create_engine(DATABASE_URL)
else:
    # Local SQLite
    engine = create_engine('sqlite:///organizer.db')
```

### 3. Adicionar Postgres no Heroku
```bash
heroku addons:create heroku-postgresql:mini
```

### 4. Deploy
```bash
git add .
git commit -m "feat: adiciona suporte a PostgreSQL"
git push heroku main
```

## Variáveis de Ambiente no Heroku

### Configurar Secrets
```bash
# Chave secreta para sessões
heroku config:set SECRET_KEY="sua-chave-super-secreta-aqui"

# Modo de produção
heroku config:set FLASK_ENV=production

# Verificar configurações
heroku config
```

### Usar no app.py
```python
import os

app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-insegura')
```

## Checklist de Deploy

- [ ] `Procfile` contém linha `release:`
- [ ] `migrate_db.py` está no repositório
- [ ] `requirements.txt` está atualizado
- [ ] Variável `SECRET_KEY` configurada no Heroku
- [ ] Logs verificados após deploy
- [ ] Migração executada com sucesso
- [ ] App acessível via URL do Heroku
- [ ] Teste de login funcionando
- [ ] Estatísticas sendo salvas (se usar Postgres)

## Troubleshooting

### Erro: "ModuleNotFoundError"
```bash
# Atualizar requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "fix: atualiza dependências"
git push heroku main
```

### Erro: "Application Error"
```bash
# Ver logs detalhados
heroku logs --tail

# Reiniciar dyno
heroku restart
```

### Migração não executou
```bash
# Executar manualmente
heroku run python migrate_db.py

# Ver saída
heroku logs --source app
```

### Banco perdeu dados após reinício
```bash
# Confirmar: Heroku usa FS efêmero
# Solução: Migrar para PostgreSQL ou S3
```

## Estrutura de Arquivos

```
organizer/
├── app.py                           # Aplicação principal
├── migrate_db.py                    # Script de migração ⭐
├── Procfile                         # Config Heroku ⭐
├── release.sh                       # Release script (opcional)
├── requirements.txt                 # Dependências Python
├── runtime.txt                      # Versão Python (opcional)
├── organizer.db                     # Banco SQLite (local)
├── templates/                       # Templates HTML
├── static/                          # CSS/JS/Assets
└── *.md                            # Documentação
```

## Monitoramento

### Ver Logs em Tempo Real
```bash
heroku logs --tail
```

### Ver Apenas Release Phase
```bash
heroku logs --source app --tail | grep -i "migra"
```

### Executar Comandos Remotos
```bash
heroku run bash
# ou
heroku run python
```

## Próximos Passos

1. **Teste Local Completo**
   ```bash
   python app.py
   # Testar todas as funcionalidades
   ```

2. **Commit e Push**
   ```bash
   git add Procfile migrate_db.py
   git commit -m "feat: adiciona migração automática no Heroku"
   git push heroku main
   ```

3. **Verificar Deploy**
   ```bash
   heroku logs --tail
   # Procurar por mensagens de migração
   ```

4. **Testar App**
   ```bash
   heroku open
   # Fazer login e testar funcionalidades
   ```

5. **Considerar PostgreSQL**
   - Para produção real, migre para Postgres
   - Dados persistirão entre restarts
   - Melhor performance e escalabilidade

---

**Referências:**
- [Heroku Release Phase](https://devcenter.heroku.com/articles/release-phase)
- [Heroku SQLite Limitations](https://devcenter.heroku.com/articles/sqlite3)
- [Heroku PostgreSQL](https://devcenter.heroku.com/articles/heroku-postgresql)
