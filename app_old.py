from flask import Flask, render_template, request, jsonify, session, Response
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

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# ===============================
# CONFIGURAÇÕES
# ===============================
SERVIDOR_IMAP = "imap.gmail.com"
LIMITE_EMAILS = 2000
INTERVALO_SEGUNDOS = 3 * 60 * 60  # 3 horas

# Armazenamento em memória (em produção, use Redis ou banco de dados)
execucoes_logs = []
agendador_ativo = False
agendador_thread = None
stop_event = threading.Event()

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
    blob = TextBlob(texto)
    sentimento = blob.sentiment.polarity
    if sentimento < -0.1:
        return "Problemas"
    elif sentimento > 0.3:
        return "Positivos"
    return "Neutros"

def conectar_email(email_usuario, senha, log_callback=None):
    if log_callback:
        log_callback(f"🔌 Iniciando conexão com {SERVIDOR_IMAP}...")
    
    imap = imaplib.IMAP4_SSL(SERVIDOR_IMAP)
    
    if log_callback:
        log_callback(f"🔐 Autenticando usuário: {email_usuario}")
    
    imap.login(email_usuario, senha)
    
    if log_callback:
        log_callback(f"✅ Conexão estabelecida com sucesso!")
    
    return imap

def listar_emails(imap, limite=LIMITE_EMAILS, log_callback=None, progress_callback=None):
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
    
    for idx, num in enumerate(ids_para_processar, 1):
        if progress_callback:
            percentual_listagem = (idx / limite_real) * 100
            progress_callback(idx / limite_real, f"Carregando e-mails: {idx}/{limite_real} ({int(percentual_listagem)}%)")
        
        if log_callback and idx % 50 == 0:
            log_callback(f"📖 Carregados {idx}/{limite_real} e-mails...")
        
        status, data = imap.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        
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
    
    if log_callback:
        log_callback(f"✅ {len(emails)} e-mails carregados com sucesso!")
    
    return emails

def mover_email(imap, email_id, categoria, log_callback=None):
    if log_callback:
        log_callback(f"📁 Criando/verificando pasta: {categoria}")
    
    imap.create(categoria)
    
    if log_callback:
        log_callback(f"📤 Copiando e-mail para: {categoria}")
    
    imap.copy(email_id, categoria)
    
    if log_callback:
        log_callback(f"🗑️ Marcando e-mail original para exclusão")
    
    imap.store(email_id, '+FLAGS', '\\Deleted')

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
    
    # Mapeia Message-IDs
    inbox_message_ids = {}
    for idx, email_id in enumerate(ids_inbox, 1):
        status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
        if status == "OK":
            msg = email.message_from_bytes(data[0][1])
            message_id = msg.get("Message-ID", "").strip()
            if message_id:
                inbox_message_ids[message_id] = email_id
        
        if progress_callback and idx % 20 == 0:
            progresso = 0.2 + (idx / len(ids_inbox)) * 0.3
            progress_callback(progresso, f"Mapeando: {idx}/{len(ids_inbox)}")
    
    if progress_callback:
        progress_callback(0.5, "Comparando pastas...")
    
    # Verifica duplicatas
    duplicatas_encontradas = set()
    
    for pasta in pastas_organizadas:
        try:
            status, _ = imap.select(f'"{pasta}"' if ' ' in pasta else pasta, readonly=True)
            if status != "OK":
                continue
            
            status, msgs_pasta = imap.search(None, "ALL")
            if status != "OK":
                continue
            
            ids_pasta = msgs_pasta[0].split()
            if not ids_pasta:
                continue
            
            for email_id in ids_pasta:
                status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
                if status == "OK":
                    msg = email.message_from_bytes(data[0][1])
                    message_id = msg.get("Message-ID", "").strip()
                    
                    if message_id in inbox_message_ids:
                        duplicatas_encontradas.add(message_id)
        
        except Exception as e:
            if log_callback:
                log_callback(f"⚠️ Erro na pasta '{pasta}': {e}")
            continue
    
    if progress_callback:
        progress_callback(0.8, f"{len(duplicatas_encontradas)} duplicatas encontradas")
    
    # Remove duplicatas
    if duplicatas_encontradas:
        if log_callback:
            log_callback(f"🗑️ Removendo {len(duplicatas_encontradas)} duplicatas...")
        
        imap.select("INBOX")
        removidos = 0
        
        for message_id in duplicatas_encontradas:
            if message_id in inbox_message_ids:
                email_id = inbox_message_ids[message_id]
                imap.store(email_id, '+FLAGS', '\\Deleted')
                removidos += 1
        
        imap.expunge()
        
        if log_callback:
            log_callback(f"✅ {removidos} duplicatas removidas")
        
        if progress_callback:
            progress_callback(1.0, f"✅ {removidos} duplicatas removidas!")
        
        return removidos
    else:
        if log_callback:
            log_callback("✅ Nenhuma duplicata encontrada")
        if progress_callback:
            progress_callback(1.0, "✅ Nenhuma duplicata")
        return 0

