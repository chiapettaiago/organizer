# Variáveis de Ambiente - Heroku

## Configuração Básica

```bash
# Desabilitar debug em produção
heroku config:set DEBUG=False

# Aumentar timeout (se necessário)
heroku config:set TIMEOUT=60
```

## Ver Configurações Atuais

```bash
heroku config
```

## Remover Variável

```bash
heroku config:unset NOME_VARIAVEL
```

## Variáveis Disponíveis

### DEBUG
- **Descrição**: Ativa/desativa modo debug do Flask
- **Valores**: `True` ou `False`
- **Recomendado em produção**: `False`

```bash
heroku config:set DEBUG=False
```

### PORT
- **Descrição**: Porta onde o app roda
- **Valor**: Definido automaticamente pelo Heroku
- **Não modificar**: Heroku define automaticamente

## Variáveis Opcionais Futuras

Se você quiser adicionar autenticação ou outras features:

```bash
# Secret key personalizada
heroku config:set SECRET_KEY="sua-chave-super-secreta-aqui"

# Modo de manutenção
heroku config:set MAINTENANCE_MODE=False

# Limite de emails customizado
heroku config:set EMAIL_LIMIT=2000
```

## Logs de Configuração

```bash
# Ver mudanças de configuração
heroku releases

# Reverter para versão anterior
heroku rollback
```
