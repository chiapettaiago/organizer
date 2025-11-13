from flask import Flask, render_template, request, jsonify, session, Response, redirect, url_for, flash
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
INVITE_CODES = {}  # {codigo: {'created_by': username, 'created_at': datetime, 'used': False, 'used_by': None}}

def gerar_codigo_convite(username):
    """Gera um código de convite único"""
    codigo = secrets.token_urlsafe(16)[:12].upper()
    INVITE_CODES[codigo] = {
        'created_by': username,
        'created_at': datetime.datetime.now(),
        'used': False,
        'used_by': None
    }
    return codigo

def validar_codigo_convite(codigo):
    """Valida se o código existe e não foi usado"""
    codigo = codigo.upper().strip()
    if codigo in INVITE_CODES and not INVITE_CODES[codigo]['used']:
        return True
    return False

def marcar_codigo_usado(codigo, username):
    """Marca um código como usado"""
    codigo = codigo.upper().strip()
    if codigo in INVITE_CODES:
        INVITE_CODES[codigo]['used'] = True
        INVITE_CODES[codigo]['used_by'] = username
        INVITE_CODES[codigo]['used_at'] = datetime.datetime.now()
        return True
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
        
        # Verificar se tem flag is_admin na sessão ou no USERS
        is_admin_session = session.get('is_admin', False)
        user = USERS.get(session.get('user_id'))
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
        
        # Verificar credenciais
        user = USERS.get(username)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if user and user['password'] == password_hash:
            # Login bem-sucedido
            session.permanent = True
            session['user_id'] = username
            session['user_name'] = user['name']
            session['is_guest'] = False
            session['is_admin'] = user.get('is_admin', False)
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login realizado com sucesso',
                    'redirect': url_for('index')
                })
            return redirect(url_for('index'))
        else:
            # Credenciais inválidas
            if request.is_json:
                return jsonify({'error': 'Usuário ou senha inválidos'}), 401
            flash('Usuário ou senha inválidos', 'error')
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
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
    if email in USERS:
        return jsonify({'error': 'Este e-mail já está cadastrado'}), 400
    
    # Verificar se o código de convite está na sessão
    if session.get('pending_invite_code') != invite_code.upper():
        return jsonify({'error': 'Código de convite inválido'}), 400
    
    # Validar código novamente
    if not validar_codigo_convite(invite_code):
        return jsonify({'error': 'Código de convite inválido ou já utilizado'}), 400
    
    # Criar novo usuário
    password_hash = hashlib.sha256(senha.encode()).hexdigest()
    USERS[email] = {
        'password': password_hash,
        'name': nome,
        'is_admin': False,
        'created_at': datetime.datetime.now(),
        'created_via': 'invite',
        'invite_code': invite_code.upper()
    }
    
    # Marcar código como usado
    marcar_codigo_usado(invite_code, email)
    
    # Fazer login automático
    session.permanent = True
    session['user_id'] = email
    session['user_name'] = nome
    session['is_guest'] = False
    session['is_admin'] = False
    
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
    return render_template('admin_convites.html', 
                         user_name=session.get('user_name', 'Admin'),
                         convites=INVITE_CODES)

@app.route('/api/admin/gerar-convite', methods=['POST'])
@admin_required
def gerar_convite():
    """Gera um novo código de convite"""
    try:
        codigo = gerar_codigo_convite(session.get('user_id'))
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
    convites = []
    for codigo, info in INVITE_CODES.items():
        convites.append({
            'codigo': codigo,
            'criado_por': info['created_by'],
            'criado_em': info['created_at'].strftime('%d/%m/%Y %H:%M'),
            'usado': info['used'],
            'usado_por': info.get('used_by'),
            'usado_em': info.get('used_at').strftime('%d/%m/%Y %H:%M') if info.get('used_at') else None
        })
    
    # Ordenar por data de criação (mais recentes primeiro)
    convites.sort(key=lambda x: INVITE_CODES[x['codigo']]['created_at'], reverse=True)
    
    return jsonify({
        'success': True,
        'convites': convites,
        'total': len(convites),
        'usados': sum(1 for c in INVITE_CODES.values() if c['used']),
        'disponiveis': sum(1 for c in INVITE_CODES.values() if not c['used'])
    })

@app.route('/api/admin/revogar-convite/<codigo>', methods=['DELETE'])
@admin_required
def revogar_convite(codigo):
    """Revoga (remove) um código de convite"""
    codigo = codigo.upper().strip()
    if codigo in INVITE_CODES:
        del INVITE_CODES[codigo]
        return jsonify({
            'success': True,
            'message': f'Código {codigo} revogado com sucesso'
        })
    else:
        return jsonify({'error': 'Código não encontrado'}), 404

# ===============================
# ROTAS PRINCIPAIS
# ===============================
@app.route('/')
@login_required
def index():
    # Verificar is_admin da sessão ou do usuário no USERS
    is_admin = session.get('is_admin', False)
    
    # Se não estiver na sessão, verificar no USERS
    if not is_admin:
        user_id = session.get('user_id')
        user = USERS.get(user_id) if user_id in USERS else None
        is_admin = user.get('is_admin', False) if user else False
    
    return render_template('index.html', 
                         user_name=session.get('user_name', 'Usuário'),
                         is_admin=is_admin)

@app.route('/api/organizar', methods=['POST'])
@login_required
def organizar():
    data = request.json
    email_usuario = data.get('email')
    senha = data.get('senha')
    excluir_inbox = data.get('excluir_inbox', True)
    
    if not email_usuario or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    # Executa em thread separada e envia progresso via WebSocket
    thread = threading.Thread(
        target=processar_organizacao,
        args=(email_usuario, senha, excluir_inbox, request.sid if hasattr(request, 'sid') else None)
    )
    thread.start()
    
    return jsonify({'message': 'Organização iniciada'}), 202

@app.route('/api/verificar-duplicatas', methods=['POST'])
@login_required
def verificar_duplicatas_route():
    data = request.json
    email_usuario = data.get('email')
    senha = data.get('senha')
    
    if not email_usuario or not senha:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    thread = threading.Thread(
        target=processar_duplicatas,
        args=(email_usuario, senha)
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
def processar_organizacao(email_usuario, senha, excluir_inbox, sid=None):
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
                
                sucesso = mover_email(imap, e["id"], categoria, log_callback=adicionar_log)
                if sucesso:
                    emails_movidos += 1
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

def processar_duplicatas(email_usuario, senha):
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
        
        atualizar_progresso(1.0, "✅ Concluído!")
        emit_evento('duplicatas_resultado', {'duplicatas': duplicatas})
        
    except Exception as e:
        error_msg = str(e)
        adicionar_log(f"❌ Erro crítico: {error_msg}")
        atualizar_progresso(0, "❌ Erro")
        emit_evento('erro', {'message': error_msg})
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