# ===============================
# ROTAS FLASK
# ===============================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/organizar', methods=['POST'])
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
def get_logs():
    return jsonify({'logs': execucoes_logs[-100:]})

@app.route('/api/limpar-logs', methods=['POST'])
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
        socketio.emit('log', {'message': log_completo})
        return log_completo
    
    def atualizar_progresso(progresso, texto):
        socketio.emit('progresso', {'progresso': progresso, 'texto': texto})
    
    try:
        adicionar_log("🚀 ===== INICIANDO ORGANIZAÇÃO =====")
        
        # Conecta
        atualizar_progresso(0.05, "🔌 Conectando...")
        imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
        
        # Lista emails
        atualizar_progresso(0.1, "📥 Listando e-mails...")
        emails = listar_emails(imap, log_callback=adicionar_log, progress_callback=lambda p, t: atualizar_progresso(0.1 + p * 0.2, t))
        
        total = len(emails)
        if not total:
            adicionar_log("⚠️ Nenhum e-mail encontrado")
            imap.logout()
            atualizar_progresso(1.0, "Concluído")
            socketio.emit('conclusao', {'total': 0, 'categorias': {}})
            return
        
        # Organiza
        adicionar_log(f"📊 Organizando {total} e-mails...")
        categorias_count = {}
        
        for i, e in enumerate(emails, 1):
            categoria = classificar_email(e["assunto"], e["corpo"])
            categorias_count[categoria] = categorias_count.get(categoria, 0) + 1
            
            mover_email(imap, e["id"], categoria, log_callback=adicionar_log)
            
            progresso = 0.3 + (i / total) * 0.5
            atualizar_progresso(progresso, f"Organizando: {i}/{total}")
            
            adicionar_log(f"📨 ({i}/{total}) {e['assunto'][:50]} → {categoria}")
        
        # Finaliza
        if excluir_inbox:
            adicionar_log("🗑️ Removendo da INBOX...")
            imap.expunge()
        
        # Duplicatas
        atualizar_progresso(0.85, "🔍 Verificando duplicatas...")
        duplicatas = verificar_e_remover_duplicatas(
            imap,
            log_callback=adicionar_log,
            progress_callback=lambda p, t: atualizar_progresso(0.85 + p * 0.15, t)
        )
        
        imap.logout()
        adicionar_log(f"✅ Organização concluída! {total} e-mails processados")
        atualizar_progresso(1.0, "✅ Concluído!")
        
        socketio.emit('conclusao', {
            'total': total,
            'categorias': categorias_count,
            'duplicatas': duplicatas
        })
        
    except Exception as e:
        adicionar_log(f"❌ Erro: {str(e)}")
        traceback.print_exc()
        socketio.emit('erro', {'message': str(e)})

def processar_duplicatas(email_usuario, senha):
    logs = []
    
    def adicionar_log(mensagem):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        logs.append(log_completo)
        execucoes_logs.append(log_completo)
        socketio.emit('log', {'message': log_completo})
        return log_completo
    
    def atualizar_progresso(progresso, texto):
        socketio.emit('progresso', {'progresso': progresso, 'texto': texto})
    
    try:
        adicionar_log("🔍 ===== VERIFICANDO DUPLICATAS =====")
        
        imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
        duplicatas = verificar_e_remover_duplicatas(
            imap,
            log_callback=adicionar_log,
            progress_callback=atualizar_progresso
        )
        imap.logout()
        
        socketio.emit('duplicatas_resultado', {'duplicatas': duplicatas})
        
    except Exception as e:
        adicionar_log(f"❌ Erro: {str(e)}")
        socketio.emit('erro', {'message': str(e)})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, debug=True, host='0.0.0.0', port=port)
