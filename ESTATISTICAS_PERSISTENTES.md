# 📊 Sistema de Estatísticas Persistentes

## Visão Geral

O sistema agora salva **todas as métricas do usuário** no banco de dados SQLite, permitindo que as estatísticas sejam mantidas **entre sessões**, mesmo após logout.

## Funcionalidades

### 1. **Persistência Automática**
- ✅ E-mails Organizados
- ✅ Duplicatas Removidas  
- ✅ Categorias Criadas
- ✅ Última Atualização

### 2. **Sincronização em Tempo Real**
- Estatísticas são atualizadas **automaticamente** após cada operação
- Dados são **incrementados** (não substituídos)
- Interface atualiza via WebSocket

### 3. **Carregamento Automático**
- Ao fazer login, estatísticas são carregadas do banco
- Valores são exibidos imediatamente na tela
- Sincronização transparente para o usuário

## Estrutura do Banco de Dados

### Tabela `user_statistics`

```sql
CREATE TABLE user_statistics (
    user_id TEXT PRIMARY KEY,
    emails_organizados INTEGER DEFAULT 0,
    duplicatas_removidas INTEGER DEFAULT 0,
    categorias_criadas INTEGER DEFAULT 0,
    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

## API Endpoints

### GET `/api/estatisticas`
Retorna as estatísticas salvas do usuário.

**Resposta:**
```json
{
    "success": true,
    "estatisticas": {
        "emails_organizados": 1234,
        "duplicatas_removidas": 56,
        "categorias_criadas": 8,
        "ultima_atualizacao": "2025-11-13T10:30:45"
    }
}
```

### POST `/api/estatisticas/resetar`
Reseta todas as estatísticas do usuário para zero.

**Resposta:**
```json
{
    "success": true,
    "message": "Estatísticas resetadas com sucesso"
}
```

## Funções Python

### `obter_estatisticas_usuario(user_id)`
Retorna as estatísticas do usuário. Se não existir, cria registro zerado.

```python
stats = obter_estatisticas_usuario('admin')
# Retorna: {'emails_organizados': 100, 'duplicatas_removidas': 5, ...}
```

### `criar_estatisticas_usuario(user_id)`
Cria registro de estatísticas zerado para novo usuário.

```python
criar_estatisticas_usuario('novo_usuario')
# Cria: {emails: 0, duplicatas: 0, categorias: 0}
```

### `atualizar_estatisticas_usuario(user_id, emails, duplicatas, categorias, incrementar=True)`
Atualiza as estatísticas do usuário.

**Modo Incremental (padrão):**
```python
# Adiciona +50 emails, +3 duplicatas, máximo 5 categorias
atualizar_estatisticas_usuario('admin', 
    emails_organizados=50,
    duplicatas_removidas=3,
    categorias_criadas=5,
    incrementar=True
)
```

**Modo Absoluto:**
```python
# Define valores exatos
atualizar_estatisticas_usuario('admin',
    emails_organizados=100,
    duplicatas_removidas=10,
    categorias_criadas=8,
    incrementar=False
)
```

### `resetar_estatisticas_usuario(user_id)`
Reseta todas as estatísticas para zero.

```python
resetar_estatisticas_usuario('admin')
# Define tudo como 0
```

## Funções JavaScript

### `carregarEstatisticas()`
Carrega estatísticas do servidor e atualiza interface.

```javascript
await carregarEstatisticas();
// Atualiza totalOrganizados, totalDuplicatas, totalCategorias
```

### `atualizarMetricas()`
Atualiza os elementos da interface com as variáveis globais.

```javascript
atualizarMetricas();
// Atualiza #metric-total, #metric-duplicatas, #metric-categorias
```

### `resetarEstatisticas()`
Reseta estatísticas (com confirmação) e atualiza interface.

```javascript
await resetarEstatisticas();
// Pede confirmação, reseta no backend, atualiza UI
```

## Fluxo de Atualização

### 1. Organização de E-mails
```
Usuário clica "Organizar Agora"
↓
Backend processa e-mails
↓
Ao concluir: atualizar_estatisticas_usuario()
↓
WebSocket envia evento 'conclusao'
↓
Frontend recebe evento
↓
carregarEstatisticas() busca dados atualizados
↓
Interface é atualizada
```

### 2. Verificação de Duplicatas
```
Usuário clica "Verificar Duplicatas"
↓
Backend processa duplicatas
↓
Ao concluir: atualizar_estatisticas_usuario()
↓
WebSocket envia evento 'duplicatas_resultado'
↓
Frontend recebe evento
↓
carregarEstatisticas() busca dados atualizados
↓
Interface é atualizada
```

### 3. Login do Usuário
```
Usuário faz login
↓
Página index.html carrega
↓
DOMContentLoaded dispara
↓
carregarEstatisticas() é chamada
↓
Dados são carregados do banco
↓
Interface mostra valores salvos
```

## Logs de Atividade

O sistema registra:
- ✅ `statistics_reset` - Quando estatísticas são resetadas
- ✅ `email_organization_completed` - Inclui métricas da operação
- ✅ `duplicate_check_completed` - Inclui número de duplicatas

## Migração de Banco Existente

Se você já tem um banco de dados `organizer.db`, execute:

```bash
python migrate_db.py
```

A migração:
1. ✅ Cria tabela `user_statistics`
2. ✅ Inicializa registros para usuários existentes
3. ✅ Mantém dados existentes intactos

## Comportamento de Categorias

O campo `categorias_criadas` usa lógica especial:

- **Incremento:** Sempre usa o **maior valor** (não soma)
- **Razão:** Categorias são contadas por operação, não acumuladas

```python
# Se tinha 5 categorias e operação criou 8
# Resultado: 8 (não 13)

