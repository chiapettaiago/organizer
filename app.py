from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for, flash, has_request_context
from flask_socketio import SocketIO, emit
import imaplib
import email
from email.header import decode_header
import re
from textblob import TextBlob
import threading
import time
import datetime
import traceback
import json
from functools import wraps
import secrets
import hashlib
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(hours=24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ===============================
# USUÁRIOS (Em produção, use banco de dados)
# ===============================
# Senha: hash de 'admin123'
USERS = {
    'admin': {
        'password': hashlib.sha256('admin123'.encode()).hexdigest(),
        'name': 'Administrador',
        'is_admin': True
    }
}

# ===============================
# CÓDIGOS DE CONVITE
# ===============================
# BANCO DE DADOS SQLITE
# ===============================
DB_PATH = 'organizer.db'

def init_database():
    """Inicializa o banco de dados SQLite com todas as tabelas"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            gmail_email TEXT,
            gmail_password TEXT
        )
    ''')
    
    # Tabela de códigos de convite
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invite_codes (
            code TEXT PRIMARY KEY,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            used INTEGER DEFAULT 0,
            used_by TEXT,
            used_at TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    ''')
    
    # Tabela de atividades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Tabela de estatísticas do usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_statistics (
            user_id TEXT PRIMARY KEY,
            emails_organizados INTEGER DEFAULT 0,
            duplicatas_removidas INTEGER DEFAULT 0,
            categorias_criadas INTEGER DEFAULT 0,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Índices para melhor performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON user_activities(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON user_activities(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_action ON user_activities(action)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_created_by ON invite_codes(created_by)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_invite_used ON invite_codes(used)')
    
    # Inserir usuário admin padrão se não existir
    cursor.execute('SELECT COUNT(*) FROM users WHERE user_id = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (user_id, password_hash, name, email, is_admin)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', admin_password, 'Administrador', 'admin@organizer.local', 1))
    
    conn.commit()
    conn.close()

# Inicializar banco ao carregar app
init_database()

# ===============================
# FUNÇÕES DE GERENCIAMENTO DE USUÁRIOS
# ===============================
def criar_usuario(user_id, password, name, email=None, is_admin=False):
    """Cria um novo usuário no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (user_id, password_hash, name, email, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, password_hash, name, email, 1 if is_admin else 0, datetime.datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False  # Usuário já existe
    except Exception as e:
        print(f"Erro ao criar usuário: {e}")
        return False

def obter_usuario(user_id):
    """Obtém dados de um usuário do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, password_hash, name, email, is_admin, created_at, last_login
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0],
                'password': row[1],
                'nome': row[2],
                'email': row[3],
                'is_admin': bool(row[4]),
                'criado_em': row[5],
                'last_login': row[6]
            }
        return None
    except Exception as e:
        print(f"Erro ao obter usuário: {e}")
        return None

def obter_todos_usuarios():
    """Retorna todos os usuários do sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, name, email, is_admin, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')
        
        usuarios = {}
        for row in cursor.fetchall():
            usuarios[row[0]] = {
                'nome': row[1],
                'email': row[2],
                'is_admin': bool(row[3]),
                'criado_em': row[4],
                'last_login': row[5]
            }
        
        conn.close()
        return usuarios
    except Exception as e:
        print(f"Erro ao obter usuários: {e}")
        return {}

def atualizar_ultimo_login(user_id):
    """Atualiza o timestamp do último login"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_login = ? WHERE user_id = ?
        ''', (datetime.datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao atualizar último login: {e}")
        return False

def validar_credenciais(user_id, password):
    """Valida credenciais de login"""
    usuario = obter_usuario(user_id)
    if not usuario:
        return False
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return usuario['password'] == password_hash

# ===============================
# FUNÇÕES DE CÓDIGOS DE CONVITE
# ===============================
def gerar_codigo_convite(created_by):
    """Gera um novo código de convite no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        codigo = secrets.token_urlsafe(16)[:12].upper()
        
        cursor.execute('''
            INSERT INTO invite_codes (code, created_by, created_at, used, used_by, used_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (codigo, created_by, datetime.datetime.now().isoformat(), 0, None, None))
        
        conn.commit()
        conn.close()
        return codigo
    except Exception as e:
        print(f"Erro ao gerar código de convite: {e}")
        return None

def obter_codigo_convite(code):
    """Obtém informações de um código de convite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, created_by, created_at, used, used_by, used_at
            FROM invite_codes WHERE code = ?
        ''', (code.upper().strip(),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'code': row[0],
                'created_by': row[1],
                'created_at': row[2],
                'used': bool(row[3]),
                'used_by': row[4],
                'used_at': row[5]
            }
        return None
    except Exception as e:
        print(f"Erro ao obter código de convite: {e}")
        return None

def obter_todos_convites():
    """Retorna todos os códigos de convite"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT code, created_by, created_at, used, used_by, used_at
            FROM invite_codes
            ORDER BY created_at DESC
        ''')
        
        convites = {}
        for row in cursor.fetchall():
            convites[row[0]] = {
                'created_by': row[1],
                'created_at': row[2],
                'used': bool(row[3]),
                'used_by': row[4],
                'used_at': row[5]
            }
        
        conn.close()
        return convites
    except Exception as e:
        print(f"Erro ao obter convites: {e}")
        return {}

def marcar_convite_usado(code, used_by):
    """Marca um código de convite como usado"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE invite_codes 
            SET used = 1, used_by = ?, used_at = ?
            WHERE code = ?
        ''', (used_by, datetime.datetime.now().isoformat(), code.upper().strip()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao marcar convite como usado: {e}")
        return False

def revogar_codigo_convite(code):
    """Remove um código de convite do banco"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM invite_codes WHERE code = ?', (code.upper().strip(),))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao revogar código: {e}")
        return False

def validar_codigo_convite(code):
    """Valida se um código de convite existe e não foi usado"""
    convite = obter_codigo_convite(code)
    if convite and not convite['used']:
        return True
    return False

# ===============================
# FUNÇÕES DE CREDENCIAIS DO GMAIL
# ===============================
def salvar_credenciais_gmail(user_id, gmail_email, gmail_password):
    """Salva as credenciais do Gmail do usuário (criptografia básica)"""
    try:
        import base64
        # Criptografia básica com base64 (em produção, use cryptography ou keyring)
        encrypted_password = base64.b64encode(gmail_password.encode()).decode()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET gmail_email = ?, gmail_password = ?
            WHERE user_id = ?
        ''', (gmail_email, encrypted_password, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar credenciais Gmail: {e}")
        traceback.print_exc()
        return False

def obter_credenciais_gmail(user_id):
    """Obtém as credenciais do Gmail do usuário"""
    try:
        import base64
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT gmail_email, gmail_password
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] and row[1]:
            # Descriptografar senha
            decrypted_password = base64.b64decode(row[1].encode()).decode()
            return {
                'gmail_email': row[0],
                'gmail_password': decrypted_password
            }
        return None
    except Exception as e:
        print(f"Erro ao obter credenciais Gmail: {e}")
        traceback.print_exc()
        return None

def remover_credenciais_gmail(user_id):
    """Remove as credenciais do Gmail do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET gmail_email = NULL, gmail_password = NULL
            WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao remover credenciais Gmail: {e}")
        return False

# ===============================
# ESTATÍSTICAS DO USUÁRIO
# ===============================
def obter_estatisticas_usuario(user_id):
    """Obtém as estatísticas do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT emails_organizados, duplicatas_removidas, categorias_criadas, ultima_atualizacao
            FROM user_statistics WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'emails_organizados': row[0],
                'duplicatas_removidas': row[1],
                'categorias_criadas': row[2],
                'ultima_atualizacao': row[3]
            }
        else:
            # Se não existe, criar registro zerado
            criar_estatisticas_usuario(user_id)
            return {
                'emails_organizados': 0,
                'duplicatas_removidas': 0,
                'categorias_criadas': 0,
                'ultima_atualizacao': datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        traceback.print_exc()
        return None

def criar_estatisticas_usuario(user_id):
    """Cria registro de estatísticas para um novo usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_statistics (user_id, emails_organizados, duplicatas_removidas, categorias_criadas)
            VALUES (?, 0, 0, 0)
        ''', (user_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao criar estatísticas: {e}")
        return False

def atualizar_estatisticas_usuario(user_id, emails_organizados=0, duplicatas_removidas=0, categorias_criadas=0, incrementar=True):
    """Atualiza as estatísticas do usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Garantir que existe registro
        criar_estatisticas_usuario(user_id)
        
        if incrementar:
            # Incrementar valores existentes
            cursor.execute('''
                UPDATE user_statistics 
                SET emails_organizados = emails_organizados + ?,
                    duplicatas_removidas = duplicatas_removidas + ?,
                    categorias_criadas = CASE 
                        WHEN ? > categorias_criadas THEN ?
                        ELSE categorias_criadas
                    END,
                    ultima_atualizacao = ?
                WHERE user_id = ?
            ''', (emails_organizados, duplicatas_removidas, categorias_criadas, categorias_criadas, 
                  datetime.datetime.now().isoformat(), user_id))
        else:
            # Definir valores absolutos
            cursor.execute('''
                UPDATE user_statistics 
                SET emails_organizados = ?,
                    duplicatas_removidas = ?,
                    categorias_criadas = ?,
                    ultima_atualizacao = ?
                WHERE user_id = ?
            ''', (emails_organizados, duplicatas_removidas, categorias_criadas, 
                  datetime.datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Estatísticas atualizadas para {user_id}: +{emails_organizados} emails, +{duplicatas_removidas} duplicatas, {categorias_criadas} categorias")
        return True
    except Exception as e:
        print(f"Erro ao atualizar estatísticas: {e}")
        traceback.print_exc()
        return False

def resetar_estatisticas_usuario(user_id):
    """Reseta as estatísticas do usuário para zero"""
    return atualizar_estatisticas_usuario(user_id, 0, 0, 0, incrementar=False)

# ===============================
# LOGS E HISTÓRICO DE ATIVIDADES
# ===============================
def registrar_atividade(user_id, action, details=None, ip_address=None):
    """Registra uma atividade do usuário no banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        details_json = json.dumps(details) if details else '{}'
        
        # Tentar obter IP e user agent do request, com fallback
        if has_request_context():
            ip = ip_address or request.remote_addr
            user_agent = request.headers.get('User-Agent', 'unknown')
        else:
            ip = ip_address or 'system'
            user_agent = 'system'
        
        cursor.execute('''
            INSERT INTO user_activities (user_id, timestamp, action, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, timestamp, action, details_json, ip, user_agent))
        
        conn.commit()
        conn.close()
        
        print(f"✓ Atividade registrada: {user_id} - {action}")  # Debug
        
        return {
            'timestamp': timestamp,
            'action': action,
            'details': details or {},
            'ip_address': ip,
            'user_agent': user_agent
        }
    except Exception as e:
        print(f"✗ Erro ao registrar atividade: {e}")
        import traceback
        traceback.print_exc()
        return None

def obter_historico_usuario(user_id, limit=100):
    """Retorna o histórico de atividades de um usuário do banco de dados"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, action, details, ip_address, user_agent
            FROM user_activities
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        atividades = []
        for row in rows:
            atividades.append({
                'timestamp': row[0],
                'action': row[1],
                'details': json.loads(row[2]) if row[2] else {},
                'ip_address': row[3],
                'user_agent': row[4]
            })
        
        # Retornar em ordem cronológica (mais antiga primeiro)
        return list(reversed(atividades))
    except Exception as e:
        print(f"Erro ao obter histórico: {e}")
        return []

def obter_total_atividades_usuario(user_id):
    """Retorna o total de atividades registradas de um usuário"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_activities WHERE user_id = ?
        ''', (user_id,))
        
        total = cursor.fetchone()[0]
        conn.close()
        
        return total
    except Exception as e:
        print(f"Erro ao contar atividades: {e}")
        return 0

def obter_todas_atividades(limit=1000):
    """Retorna todas as atividades de todos os usuários"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, timestamp, action, details, ip_address, user_agent
            FROM user_activities
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        atividades = []
        for row in rows:
            atividades.append({
                'user_id': row[0],
                'timestamp': row[1],
                'action': row[2],
                'details': json.loads(row[3]) if row[3] else {},
                'ip_address': row[4],
                'user_agent': row[5]
            })
        
        return atividades
    except Exception as e:
        print(f"Erro ao obter todas atividades: {e}")
        return []

def limpar_atividades_antigas(dias=90):
    """Remove atividades mais antigas que X dias"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        data_limite = (datetime.datetime.now() - datetime.timedelta(days=dias)).isoformat()
        
        cursor.execute('''
            DELETE FROM user_activities WHERE timestamp < ?
        ''', (data_limite,))
        
        deletados = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deletados
    except Exception as e:
        print(f"Erro ao limpar atividades antigas: {e}")
        return 0

def exportar_atividades_csv(user_id=None):
    """Exporta atividades para formato CSV"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute('''
                SELECT user_id, timestamp, action, details, ip_address, user_agent
                FROM user_activities
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT user_id, timestamp, action, details, ip_address, user_agent
                FROM user_activities
                ORDER BY timestamp DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Criar CSV
        csv_lines = ['User ID,Timestamp,Action,Details,IP Address,User Agent']
        for row in rows:
            details = row[3].replace('"', '""')  # Escape aspas
            csv_lines.append(f'"{row[0]}","{row[1]}","{row[2]}","{details}","{row[4]}","{row[5]}"')
        
        return '\n'.join(csv_lines)
    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")
        return None

# Funções antigas removidas - agora usamos as funções SQLite acima
    return False

# ===============================
# CONFIGURAÇÕES
# ===============================
SERVIDOR_IMAP = "imap.gmail.com"
LIMITE_EMAILS = 2000
INTERVALO_SEGUNDOS = 3 * 60 * 60  # 3 horas
TIMEOUT_CONEXAO = 30  # Timeout de conexão em segundos
MAX_ERROS_CONSECUTIVOS = 10  # Máximo de erros antes de parar
KEEPALIVE_INTERVALO = 100  # Enviar NOOP a cada N emails

# Armazenamento em memória (em produção, use Redis ou banco de dados)
execucoes_logs = []
agendador_ativo = False
agendador_thread = None
stop_event = threading.Event()

# Função auxiliar para emitir eventos com contexto
def emit_evento(evento, dados):
    """Emite eventos WebSocket com contexto de aplicação"""
    try:
        socketio.emit(evento, dados)
        socketio.sleep(0)  # Permite que o evento seja processado
    except Exception as e:
        print(f"Erro ao emitir evento {evento}: {e}")

# ===============================
# DECORADORES DE AUTENTICAÇÃO
# ===============================
def login_required(f):
    """Decorator para rotas que requerem login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Não autenticado', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator para rotas que requerem privilégios de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Não autenticado', 'redirect': '/login'}), 401
            return redirect(url_for('login'))
        
        # Verificar se é convidado (não pode ser admin)
        if session.get('is_guest', False):
            if request.is_json:
                return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
            flash('Acesso negado. Apenas administradores.', 'error')
            return redirect(url_for('index'))
        
        # Verificar se tem flag is_admin na sessão ou no banco
        is_admin_session = session.get('is_admin', False)
        user = obter_usuario(session.get('user_id'))
        is_admin_user = user.get('is_admin', False) if user else False
        
        if not (is_admin_session or is_admin_user):
            if request.is_json:
                return jsonify({'error': 'Acesso negado. Apenas administradores.'}), 403
            flash('Acesso negado. Apenas administradores.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

# ===============================
# FUNÇÕES AUXILIARES
# ===============================
def limpar_texto(texto):
    return re.sub(r"[^a-zA-Z0-9áéíóúãõâêôçÁÉÍÓÚÃÕÂÊÔÇ ]", "", texto)

def classificar_email(assunto, corpo):
    texto = f"{assunto} {corpo}".lower()
    categorias = {
        "Faturas": ["boleto", "pagamento", "vencimento", "conta", "nota fiscal", "pix"],
        "Trabalho": ["projeto", "relatório", "reunião", "anexo", "cliente", "documento"],
        "Pessoal": ["amizade", "convite", "parabéns", "evento", "família"],
        "Marketing": ["promoção", "desconto", "oferta", "newsletter", "cupom"],
        "Sistema": ["erro", "bug", "alerta", "sistema", "login"],
    }
    for categoria, palavras in categorias.items():
        if any(p in texto for p in palavras):
            return categoria
    
    # Análise de sentimento com fallback
    try:
        blob = TextBlob(texto)
        sentimento = blob.sentiment.polarity
        if sentimento < -0.1:
            return "Problemas"
        elif sentimento > 0.3:
            return "Positivos"
    except Exception:
        # Se TextBlob falhar, retorna categoria padrão
        pass
    
    return "Neutros"

def conectar_email(email_usuario, senha, log_callback=None):
    """Conecta ao servidor Gmail via IMAP com tratamento de erros e timeout"""
    try:
        if log_callback:
            log_callback(f"🔌 Iniciando conexão com {SERVIDOR_IMAP}...")
        
        # Timeout de 30 segundos para conexão
        imap = imaplib.IMAP4_SSL(SERVIDOR_IMAP, timeout=30)
        
        if log_callback:
            log_callback(f"🔐 Autenticando usuário: {email_usuario}")
        
        imap.login(email_usuario, senha)
        
        if log_callback:
            log_callback(f"✅ Conexão estabelecida com sucesso!")
        
        return imap
        
    except imaplib.IMAP4.error as e:
        erro_msg = str(e).lower()
        if 'authentication failed' in erro_msg or 'invalid credentials' in erro_msg:
            raise Exception("❌ ERRO DE AUTENTICAÇÃO\n\n"
                          "Suas credenciais estão incorretas ou você precisa usar uma 'Senha de App'.\n\n"
                          "📌 COMO RESOLVER:\n"
                          "1. Verifique se o email e senha estão corretos\n"
                          "2. Se usar verificação em 2 etapas, gere uma Senha de App:\n"
                          "   • Acesse: myaccount.google.com/apppasswords\n"
                          "   • Crie uma senha para 'Mail'\n"
                          "   • Use essa senha gerada no lugar da sua senha normal")
        else:
            raise Exception(f"❌ Erro de autenticação: {str(e)}")
    
    except Exception as e:
        raise Exception(f"❌ Erro ao conectar ao servidor: {str(e)}\n\n"
                       "Verifique sua conexão com a internet.")

def listar_emails(imap, limite=LIMITE_EMAILS, log_callback=None, progress_callback=None):
    """Lista emails com tratamento de erro e timeout"""
    try:
        if log_callback:
            log_callback(f"📬 Selecionando caixa de entrada (INBOX)...")
        
        imap.select("INBOX")
        
        if log_callback:
            log_callback(f"🔍 Buscando e-mails na caixa de entrada...")
        
        status, mensagens = imap.search(None, "ALL")
        if status != "OK":
            if log_callback:
                log_callback(f"❌ Erro ao buscar e-mails. Status: {status}")
            return []
        
        ids = mensagens[0].split()
        total_inbox = len(ids)
        limite_real = min(limite, total_inbox)
        
        if log_callback:
            log_callback(f"📊 Total de e-mails encontrados: {total_inbox}")
            log_callback(f"📥 Carregando os últimos {limite_real} e-mails...")
        
        emails = []
        ids_para_processar = ids[-limite_real:]
        erros_consecutivos = 0
        max_erros = 10  # Máximo de erros consecutivos antes de parar
        
        for idx, num in enumerate(ids_para_processar, 1):
            try:
                if progress_callback:
                    percentual_listagem = (idx / limite_real) * 100
                    progress_callback(idx / limite_real, f"Carregando e-mails: {idx}/{limite_real} ({int(percentual_listagem)}%)")
                
                if log_callback and idx % 50 == 0:
                    log_callback(f"📖 Carregados {idx}/{limite_real} e-mails...")
                
                # Timeout individual para cada fetch
                status, data = imap.fetch(num, "(RFC822)")
                if status != "OK":
                    erros_consecutivos += 1
                    if erros_consecutivos >= max_erros:
                        if log_callback:
                            log_callback(f"⚠️ Muitos erros consecutivos. Parando listagem.")
                        break
                    continue
                
                # Reseta contador de erros em caso de sucesso
                erros_consecutivos = 0
                
                msg = email.message_from_bytes(data[0][1])
                assunto, cod = decode_header(msg["Subject"])[0]
                if isinstance(assunto, bytes):
                    assunto = assunto.decode(cod or "utf-8", errors="ignore")
                
                corpo = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        corpo += part.get_payload(decode=True).decode(errors="ignore")
                
                emails.append({
                    "id": num,
                    "assunto": assunto or "(Sem assunto)",
                    "corpo": corpo
                })
                
            except Exception as e:
                erros_consecutivos += 1
                if log_callback and idx % 10 == 0:
                    log_callback(f"⚠️ Erro ao processar e-mail {idx}: {str(e)[:50]}")
                
                if erros_consecutivos >= max_erros:
                    if log_callback:
                        log_callback(f"❌ Muitos erros consecutivos ({max_erros}). Parando listagem.")
                    break
                continue
        
        if log_callback:
            log_callback(f"✅ {len(emails)} e-mails carregados com sucesso!")
        
        return emails
        
    except Exception as e:
        if log_callback:
            log_callback(f"❌ Erro ao listar e-mails: {str(e)}")
        raise

def mover_email(imap, email_id, categoria, log_callback=None):
    """Move email com tratamento robusto de erros"""
    try:
        if log_callback:
            log_callback(f"📁 Criando/verificando pasta: {categoria}")
        
        # Ignora erro se pasta já existe
        try:
            imap.create(categoria)
        except:
            pass  # Pasta já existe
        
        if log_callback:
            log_callback(f"📤 Copiando e-mail para: {categoria}")
        
        imap.copy(email_id, categoria)
        
        if log_callback:
            log_callback(f"🗑️ Marcando e-mail original para exclusão")
        
        imap.store(email_id, '+FLAGS', '\\Deleted')
        
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"⚠️ Erro ao mover e-mail: {str(e)[:100]}")
        return False

def verificar_e_remover_duplicatas(imap, log_callback=None, progress_callback=None):
    if log_callback:
        log_callback("\n" + "=" * 50)
        log_callback("🔍 VERIFICANDO DUPLICATAS")
        log_callback("=" * 50)
    
    # Lista todas as pastas
    if log_callback:
        log_callback("📂 Listando todas as pastas do Gmail...")
    
    status, pastas = imap.list()
    if status != "OK":
        if log_callback:
            log_callback("❌ Erro ao listar pastas")
        return 0
    
    pastas_organizadas = []
    for pasta in pastas:
        pasta_nome = pasta.decode().split('"/"')[-1].strip(' "')
        if pasta_nome not in ['INBOX', '[Gmail]'] and not pasta_nome.startswith('[Gmail]/'):
            pastas_organizadas.append(pasta_nome)
    
    if log_callback:
        log_callback(f"📁 Pastas organizadas encontradas: {len(pastas_organizadas)}")
    
    if progress_callback:
        progress_callback(0.2, "📂 Pastas listadas")
    
    # Obtém IDs dos e-mails na INBOX
    imap.select("INBOX")
    status, msgs_inbox = imap.search(None, "ALL")
    if status != "OK":
        return 0
    
    ids_inbox = msgs_inbox[0].split()
    if not ids_inbox:
        if log_callback:
            log_callback("📭 INBOX vazia")
        return 0
    
    total_inbox = len(ids_inbox)
    
    # Limita a 1000 e-mails mais recentes
    LIMITE_VERIFICACAO = 1000
    if total_inbox > LIMITE_VERIFICACAO:
        ids_inbox = ids_inbox[-LIMITE_VERIFICACAO:]
        if log_callback:
            log_callback(f"⚠️ Verificando últimos {LIMITE_VERIFICACAO} de {total_inbox} e-mails")
    
    if log_callback:
        log_callback(f"📧 E-mails a verificar: {len(ids_inbox)}")
    
    # Mapeia Message-IDs com tratamento de erro
    inbox_message_ids = {}
    erros_mapping = 0
    
    for idx, email_id in enumerate(ids_inbox, 1):
        try:
            status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
            if status == "OK":
                msg = email.message_from_bytes(data[0][1])
                message_id = msg.get("Message-ID", "").strip()
                if message_id:
                    inbox_message_ids[message_id] = email_id
            else:
                erros_mapping += 1
        except Exception as e:
            erros_mapping += 1
            if erros_mapping > MAX_ERROS_CONSECUTIVOS:
                if log_callback:
                    log_callback(f"❌ Muitos erros ao mapear e-mails. Abortando.")
                return 0
        
        if progress_callback and idx % 20 == 0:
            progresso = 0.2 + (idx / len(ids_inbox)) * 0.3
            progress_callback(progresso, f"Mapeando: {idx}/{len(ids_inbox)}")
        
        # Keepalive
        if idx % KEEPALIVE_INTERVALO == 0:
            try:
                imap.noop()
            except:
                pass
    
    # Verifica duplicatas com tratamento de erro
    duplicatas_encontradas = set()
    pastas_com_erro = 0
    
    for idx_pasta, pasta in enumerate(pastas_organizadas, 1):
        try:
            status, _ = imap.select(f'"{pasta}"' if ' ' in pasta else pasta, readonly=True)
            if status != "OK":
                pastas_com_erro += 1
                continue
            
            status, msgs_pasta = imap.search(None, "ALL")
            if status != "OK":
                pastas_com_erro += 1
                continue
            
            ids_pasta = msgs_pasta[0].split()
            if not ids_pasta:
                continue
            
            for idx_email, email_id in enumerate(ids_pasta, 1):
                try:
                    status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
                    if status == "OK":
                        msg = email.message_from_bytes(data[0][1])
                        message_id = msg.get("Message-ID", "").strip()
                        
                        if message_id in inbox_message_ids:
                            duplicatas_encontradas.add(message_id)
                    
                    # Keepalive
                    if idx_email % KEEPALIVE_INTERVALO == 0:
                        try:
                            imap.noop()
                        except:
                            pass
                            
                except Exception as e:
                    continue
        
        except Exception as e:
            pastas_com_erro += 1
            if log_callback:
                log_callback(f"⚠️ Erro na pasta '{pasta}': {str(e)[:50]}")
            continue
        
        # Progress update
        if progress_callback:
            progresso = 0.5 + (idx_pasta / len(pastas_organizadas)) * 0.3
            progress_callback(progresso, f"Verificando: {idx_pasta}/{len(pastas_organizadas)}")
    
    if pastas_com_erro > 0 and log_callback:
        log_callback(f"⚠️ {pastas_com_erro} pastas com erro")
    
    if progress_callback:
        progress_callback(0.8, f"{len(duplicatas_encontradas)} duplicatas encontradas")
    
    # Remove duplicatas com tratamento de erro
    if duplicatas_encontradas:
        if log_callback:
            log_callback(f"🗑️ Removendo {len(duplicatas_encontradas)} duplicatas...")
        
        try:
            imap.select("INBOX")
            removidos = 0
            erros_remocao = 0
            
            for message_id in duplicatas_encontradas:
                try:
                    if message_id in inbox_message_ids:
                        email_id = inbox_message_ids[message_id]
                        imap.store(email_id, '+FLAGS', '\\Deleted')
                        removidos += 1
                except Exception as e:
                    erros_remocao += 1
                    if erros_remocao > MAX_ERROS_CONSECUTIVOS:
                        if log_callback:
                            log_callback(f"❌ Muitos erros ao remover. Abortando.")
                        break
            
            try:
                imap.expunge()
            except Exception as e:
                if log_callback:
                    log_callback(f"⚠️ Erro ao expurgar: {str(e)[:50]}")
            
            if log_callback:
                log_callback(f"✅ {removidos} duplicatas removidas")
                if erros_remocao > 0:
                    log_callback(f"⚠️ {erros_remocao} erros durante remoção")
            
            if progress_callback:
                progress_callback(1.0, f"✅ {removidos} duplicatas removidas!")
            
            return removidos
            
        except Exception as e:
            if log_callback:
                log_callback(f"❌ Erro ao remover duplicatas: {str(e)[:100]}")
            return 0
    else:
        if log_callback:
            log_callback("✅ Nenhuma duplicata encontrada")
        if progress_callback:
            progress_callback(1.0, "✅ Nenhuma duplicata")
        return 0

# ===============================
# ROTAS DE AUTENTICAÇÃO
# ===============================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # Se já está logado, redireciona para index
        if 'user_id' in session:
            return redirect(url_for('index'))
        return render_template('login.html')
    
    # POST - processar login
    data = request.json if request.is_json else request.form
    login_type = data.get('login_type', 'credentials')  # 'credentials' ou 'invite'
    
    if login_type == 'invite':
        # Login com código de convite
        invite_code = data.get('invite_code', '').strip()
        
        if not invite_code:
            if request.is_json:
                return jsonify({'error': 'Código de convite é obrigatório'}), 400
            flash('Código de convite é obrigatório', 'error')
            return redirect(url_for('login'))
        
        if validar_codigo_convite(invite_code):
            # Código válido - redirecionar para página de registro
            codigo_upper = invite_code.upper()
            
            # Registrar validação de convite
            registrar_atividade(
                user_id=f'invite_{codigo_upper}',
                action='invite_validated',
                details={
                    'invite_code': codigo_upper,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            # Armazenar código na sessão temporariamente para a página de registro
            session['pending_invite_code'] = codigo_upper
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Código validado! Complete seu cadastro.',
                    'redirect': url_for('registro_page')
                })
            return redirect(url_for('registro_page'))
        else:
            # Registrar tentativa de convite inválido
            registrar_atividade(
                user_id='unknown',
                action='invite_failed',
                details={
                    'invite_code': invite_code.upper(),
                    'reason': 'invalid_or_used',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            if request.is_json:
                return jsonify({'error': 'Código de convite inválido ou já utilizado'}), 401
            flash('Código de convite inválido ou já utilizado', 'error')
            return redirect(url_for('login'))
    
    else:
        # Login com credenciais normais
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            if request.is_json:
                return jsonify({'error': 'Usuário e senha são obrigatórios'}), 400
            flash('Usuário e senha são obrigatórios', 'error')
            return redirect(url_for('login'))
        
        # Verificar credenciais no banco de dados
        if validar_credenciais(username, password):
            user = obter_usuario(username)
            
            # Atualizar último login
            atualizar_ultimo_login(username)
            
            # Login bem-sucedido
            session.permanent = True
            session['user_id'] = username
            session['user_name'] = user['nome']
            session['is_guest'] = False
            session['is_admin'] = user.get('is_admin', False)
            
            # Registrar login no histórico
            registrar_atividade(
                user_id=username,
                action='login',
                details={
                    'method': 'credentials',
                    'success': True,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login realizado com sucesso',
                    'redirect': url_for('index')
                })
            return redirect(url_for('index'))
        else:
            # Credenciais inválidas - registrar tentativa falha
            registrar_atividade(
                user_id=username if username else 'unknown',
                action='login_failed',
                details={
                    'method': 'credentials',
                    'reason': 'invalid_credentials',
                    'username_attempted': username,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            if request.is_json:
                return jsonify({'error': 'Usuário ou senha inválidos'}), 401
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    
    # Registrar logout
    if user_id:
        registrar_atividade(
            user_id=user_id,
            action='logout',
            details={
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
    
    session.clear()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('login'))

# ===============================
# ROTAS DE REGISTRO
# ===============================
@app.route('/registro')
def registro_page():
    """Página de registro para usuários com código de convite"""
    # Verificar se há código de convite pendente na sessão
    invite_code = session.get('pending_invite_code')
    if not invite_code:
        flash('Código de convite não encontrado. Faça login novamente.', 'error')
        return redirect(url_for('login'))
    
    return render_template('registro.html', invite_code=invite_code)

@app.route('/registrar', methods=['POST'])
def registrar():
    """Processa o registro de novo usuário via código de convite"""
    data = request.json if request.is_json else request.form
    
    nome = data.get('nome', '').strip()
    email = data.get('email', '').strip().lower()
    senha = data.get('senha', '')
    invite_code = data.get('invite_code', '').strip()
    
    # Validações
    if not nome or not email or not senha or not invite_code:
        return jsonify({'error': 'Todos os campos são obrigatórios'}), 400
    
    if len(senha) < 6:
        return jsonify({'error': 'A senha deve ter no mínimo 6 caracteres'}), 400
    
    # Validar formato de email
    import re
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, email):
        return jsonify({'error': 'E-mail inválido'}), 400
    
    # Verificar se o email já existe
    if obter_usuario(email):
        return jsonify({'error': 'Este e-mail já está cadastrado'}), 400
    
    # Verificar se o código de convite está na sessão
    if session.get('pending_invite_code') != invite_code.upper():
        return jsonify({'error': 'Código de convite inválido'}), 400
    
    # Validar código novamente
    if not validar_codigo_convite(invite_code):
        return jsonify({'error': 'Código de convite inválido ou já utilizado'}), 400
    
    # Criar novo usuário no banco de dados
    if not criar_usuario(email, senha, nome, email, is_admin=False):
        return jsonify({'error': 'Erro ao criar usuário'}), 500
    
    # Marcar código como usado
    marcar_convite_usado(invite_code, email)
    
    # Registrar criação de conta
    registrar_atividade(
        user_id=email,
        action='account_created',
        details={
            'name': nome,
            'email': email,
            'created_via': 'invite',
            'invite_code': invite_code.upper(),
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    # Fazer login automático
    session.permanent = True
    session['user_id'] = email
    session['user_name'] = nome
    session['is_guest'] = False
    session['is_admin'] = False
    
    # Atualizar último login
    atualizar_ultimo_login(email)
    
    # Registrar primeiro login
    registrar_atividade(
        user_id=email,
        action='first_login',
        details={
            'method': 'auto_after_registration',
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    # Limpar código pendente
    session.pop('pending_invite_code', None)
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Conta criada com sucesso!',
            'redirect': url_for('index')
        })
    return redirect(url_for('index'))

# ===============================
# ROTAS DE CONVITES (ADMIN)
# ===============================
@app.route('/admin/convites')
@admin_required
def admin_convites():
    """Página de gerenciamento de códigos de convite"""
    convites = obter_todos_convites()
    return render_template('admin_convites.html', 
                         user_name=session.get('user_name', 'Admin'),
                         convites=convites)

@app.route('/admin/atividades')
@admin_required
def admin_atividades():
    """Página de visualização de atividades dos usuários"""
    return render_template('admin_atividades.html',
                         user_name=session.get('user_name', 'Admin'))

@app.route('/api/admin/gerar-convite', methods=['POST'])
@admin_required
def gerar_convite_route():
    """Gera um novo código de convite"""
    try:
        user_id = session.get('user_id')
        codigo = gerar_codigo_convite(user_id)
        
        if not codigo:
            return jsonify({'error': 'Erro ao gerar código'}), 500
        
        # Registrar geração de convite
        registrar_atividade(
            user_id=user_id,
            action='invite_code_generated',
            details={
                'codigo': codigo,
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'codigo': codigo,
            'message': f'Código {codigo} gerado com sucesso!'
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao gerar código: {str(e)}'}), 500

@app.route('/api/admin/listar-convites', methods=['GET'])
@admin_required
def listar_convites():
    """Lista todos os códigos de convite"""
    convites_dict = obter_todos_convites()
    convites = []
    
    for codigo, info in convites_dict.items():
        # Converter string ISO para datetime se necessário
        created_at = info['created_at']
        if isinstance(created_at, str):
            try:
                created_at = datetime.datetime.fromisoformat(created_at)
            except:
                created_at = datetime.datetime.now()
        
        convites.append({
            'codigo': codigo,
            'criado_por': info['created_by'],
            'criado_em': created_at.strftime('%d/%m/%Y %H:%M') if isinstance(created_at, datetime.datetime) else created_at,
            'usado': info['used'],
            'usado_por': info.get('used_by'),
            'usado_em': info.get('used_at')
        })
    
    # Ordenar por usado (não usados primeiro) e depois por código
    convites.sort(key=lambda x: (x['usado'], x['codigo']))
    
    return jsonify({
        'success': True,
        'convites': convites,
        'total': len(convites),
        'usados': sum(1 for c in convites if c['usado']),
        'disponiveis': sum(1 for c in convites if not c['usado'])
    })

@app.route('/api/admin/revogar-convite/<codigo>', methods=['DELETE'])
@admin_required
def revogar_convite_route(codigo):
    """Revoga (remove) um código de convite"""
    codigo = codigo.upper().strip()
    convite = obter_codigo_convite(codigo)
    
    if convite:
        user_id = session.get('user_id')
        
        # Registrar revogação
        registrar_atividade(
            user_id=user_id,
            action='invite_code_revoked',
            details={
                'codigo': codigo,
                'was_used': convite['used'],
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        revogar_codigo_convite(codigo)
        return jsonify({
            'success': True,
            'message': f'Código {codigo} revogado com sucesso'
        })
    else:
        return jsonify({'error': 'Código não encontrado'}), 404

@app.route('/api/admin/usuarios', methods=['GET'])
@admin_required
def listar_usuarios():
    """Lista todos os usuários do sistema"""
    usuarios_dict = obter_todos_usuarios()
    usuarios = []
    
    for user_id, user_data in usuarios_dict.items():
        usuarios.append({
            'id': user_id,
            'nome': user_data.get('nome', 'N/A'),
            'email': user_data.get('email', 'N/A'),
            'is_admin': user_data.get('is_admin', False),
            'criado_em': user_data.get('criado_em', 'N/A')
        })
    
    return jsonify({
        'success': True,
        'usuarios': usuarios,
        'total': len(usuarios)
    })

@app.route('/api/admin/atividades/<user_id>', methods=['GET'])
@admin_required
def obter_atividades_usuario_route(user_id):
    """Obtém o histórico de atividades de um usuário específico"""
    limit = request.args.get('limit', 100, type=int)
    
    usuario = obter_usuario(user_id)
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    historico = obter_historico_usuario(user_id, limit)
    total_atividades = obter_total_atividades_usuario(user_id)
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'nome': usuario.get('nome', 'N/A'),
        'email': usuario.get('email', 'N/A'),
        'total_atividades': total_atividades,
        'atividades': historico
    })

@app.route('/api/admin/atividades/exportar/<user_id>', methods=['GET'])
@admin_required
def exportar_atividades_usuario(user_id):
    """Exporta atividades de um usuário em formato CSV"""
    usuario = obter_usuario(user_id)
    if not usuario:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    csv_data = exportar_atividades_csv(user_id)
    
    if csv_data:
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=atividades_{user_id}.csv'}
        )
    else:
        return jsonify({'error': 'Erro ao exportar dados'}), 500

@app.route('/api/admin/atividades/exportar-todas', methods=['GET'])
@admin_required
def exportar_todas_atividades():
    """Exporta todas as atividades em formato CSV"""
    csv_data = exportar_atividades_csv()
    
    if csv_data:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=atividades_todas_{timestamp}.csv'}
        )
    else:
        return jsonify({'error': 'Erro ao exportar dados'}), 500

@app.route('/api/admin/atividades/limpar', methods=['POST'])
@admin_required
def limpar_atividades():
    """Remove atividades antigas (padrão: 90 dias)"""
    dias = request.json.get('dias', 90)
    
    deletados = limpar_atividades_antigas(dias)
    
    # Registra a limpeza
    user_id = session.get('user_id')
    registrar_atividade(
        user_id=user_id,
        action='activities_cleanup',
        details={
            'dias': dias,
            'registros_deletados': deletados,
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    return jsonify({
        'success': True,
        'message': f'{deletados} registros removidos',
        'deletados': deletados
    })

@app.route('/api/admin/estatisticas', methods=['GET'])
@admin_required
def obter_estatisticas():
    """Retorna estatísticas gerais do sistema"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total de atividades
        cursor.execute('SELECT COUNT(*) FROM user_activities')
        total_atividades = cursor.fetchone()[0]
        
        # Atividades por usuário
        cursor.execute('''
            SELECT user_id, COUNT(*) as count
            FROM user_activities
            GROUP BY user_id
            ORDER BY count DESC
        ''')
        atividades_por_usuario = [{'user_id': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Atividades por tipo
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM user_activities
            GROUP BY action
            ORDER BY count DESC
        ''')
        atividades_por_tipo = [{'action': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Atividades nos últimos 7 dias
        data_limite = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM user_activities WHERE timestamp > ?
        ''', (data_limite,))
        atividades_7_dias = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_atividades': total_atividades,
            'total_usuarios': len(USERS),
            'atividades_7_dias': atividades_7_dias,
            'atividades_por_usuario': atividades_por_usuario,
            'atividades_por_tipo': atividades_por_tipo
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===============================
# ROTAS PRINCIPAIS
# ===============================
@app.route('/')
@login_required
def index():
    # Verificar is_admin da sessão ou do banco de dados
    is_admin = session.get('is_admin', False)
    
    # Se não estiver na sessão, verificar no banco
    if not is_admin:
        user_id = session.get('user_id')
        user = obter_usuario(user_id)
        is_admin = user.get('is_admin', False) if user else False
    
    return render_template('index.html', 
                         user_name=session.get('user_name', 'Usuário'),
                         is_admin=is_admin)

# ===============================
# ROTAS DE CREDENCIAIS GMAIL
# ===============================
@app.route('/api/gmail/credenciais', methods=['GET'])
@login_required
def obter_credenciais_gmail_route():
    """Retorna as credenciais do Gmail do usuário (se salvas)"""
    user_id = session.get('user_id')
    credenciais = obter_credenciais_gmail(user_id)
    
    if credenciais:
        return jsonify({
            'success': True,
            'gmail_email': credenciais['gmail_email'],
            'gmail_password': credenciais['gmail_password'],  # Retorna a senha descriptografada
            'has_password': True
        })
    else:
        return jsonify({
            'success': True,
            'gmail_email': None,
            'gmail_password': None,
            'has_password': False
        })

@app.route('/api/gmail/credenciais', methods=['POST'])
@login_required
def salvar_credenciais_gmail_route():
    """Salva as credenciais do Gmail do usuário"""
    data = request.json
    gmail_email = data.get('gmail_email', '').strip()
    gmail_password = data.get('gmail_password', '')
    
    if not gmail_email or not gmail_password:
        return jsonify({'error': 'Email e senha do Gmail são obrigatórios'}), 400
    
    user_id = session.get('user_id')
    
    if salvar_credenciais_gmail(user_id, gmail_email, gmail_password):
        # Registrar salvamento
        registrar_atividade(
            user_id=user_id,
            action='gmail_credentials_saved',
            details={
                'gmail_account': gmail_email,
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Credenciais salvas com sucesso'
        })
    else:
        return jsonify({'error': 'Erro ao salvar credenciais'}), 500

@app.route('/api/gmail/credenciais', methods=['DELETE'])
@login_required
def remover_credenciais_gmail_route():
    """Remove as credenciais do Gmail do usuário"""
    user_id = session.get('user_id')
    
    if remover_credenciais_gmail(user_id):
        # Registrar remoção
        registrar_atividade(
            user_id=user_id,
            action='gmail_credentials_removed',
            details={
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Credenciais removidas com sucesso'
        })
    else:
        return jsonify({'error': 'Erro ao remover credenciais'}), 500

# ===============================
# ROTAS DE ESTATÍSTICAS
# ===============================
@app.route('/api/estatisticas', methods=['GET'])
@login_required
def obter_estatisticas_route():
    """Retorna as estatísticas do usuário"""
    user_id = session.get('user_id')
    stats = obter_estatisticas_usuario(user_id)
    
    if stats:
        return jsonify({
            'success': True,
            'estatisticas': stats
        })
    else:
        return jsonify({'error': 'Erro ao obter estatísticas'}), 500

@app.route('/api/estatisticas/resetar', methods=['POST'])
@login_required
def resetar_estatisticas_route():
    """Reseta as estatísticas do usuário para zero"""
    user_id = session.get('user_id')
    
    if resetar_estatisticas_usuario(user_id):
        # Registrar reset
        registrar_atividade(
            user_id=user_id,
            action='statistics_reset',
            details={
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Estatísticas resetadas com sucesso'
        })
    else:
        return jsonify({'error': 'Erro ao resetar estatísticas'}), 500

@app.route('/api/organizar', methods=['POST'])
@login_required
def organizar():
    data = request.json
    email_usuario = data.get('email')
    senha = data.get('senha')
    excluir_inbox = data.get('excluir_inbox', True)
    user_id = session.get('user_id')
    
    # Se não foram fornecidas, tentar usar as credenciais salvas
    if not email_usuario or not senha:
        credenciais = obter_credenciais_gmail(user_id)
        if credenciais:
            email_usuario = email_usuario or credenciais['gmail_email']
            senha = senha or credenciais['gmail_password']
    
    if not email_usuario or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Registrar início da organização
    registrar_atividade(
        user_id=user_id,
        action='email_organization_started',
        details={
            'gmail_account': email_usuario,
            'excluir_inbox': excluir_inbox,
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    # Executa em thread separada e envia progresso via WebSocket
    thread = threading.Thread(
        target=processar_organizacao,
        args=(email_usuario, senha, excluir_inbox, request.sid if hasattr(request, 'sid') else None, user_id)
    )
    thread.start()
    
    return jsonify({'message': 'Organização iniciada'}), 202

@app.route('/api/verificar-duplicatas', methods=['POST'])
@login_required
def verificar_duplicatas_route():
    data = request.json
    email_usuario = data.get('email')
    senha = data.get('senha')
    
    user_id = session.get('user_id')
    
    # Se não foram fornecidas, tentar usar as credenciais salvas
    if not email_usuario or not senha:
        credenciais = obter_credenciais_gmail(user_id)
        if credenciais:
            email_usuario = email_usuario or credenciais['gmail_email']
            senha = senha or credenciais['gmail_password']
    
    if not email_usuario or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Registra início da verificação
    registrar_atividade(
        user_id=user_id,
        action='duplicate_check_started',
        details={
            'gmail_account': email_usuario,
            'timestamp': datetime.datetime.now().isoformat()
        }
    )
    
    thread = threading.Thread(
        target=processar_duplicatas,
        args=(email_usuario, senha, user_id)
    )
    thread.start()
    
    return jsonify({'message': 'Verificação iniciada'}), 202

@app.route('/api/logs')
@login_required
def get_logs():
    return jsonify({'logs': execucoes_logs[-100:]})

@app.route('/api/limpar-logs', methods=['POST'])
@login_required
def limpar_logs():
    global execucoes_logs
    execucoes_logs = []
    return jsonify({'message': 'Logs limpos'}), 200

# ===============================
# PROCESSAMENTO VIA WEBSOCKET
# ===============================
def processar_organizacao(email_usuario, senha, excluir_inbox, sid=None, user_id=None):
    logs = []
    emails_organizados = 0
    categorias_criadas = []
    
    def adicionar_log(mensagem):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        logs.append(log_completo)
        execucoes_logs.append(log_completo)
        emit_evento('log', {'message': log_completo})
        print(f"LOG EMITIDO: {log_completo}")  # Debug
        return log_completo
    
    def atualizar_progresso(progresso, texto):
        emit_evento('progresso', {'progresso': progresso, 'texto': texto})
        print(f"PROGRESSO: {progresso*100}% - {texto}")  # Debug
    
    try:
        adicionar_log("🚀 ===== INICIANDO ORGANIZAÇÃO =====")
        
        # Conecta com timeout
        atualizar_progresso(0.05, "🔌 Conectando...")
        try:
            imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
        except Exception as e:
            adicionar_log(str(e))
            emit_evento('erro', {'message': str(e)})
            atualizar_progresso(0, "❌ Erro na conexão")
            return
        
        # Lista emails com timeout e recuperação
        atualizar_progresso(0.1, "📥 Listando e-mails...")
        try:
            emails = listar_emails(imap, log_callback=adicionar_log, progress_callback=lambda p, t: atualizar_progresso(0.1 + p * 0.2, t))
        except Exception as e:
            adicionar_log(f"❌ Erro ao listar e-mails: {str(e)}")
            try:
                imap.logout()
            except:
                pass
            emit_evento('erro', {'message': f"Erro ao listar e-mails: {str(e)}"})
            atualizar_progresso(0, "❌ Erro")
            return
        
        total = len(emails)
        if not total:
            adicionar_log("⚠️ Nenhum e-mail encontrado")
            try:
                imap.logout()
            except:
                pass
            atualizar_progresso(1.0, "Concluído")
            emit_evento('conclusao', {'total': 0, 'categorias': {}})
            return
        
        # Organiza com tratamento de erro individual
        adicionar_log(f"📊 Organizando {total} e-mails...")
        categorias_count = {}
        emails_movidos = 0
        emails_com_erro = 0
        
        for i, e in enumerate(emails, 1):
            try:
                categoria = classificar_email(e["assunto"], e["corpo"])
                categorias_count[categoria] = categorias_count.get(categoria, 0) + 1
                
                # Rastreia categorias criadas
                if categoria not in categorias_criadas:
                    categorias_criadas.append(categoria)
                
                sucesso = mover_email(imap, e["id"], categoria, log_callback=adicionar_log)
                if sucesso:
                    emails_movidos += 1
                    emails_organizados += 1
                else:
                    emails_com_erro += 1
                
                progresso = 0.3 + (i / total) * 0.5
                atualizar_progresso(progresso, f"Organizando: {i}/{total}")
                
                adicionar_log(f"📨 ({i}/{total}) {e['assunto'][:50]} → {categoria}")
                
                # Keepalive a cada 100 emails
                if i % 100 == 0:
                    try:
                        imap.noop()  # Mantém conexão ativa
                        adicionar_log(f"🔄 Conexão mantida ativa ({i}/{total})")
                    except:
                        adicionar_log(f"⚠️ Reconectando ao servidor...")
                        try:
                            imap.logout()
                        except:
                            pass
                        imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
                        
            except Exception as e:
                emails_com_erro += 1
                adicionar_log(f"⚠️ Erro ao processar e-mail {i}: {str(e)[:100]}")
                continue
        
        if emails_com_erro > 0:
            adicionar_log(f"⚠️ {emails_com_erro} e-mails com erro")
        
        # Finaliza
        if excluir_inbox:
            try:
                adicionar_log("🗑️ Removendo da INBOX...")
                imap.expunge()
            except Exception as e:
                adicionar_log(f"⚠️ Erro ao limpar INBOX: {str(e)[:100]}")
        
        # Duplicatas com timeout
        try:
            atualizar_progresso(0.85, "🔍 Verificando duplicatas...")
            duplicatas = verificar_e_remover_duplicatas(
                imap,
                log_callback=adicionar_log,
                progress_callback=lambda p, t: atualizar_progresso(0.85 + p * 0.15, t)
            )
        except Exception as e:
            adicionar_log(f"⚠️ Erro ao verificar duplicatas: {str(e)[:100]}")
            duplicatas = 0
        
        # Fecha conexão de forma segura
        try:
            imap.logout()
            adicionar_log("🔌 Conexão fechada")
        except:
            pass
        
        # Registra a conclusão da organização
        if user_id:
            registrar_atividade(
                user_id=user_id,
                action='email_organization_completed',
                details={
                    'gmail_account': email_usuario,
                    'total_emails': total,
                    'emails_organizados': emails_organizados,
                    'emails_com_erro': emails_com_erro,
                    'categorias_criadas': categorias_criadas,
                    'categorias_count': categorias_count,
                    'duplicatas_removidas': duplicatas,
                    'excluiu_inbox': excluir_inbox,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            # Atualiza estatísticas do usuário
            atualizar_estatisticas_usuario(
                user_id=user_id,
                emails_organizados=emails_organizados,
                duplicatas_removidas=duplicatas,
                categorias_criadas=len(categorias_criadas),
                incrementar=True
            )
            
        adicionar_log(f"✅ Organização concluída! {emails_movidos}/{total} e-mails processados")
        atualizar_progresso(1.0, "✅ Concluído!")
        
        emit_evento('conclusao', {
            'total': emails_movidos,
            'categorias': categorias_count,
            'duplicatas': duplicatas
        })
        
    except Exception as e:
        error_msg = str(e)
        adicionar_log(f"❌ Erro: {error_msg}")
        emit_evento('erro', {'message': error_msg})
        
        # Registra o erro
        if user_id:
            registrar_atividade(
                user_id=user_id,
                action='email_organization_failed',
                details={
                    'gmail_account': email_usuario,
                    'error': error_msg,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )

def processar_duplicatas(email_usuario, senha, user_id=None):
    logs = []
    
    def adicionar_log(mensagem):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        logs.append(log_completo)
        execucoes_logs.append(log_completo)
        emit_evento('log', {'message': log_completo})
        print(f"LOG EMITIDO: {log_completo}")  # Debug
        return log_completo
    
    def atualizar_progresso(progresso, texto):
        emit_evento('progresso', {'progresso': progresso, 'texto': texto})
        print(f"PROGRESSO: {progresso*100}% - {texto}")  # Debug
    
    try:
        adicionar_log("🔍 ===== VERIFICANDO DUPLICATAS =====")
        
        try:
            imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
        except Exception as e:
            adicionar_log(str(e))
            emit_evento('erro', {'message': str(e)})
            atualizar_progresso(0, "❌ Erro na conexão")
            return
        
        try:
            duplicatas = verificar_e_remover_duplicatas(
                imap,
                log_callback=adicionar_log,
                progress_callback=atualizar_progresso
            )
        except Exception as e:
            adicionar_log(f"❌ Erro ao verificar duplicatas: {str(e)}")
            duplicatas = 0
        
        try:
            imap.logout()
            adicionar_log("🔌 Conexão fechada")
        except:
            pass
        
        # Registra a conclusão da verificação
        if user_id:
            registrar_atividade(
                user_id=user_id,
                action='duplicate_check_completed',
                details={
                    'gmail_account': email_usuario,
                    'duplicatas_encontradas': duplicatas,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            # Atualiza estatísticas do usuário
            atualizar_estatisticas_usuario(
                user_id=user_id,
                emails_organizados=0,
                duplicatas_removidas=duplicatas,
                categorias_criadas=0,
                incrementar=True
            )
        
        atualizar_progresso(1.0, "✅ Concluído!")
        emit_evento('duplicatas_resultado', {'duplicatas': duplicatas})
        
    except Exception as e:
        error_msg = str(e)
        adicionar_log(f"❌ Erro crítico: {error_msg}")
        atualizar_progresso(0, "❌ Erro")
        emit_evento('erro', {'message': error_msg})
        
        # Registra o erro
        if user_id:
            registrar_atividade(
                user_id=user_id,
                action='duplicate_check_failed',
                details={
                    'gmail_account': email_usuario,
                    'error': error_msg,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
        
        try:
            if 'imap' in locals():
                imap.logout()
        except:
            pass

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    socketio.run(app, debug=debug, host='0.0.0.0', port=port)


