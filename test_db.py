#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para verificar o banco de dados SQLite
"""

import sqlite3
import os

DB_PATH = 'organizer.db'

def verificar_banco():
    print("=" * 50)
    print("VERIFICAÇÃO DO BANCO DE DADOS")
    print("=" * 50)
    
    # Verificar se arquivo existe
    if os.path.exists(DB_PATH):
        print(f"✓ Arquivo {DB_PATH} encontrado")
        tamanho = os.path.getsize(DB_PATH)
        print(f"  Tamanho: {tamanho} bytes")
    else:
        print(f"✗ Arquivo {DB_PATH} NÃO encontrado")
        return
    
    # Conectar e verificar tabelas
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Listar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = cursor.fetchall()
        print(f"\n✓ Tabelas encontradas: {len(tabelas)}")
        for tabela in tabelas:
            print(f"  - {tabela[0]}")
        
        # Verificar usuários
        print("\n" + "=" * 50)
        print("TABELA: users")
        print("=" * 50)
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        print(f"Total de usuários: {total_users}")
        
        cursor.execute("SELECT user_id, name, is_admin FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"  - {user[0]} | {user[1]} | Admin: {bool(user[2])}")
        
        # Verificar códigos de convite
        print("\n" + "=" * 50)
        print("TABELA: invite_codes")
        print("=" * 50)
        cursor.execute("SELECT COUNT(*) FROM invite_codes")
        total_codes = cursor.fetchone()[0]
        print(f"Total de códigos: {total_codes}")
        
        cursor.execute("SELECT code, created_by, used FROM invite_codes")
        codes = cursor.fetchall()
        for code in codes:
            print(f"  - {code[0]} | Criado por: {code[1]} | Usado: {bool(code[2])}")
        
        # Verificar atividades
        print("\n" + "=" * 50)
        print("TABELA: user_activities")
        print("=" * 50)
        cursor.execute("SELECT COUNT(*) FROM user_activities")
        total_activities = cursor.fetchone()[0]
        print(f"Total de atividades: {total_activities}")
        
        # Últimas 10 atividades
        cursor.execute("""
            SELECT user_id, action, timestamp 
            FROM user_activities 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        activities = cursor.fetchall()
        if activities:
            print("\nÚltimas 10 atividades:")
            for act in activities:
                print(f"  - {act[2]} | {act[0]} | {act[1]}")
        else:
            print("  Nenhuma atividade registrada ainda")
        
        # Atividades por usuário
        print("\n" + "=" * 50)
        print("ATIVIDADES POR USUÁRIO")
        print("=" * 50)
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM user_activities
            GROUP BY user_id
            ORDER BY total DESC
        """)
        user_stats = cursor.fetchall()
        if user_stats:
            for stat in user_stats:
                print(f"  - {stat[0]}: {stat[1]} atividades")
        else:
            print("  Nenhuma atividade registrada")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("✓ VERIFICAÇÃO CONCLUÍDA COM SUCESSO")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ Erro ao verificar banco: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verificar_banco()