# Se tinha 10 categorias e operação criou 5  
# Resultado: 10 (mantém o maior)
```

## Interface do Usuário

### Métricas Exibidas
```
┌─────────────────────────────────────────┐
│  📊 E-mails Organizados:      1,234     │
│  🗑️ Duplicatas Removidas:     56        │
│  📁 Categorias Criadas:        8        │
│  ⏹️ Status:                    ✅        │
└─────────────────────────────────────────┘
```

### Valores Persistem Após:
- ✅ Logout
- ✅ Fechar navegador
- ✅ Reiniciar aplicação
- ✅ Reiniciar computador

### Valores São Resetados Apenas:
- ❌ Manualmente pelo usuário (botão resetar)
- ❌ Administrador remove registro do banco

## Testes

### Teste 1: Persistência Após Logout
```bash
1. Faça login
2. Organize alguns e-mails (ex: métrica mostra 100)
3. Faça logout
4. Faça login novamente
5. ✅ Métrica ainda mostra 100
```

### Teste 2: Incremento de Valores
```bash
1. Métricas: 100 emails, 10 duplicatas
2. Organize mais 50 emails
3. ✅ Métricas: 150 emails, 10 duplicatas
```

### Teste 3: Reset Manual
```bash
1. Métricas: 500 emails
2. Clique em botão resetar (se implementado)
3. Confirme ação
4. ✅ Métricas: 0 emails
```

## Verificação Manual no Banco

```bash
# Conectar ao banco
sqlite3 organizer.db

# Ver estatísticas de todos os usuários
SELECT * FROM user_statistics;

# Ver estatísticas de um usuário específico
SELECT * FROM user_statistics WHERE user_id = 'admin';

# Resetar manualmente (se necessário)
UPDATE user_statistics 
SET emails_organizados = 0, duplicatas_removidas = 0, categorias_criadas = 0
WHERE user_id = 'admin';
```

## Compatibilidade

- ✅ Funciona com contas existentes
- ✅ Não quebra fluxo atual
- ✅ Migração automática no `init_database()`
- ✅ Totalmente retrocompatível
- ✅ Suporta múltiplos usuários independentes

## Próximas Melhorias Sugeridas

1. **Gráficos de Progresso**
   - Gráfico de linha mostrando evolução ao longo do tempo
   - Gráfico de pizza com distribuição de categorias

2. **Histórico Detalhado**
   - Timeline de todas as operações
   - Exportar relatório em PDF

3. **Metas e Conquistas**
   - Sistema de badges (ex: "100 emails organizados!")
   - Metas personalizáveis

4. **Comparações**
   - Estatísticas por período (semanal, mensal)
   - Comparar com outros usuários (rankings)

5. **Alertas**
   - Notificar quando atingir marcos
   - Lembrar de organizar e-mails periodicamente
