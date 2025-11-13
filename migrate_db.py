"""
Script de migração do banco de dados para adicionar:
- Colunas gmail_email e gmail_password na tabela users
- Tabela user_statistics para métricas persistentes
"""
import sqlite3
import os

DB_PATH = 'organizer.db'

def migrate_database():
    """Adiciona colunas e tabelas necessárias se não existirem"""
    if not os.path.exists(DB_PATH):
        print("⚠️  Banco de dados não encontrado.")
        print("ℹ️  O banco será criado automaticamente pelo app.py na primeira execução.")
        print("✅ Migração não necessária neste momento.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔧 MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    
    # ========== MIGRAÇÃO 1: Colunas de credenciais Gmail ==========
    print("\n📋 Verificando tabela users...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"   Colunas existentes: {len(columns)}")
    
    changes_made = False
    
    if 'gmail_email' not in columns:
        print("   📝 Adicionando coluna gmail_email...")
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_email TEXT')
        changes_made = True
        print("   ✅ Coluna gmail_email adicionada!")
    else:
        print("   ℹ️  Coluna gmail_email já existe")
    
    if 'gmail_password' not in columns:
        print("   📝 Adicionando coluna gmail_password...")
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_password TEXT')
        changes_made = True
        print("   ✅ Coluna gmail_password adicionada!")
    else:
        print("   ℹ️  Coluna gmail_password já existe")
    
    # ========== MIGRAÇÃO 2: Tabela de estatísticas ==========
    print("\n📊 Verificando tabela user_statistics...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_statistics'")
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("   📝 Criando tabela user_statistics...")
        cursor.execute('''
            CREATE TABLE user_statistics (
                user_id TEXT PRIMARY KEY,
                emails_organizados INTEGER DEFAULT 0,
                duplicatas_removidas INTEGER DEFAULT 0,
                categorias_criadas INTEGER DEFAULT 0,
                ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        changes_made = True
        print("   ✅ Tabela user_statistics criada!")
        
        # Inicializar estatísticas para usuários existentes
        print("   📝 Inicializando estatísticas para usuários existentes...")
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        for (user_id,) in users:
            cursor.execute('''
                INSERT INTO user_statistics (user_id, emails_organizados, duplicatas_removidas, categorias_criadas)
                VALUES (?, 0, 0, 0)
            ''', (user_id,))
        print(f"   ✅ Estatísticas inicializadas para {len(users)} usuário(s)!")
    else:
        print("   ℹ️  Tabela user_statistics já existe")
    
    # ========== COMMIT E VERIFICAÇÃO FINAL ==========
    if changes_made:
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✅ BANCO DE DADOS JÁ ESTÁ ATUALIZADO!")
        print("=" * 60)
    
    # ========== MOSTRAR ESTRUTURA FINAL ==========
    print("\n📋 Estrutura da tabela users:")
    cursor.execute("PRAGMA table_info(users)")
    for col in cursor.fetchall():
        print(f"   - {col[1]} ({col[2]})")
    
    print("\n� Estrutura da tabela user_statistics:")
    cursor.execute("PRAGMA table_info(user_statistics)")
    for col in cursor.fetchall():
        print(f"   - {col[1]} ({col[2]})")
    
    # ========== ESTATÍSTICAS DE DADOS ==========
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_statistics')
    total_stats = cursor.fetchone()[0]
    
    print(f"\n� Dados atuais:")
    print(f"   - Usuários cadastrados: {total_users}")
    print(f"   - Registros de estatísticas: {total_stats}")
    
    conn.close()
    print("\n" + "=" * 60)

if __name__ == '__main__':
    migrate_database()
