"""
Script de migração do banco de dados para adicionar colunas gmail_email e gmail_password
"""
import sqlite3
import os

DB_PATH = 'organizer.db'

def migrate_database():
    """Adiciona colunas gmail_email e gmail_password se não existirem"""
    if not os.path.exists(DB_PATH):
        print("❌ Banco de dados não encontrado. Execute o app.py primeiro.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Verificar se as colunas já existem
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    print(f"✅ Colunas existentes: {columns}")
    
    changes_made = False
    
    if 'gmail_email' not in columns:
        print("📝 Adicionando coluna gmail_email...")
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_email TEXT')
        changes_made = True
        print("✅ Coluna gmail_email adicionada!")
    else:
        print("ℹ️ Coluna gmail_email já existe")
    
    if 'gmail_password' not in columns:
        print("📝 Adicionando coluna gmail_password...")
        cursor.execute('ALTER TABLE users ADD COLUMN gmail_password TEXT')
        changes_made = True
        print("✅ Coluna gmail_password adicionada!")
    else:
        print("ℹ️ Coluna gmail_password já existe")
    
    if changes_made:
        conn.commit()
        print("\n✅ Migração concluída com sucesso!")
    else:
        print("\n✅ Banco de dados já está atualizado!")
    
    # Mostrar estrutura final
    cursor.execute("PRAGMA table_info(users)")
    print("\n📋 Estrutura da tabela users:")
    for col in cursor.fetchall():
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()

if __name__ == '__main__':
    print("🔧 Iniciando migração do banco de dados...\n")
    migrate_database()
