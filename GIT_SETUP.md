# 🔧 Git Setup - Gmail Organizer Pro

## Inicializar Repositório Git

Execute os comandos abaixo para inicializar o Git e fazer o primeiro commit:

```bash
# Inicializar repositório Git
git init

# Adicionar todos os arquivos
git add .

# Fazer o primeiro commit
git commit -m "🎉 Versão 2.0.0 - Interface profissional e deploy ready"

# Criar branch main (se necessário)
git branch -M main
```

## Conectar com GitHub

### Opção 1: Criar novo repositório no GitHub

1. Acesse https://github.com/new
2. Nome: `gmail-organizer-pro`
3. Descrição: `🚀 Organize seus e-mails do Gmail automaticamente com IA`
4. Público ou Privado (sua escolha)
5. **NÃO** marque "Add README" (já temos)
6. Clique em "Create repository"

7. Conecte o repositório local:
```bash
# Substitua SEU-USUARIO pelo seu usuário do GitHub
git remote add origin https://github.com/SEU-USUARIO/gmail-organizer-pro.git

# Push inicial
git push -u origin main
```

### Opção 2: Via GitHub CLI (recomendado)

```bash
# Login no GitHub
gh auth login

# Criar repositório e fazer push
gh repo create gmail-organizer-pro --public --source=. --push

# Ou para privado
gh repo create gmail-organizer-pro --private --source=. --push
```

## Estrutura de Branches (Opcional)

Para desenvolvimento profissional:

```bash
# Branch de desenvolvimento
git checkout -b develop

# Branch de features
git checkout -b feature/nova-funcionalidade

# Branch de hotfix
git checkout -b hotfix/correcao-urgente
```

## Tags de Versão

```bash
# Criar tag da versão 2.0.0
git tag -a v2.0.0 -m "Versão 2.0.0 - Interface profissional"

# Push das tags
git push origin --tags
```

## Deploy Automático

### GitHub + Heroku

```bash
# Conectar Heroku com GitHub
heroku git:remote -a gmail-organizer-pro

# Deploy automático no push
git push heroku main
```

### GitHub + Streamlit Cloud

1. Acesse https://share.streamlit.io
2. Clique em "New app"
3. Conecte com o repositório GitHub
4. Deploy automático!

## Comandos Úteis

```bash
# Ver status
git status

# Ver histórico
git log --oneline --graph

# Desfazer último commit (mantém mudanças)
git reset --soft HEAD~1

# Desfazer mudanças não commitadas
git checkout -- .

# Atualizar do remoto
git pull origin main

# Criar nova release
git tag -a v2.1.0 -m "Nova versão"
git push origin v2.1.0
```

## .gitignore

O arquivo `.gitignore` já está configurado para ignorar:
- ✅ `.venv/` - Ambiente virtual
- ✅ `__pycache__/` - Cache Python
- ✅ `.env` - Variáveis de ambiente
- ✅ `.streamlit/secrets.toml` - Secrets do Streamlit
- ✅ `emails_organizados/` - E-mails locais
- ✅ `*.log` - Arquivos de log

## Workflow Recomendado

### Para mudanças pequenas:
```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
git push
```

### Para desenvolvimento:
```bash
# 1. Crie uma branch
git checkout -b feature/minha-feature

# 2. Faça as mudanças
# ... código ...

# 3. Commit
git add .
git commit -m "feat: minha nova feature"

# 4. Push da branch
git push -u origin feature/minha-feature

# 5. Crie Pull Request no GitHub
# 6. Após aprovação, merge para main
git checkout main
git merge feature/minha-feature
git push
```

## Conventional Commits

Use mensagens de commit padronizadas:

- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação
- `refactor:` - Refatoração
- `test:` - Testes
- `chore:` - Manutenção

Exemplos:
```bash
git commit -m "feat: adiciona detecção de duplicatas"
git commit -m "fix: corrige erro na listagem de e-mails"
git commit -m "docs: atualiza README com novas instruções"
```

## Troubleshooting

**Erro: "remote origin already exists"**
```bash
git remote remove origin
git remote add origin https://github.com/SEU-USUARIO/gmail-organizer-pro.git
```

**Erro: "Permission denied (publickey)"**
```bash
# Configure SSH
ssh-keygen -t ed25519 -C "seu-email@example.com"
# Adicione a chave em: https://github.com/settings/keys
```

**Conflitos de merge**
```bash
# Ver conflitos
git status

# Edite os arquivos conflitantes
# Depois:
git add .
git commit -m "resolve: conflitos de merge"
```

---

**Pronto para começar!** 🚀

Execute `git init` e siga os passos acima para versionar seu projeto.
