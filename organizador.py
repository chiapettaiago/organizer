import imaplib
import email
from email.header import decode_header
import re
from textblob import TextBlob
import streamlit as st
import time
import datetime
import threading
import traceback

# ===============================
# CONFIGURAÇÕES
# ===============================
SERVIDOR_IMAP = "imap.gmail.com"
LIMITE_EMAILS = 2000
INTERVALO_SEGUNDOS = 3 * 60 * 60  # 3 horas

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
        # Atualiza progresso da listagem
        if progress_callback:
            percentual_listagem = (idx / limite_real) * 100
            progress_callback(idx / limite_real, f"Carregando e-mails: {idx}/{limite_real} ({int(percentual_listagem)}%)")
        
        if log_callback and idx % 50 == 0:
            log_callback(f"📖 Carregados {idx}/{limite_real} e-mails...")
        
        status, data = imap.fetch(num, "(RFC822)")
        if status != "OK":
            if log_callback and idx % 100 == 0:
                log_callback(f"⚠️ Erro ao buscar e-mail ID {num.decode()}")
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

def verificar_e_remover_duplicatas(imap, log_callback=None, progress_callback=None, status_callback=None):
    """
    Verifica se há e-mails duplicados entre INBOX e outras pastas.
    Remove da INBOX os e-mails que já existem em pastas organizadas.
    """
    if log_callback:
        log_callback("\n" + "=" * 50)
        log_callback("🔍 VERIFICANDO DUPLICATAS")
        log_callback("=" * 50)
    
    if status_callback:
        status_callback("🔍 **Fase 1/5:** Listando pastas do Gmail...")
    
    # Lista todas as pastas
    if log_callback:
        log_callback("📂 Listando todas as pastas do Gmail...")
    
    status, pastas = imap.list()
    if status != "OK":
        if log_callback:
            log_callback("❌ Erro ao listar pastas")
        return 0
    
    # Filtra apenas pastas organizadas (exclui INBOX e pastas do sistema)
    pastas_organizadas = []
    for pasta in pastas:
        pasta_nome = pasta.decode().split('"/"')[-1].strip(' "')
        # Ignora INBOX e pastas do sistema do Gmail
        if pasta_nome not in ['INBOX', '[Gmail]'] and not pasta_nome.startswith('[Gmail]/'):
            pastas_organizadas.append(pasta_nome)
    
    if log_callback:
        log_callback(f"📁 Pastas organizadas encontradas: {len(pastas_organizadas)}")
        for p in pastas_organizadas[:10]:  # Mostra até 10 primeiras
            log_callback(f"   - {p}")
    
    if progress_callback:
        progress_callback(0.1, "📂 Pastas listadas")
    
    # Obtém IDs dos e-mails na INBOX
    if status_callback:
        status_callback("🔍 **Fase 2/5:** Analisando caixa de entrada...")
    
    imap.select("INBOX")
    status, msgs_inbox = imap.search(None, "ALL")
    if status != "OK":
        if log_callback:
            log_callback("❌ Erro ao buscar e-mails da INBOX")
        return 0
    
    ids_inbox = msgs_inbox[0].split()
    if not ids_inbox:
        if log_callback:
            log_callback("📭 INBOX vazia - nada a verificar")
        if progress_callback:
            progress_callback(1.0, "✅ INBOX vazia")
        return 0
    
    total_inbox = len(ids_inbox)
    
    # Limita a 1000 e-mails mais recentes para verificação
    LIMITE_VERIFICACAO = 1000
    if total_inbox > LIMITE_VERIFICACAO:
        ids_inbox = ids_inbox[-LIMITE_VERIFICACAO:]  # Pega os últimos 1000
        if log_callback:
            log_callback(f"⚠️ INBOX possui {total_inbox} e-mails")
            log_callback(f"� Verificando apenas os últimos {LIMITE_VERIFICACAO} e-mails mais recentes")
    
    if log_callback:
        log_callback(f"�📧 E-mails a verificar: {len(ids_inbox)}")
    
    if progress_callback:
        progress_callback(0.2, f"📧 {len(ids_inbox)} e-mails selecionados")
    
    # Cria um conjunto de Message-IDs únicos da INBOX
    if status_callback:
        status_callback("🔍 **Fase 3/5:** Mapeando Message-IDs da INBOX...")
    
    if log_callback:
        log_callback("🔑 Extraindo Message-IDs da INBOX...")
    
    inbox_message_ids = {}
    total_inbox = len(ids_inbox)
    
    for idx, email_id in enumerate(ids_inbox, 1):
        status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
        if status == "OK":
            msg = email.message_from_bytes(data[0][1])
            message_id = msg.get("Message-ID", "").strip()
            if message_id:
                inbox_message_ids[message_id] = email_id
        
        # Atualiza progresso
        if progress_callback and idx % 20 == 0:
            progresso = 0.2 + (idx / total_inbox) * 0.2  # 20% a 40%
            progress_callback(progresso, f"🔑 Mapeando INBOX: {idx}/{total_inbox}")
        
        if log_callback and idx % 100 == 0:
            log_callback(f"   Processados: {idx}/{total_inbox} e-mails")
    
    if log_callback:
        log_callback(f"🔑 Message-IDs únicos na INBOX: {len(inbox_message_ids)}")
    
    if progress_callback:
        progress_callback(0.4, f"🔑 {len(inbox_message_ids)} IDs mapeados")
    
    # Verifica duplicatas em cada pasta organizada
    if status_callback:
        status_callback("🔍 **Fase 4/5:** Comparando com pastas organizadas...")
    
    if log_callback:
        log_callback(f"\n🔍 Verificando duplicatas em {len(pastas_organizadas)} pastas...")
    
    duplicatas_encontradas = set()
    total_pastas = len(pastas_organizadas)
    
    for idx_pasta, pasta in enumerate(pastas_organizadas, 1):
        try:
            if log_callback:
                log_callback(f"\n📁 Verificando pasta [{idx_pasta}/{total_pastas}]: {pasta}")
            
            status, _ = imap.select(f'"{pasta}"' if ' ' in pasta else pasta, readonly=True)
            if status != "OK":
                if log_callback:
                    log_callback(f"   ⚠️ Não foi possível acessar a pasta")
                continue
            
            status, msgs_pasta = imap.search(None, "ALL")
            if status != "OK":
                continue
            
            ids_pasta = msgs_pasta[0].split()
            if not ids_pasta:
                if log_callback:
                    log_callback(f"   📭 Pasta vazia")
                continue
            
            if log_callback:
                log_callback(f"   📊 {len(ids_pasta)} e-mails nesta pasta")
            
            # Verifica cada e-mail da pasta
            duplicatas_nesta_pasta = 0
            for idx_email, email_id in enumerate(ids_pasta, 1):
                status, data = imap.fetch(email_id, "(BODY[HEADER.FIELDS (MESSAGE-ID)])")
                if status == "OK":
                    msg = email.message_from_bytes(data[0][1])
                    message_id = msg.get("Message-ID", "").strip()
                    
                    # Se este Message-ID existe na INBOX, é uma duplicata
                    if message_id in inbox_message_ids:
                        duplicatas_encontradas.add(message_id)
                        duplicatas_nesta_pasta += 1
                
                # Atualiza progresso dentro da pasta
                if progress_callback and len(ids_pasta) > 50 and idx_email % 25 == 0:
                    progresso_pasta = 0.4 + ((idx_pasta - 1) / total_pastas) * 0.3 + (idx_email / len(ids_pasta)) * (0.3 / total_pastas)
                    progress_callback(progresso_pasta, f"🔍 Verificando {pasta[:30]}... ({idx_email}/{len(ids_pasta)})")
            
            if log_callback:
                if duplicatas_nesta_pasta > 0:
                    log_callback(f"   🔄 {duplicatas_nesta_pasta} duplicata(s) encontrada(s) nesta pasta")
                else:
                    log_callback(f"   ✅ Nenhuma duplicata nesta pasta")
            
            # Atualiza progresso entre pastas
            if progress_callback:
                progresso = 0.4 + (idx_pasta / total_pastas) * 0.3  # 40% a 70%
                progress_callback(progresso, f"📁 Verificadas: {idx_pasta}/{total_pastas} pastas")
        
        except Exception as e:
            if log_callback:
                log_callback(f"   ⚠️ Erro ao verificar pasta '{pasta}': {e}")
            continue
    
    if progress_callback:
        progress_callback(0.7, f"✅ Verificação completa")
    
    # Remove duplicatas da INBOX
    if duplicatas_encontradas:
        if status_callback:
            status_callback(f"🗑️ **Fase 5/5:** Removendo {len(duplicatas_encontradas)} duplicatas...")
        
        if log_callback:
            log_callback(f"\n🗑️ Removendo {len(duplicatas_encontradas)} duplicatas da INBOX...")
        
        imap.select("INBOX")
        removidos = 0
        total_duplicatas = len(duplicatas_encontradas)
        
        for idx, message_id in enumerate(duplicatas_encontradas, 1):
            if message_id in inbox_message_ids:
                email_id = inbox_message_ids[message_id]
                imap.store(email_id, '+FLAGS', '\\Deleted')
                removidos += 1
                
                # Atualiza progresso
                if progress_callback:
                    progresso = 0.7 + (idx / total_duplicatas) * 0.25  # 70% a 95%
                    progress_callback(progresso, f"🗑️ Removendo: {idx}/{total_duplicatas}")
                
                if log_callback and idx % 10 == 0:
                    log_callback(f"   Removidos: {idx}/{total_duplicatas}")
        
        if log_callback:
            log_callback(f"🗑️ Expurgando e-mails marcados para exclusão...")
        
        imap.expunge()
        
        if log_callback:
            log_callback(f"✅ {removidos} e-mails duplicados removidos da INBOX")
        
        if progress_callback:
            progress_callback(1.0, f"✅ {removidos} duplicatas removidas!")
        
        return removidos
    else:
        if log_callback:
            log_callback("\n✅ Nenhuma duplicata encontrada - INBOX está limpa")
        
        if progress_callback:
            progress_callback(1.0, "✅ Nenhuma duplicata encontrada")
        
        if status_callback:
            status_callback("✅ **Concluído:** Nenhuma duplicata encontrada")
        
        return 0

# ===============================
# ORGANIZAÇÃO DE E-MAILS (com feedback em tempo real)
# ===============================
def organizar_emails(email_usuario, senha, progress_container, log_container, status_container=None, excluir_da_inbox=True):
    logs = []
    categorias_count = {}
    
    def adicionar_log(mensagem):
        """Adiciona log e atualiza interface"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        logs.append(log_completo)
        # Removido print para não poluir o terminal
        return log_completo
    
    def atualizar_logs_tela():
        """Atualiza logs na tela"""
        if log_container:
            ultimos_logs = "\n".join(logs[-15:])  # Mostra últimos 15 logs
            log_container.text_area(
                "Log do Processo:",
                value=ultimos_logs,
                height=350,
                key=f"log_live_{len(logs)}"
            )
    
    try:
        adicionar_log("🚀 ===== INICIANDO ORGANIZAÇÃO DE E-MAILS =====")
        atualizar_logs_tela()
        
        # Fase 1: Conexão
        if status_container:
            status_container.info("🔌 **Fase 1/4:** Conectando ao Gmail...")
        
        imap = conectar_email(email_usuario, senha, log_callback=adicionar_log)
        atualizar_logs_tela()
        
        # Fase 2: Listagem
        if status_container:
            status_container.info("📥 **Fase 2/4:** Listando e-mails da caixa de entrada...")
        
        adicionar_log("=" * 50)
        adicionar_log("📥 FASE DE LISTAGEM DE E-MAILS")
        adicionar_log("=" * 50)
        atualizar_logs_tela()
        
        def progress_listagem(progresso, texto):
            if progress_container:
                progress_container.progress(progresso * 0.3, text=f"� {texto}")  # 30% do total
        
        emails = listar_emails(
            imap, 
            log_callback=adicionar_log,
            progress_callback=progress_listagem
        )
        
        atualizar_logs_tela()
        total = len(emails)
        
        if not total:
            adicionar_log("⚠️ Nenhum e-mail encontrado para organizar.")
            imap.logout()
            adicionar_log("🔌 Desconectado do servidor.")
            
            if progress_container:
                progress_container.progress(0.0, text="Nenhum e-mail para organizar")
            if status_container:
                status_container.warning("⚠️ Nenhum e-mail encontrado na caixa de entrada.")
            
            atualizar_logs_tela()
            return logs

        # Fase 3: Classificação e Organização
        adicionar_log("=" * 50)
        adicionar_log(f"🏷️ FASE DE CLASSIFICAÇÃO E ORGANIZAÇÃO ({total} e-mails)")
        adicionar_log("=" * 50)
        atualizar_logs_tela()
        
        if status_container:
            status_container.info(f"🏷️ **Fase 3/4:** Classificando e organizando {total} e-mails...")
        
        # Ícones das categorias
        icones = {
            "Faturas": "💰",
            "Trabalho": "💼",
            "Pessoal": "👤",
            "Marketing": "📢",
            "Sistema": "⚙️",
            "Problemas": "⚠️",
            "Positivos": "😊",
            "Neutros": "📄"
        }
        
        for i, e in enumerate(emails, 1):
            # Classifica o email
            adicionar_log(f"\n📧 E-mail {i}/{total}: {e['assunto'][:70]}...")
            
            categoria = classificar_email(e["assunto"], e["corpo"])
            icone = icones.get(categoria, "📧")
            
            adicionar_log(f"   🏷️ Categoria identificada: {icone} {categoria}")
            
            # Contabiliza categorias
            categorias_count[categoria] = categorias_count.get(categoria, 0) + 1
            
            # Move o email com logs detalhados
            def log_movimento(msg):
                adicionar_log(f"   {msg}")
            
            mover_email(imap, e["id"], categoria, log_callback=log_movimento)
            adicionar_log(f"   ✅ E-mail organizado com sucesso!")
            
            # Atualiza progresso (30% listagem + 65% organização)
            progresso_organizacao = 0.3 + (i / total) * 0.65
            percentual = int((i / total) * 100)
            
            if progress_container:
                texto_progresso = f"Organizando: {i}/{total} ({percentual}%) - {icone} {categoria}"
                progress_container.progress(progresso_organizacao, text=texto_progresso)
            
            # Atualiza status visual
            if status_container:
                status_html = f"""
                <div style="padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            color: white; border-radius: 10px; margin: 10px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h4 style="margin: 0 0 10px 0;">🔄 Processando E-mail {i}/{total}</h4>
                    <p style="margin: 5px 0;"><strong>📧 Assunto:</strong> {e['assunto'][:80]}...</p>
                    <p style="margin: 5px 0;"><strong>{icone} Categoria:</strong> {categoria}</p>
                    <p style="margin: 5px 0;"><strong>📊 Progresso:</strong> {percentual}% concluído</p>
                </div>
                """
                status_container.markdown(status_html, unsafe_allow_html=True)
            
            # Atualiza logs na tela a cada 3 emails
            if i % 3 == 0 or i == total:
                atualizar_logs_tela()
            
            time.sleep(0.02)  # Pequeno delay para visualização
        
        # Fase 4: Finalização
        adicionar_log("\n" + "=" * 50)
        adicionar_log("🧹 FASE DE FINALIZAÇÃO")
        adicionar_log("=" * 50)
        atualizar_logs_tela()
        
        if status_container:
            status_container.info("🧹 **Fase 4/5:** Finalizando e limpando...")
        
        if excluir_da_inbox:
            adicionar_log("🗑️ Removendo e-mails da caixa de entrada (INBOX)...")
            imap.expunge()
            adicionar_log("✅ E-mails excluídos da INBOX com sucesso")
        else:
            adicionar_log("📋 E-mails mantidos na INBOX (cópias criadas nas pastas)")
            adicionar_log("ℹ️ Para excluir da INBOX, marque a opção antes de executar")
        
        # Fase 5: Verificação de duplicatas
        if status_container:
            status_container.info("🔍 **Fase 5/5:** Verificando e removendo duplicatas...")
        
        atualizar_logs_tela()
        
        def progress_duplicatas(progresso, texto):
            if progress_container:
                progress_container.progress(progresso, text=f"🔍 {texto}")
        
        duplicatas_removidas = verificar_e_remover_duplicatas(
            imap, 
            log_callback=adicionar_log,
            progress_callback=progress_duplicatas,
            status_callback=status_container.info if status_container else None
        )
        
        atualizar_logs_tela()
        
        if duplicatas_removidas > 0:
            adicionar_log(f"🎯 Total de duplicatas removidas: {duplicatas_removidas}")
        
        adicionar_log("\n🔌 Desconectando do servidor Gmail...")
        imap.logout()
        adicionar_log("✅ Desconexão realizada com sucesso")
        
        # Estatísticas finais
        adicionar_log("\n" + "=" * 50)
        adicionar_log("📊 RELATÓRIO FINAL")
        adicionar_log("=" * 50)
        adicionar_log(f"✅ Organização concluída às {datetime.datetime.now():%H:%M:%S}")
        adicionar_log(f"� Total de e-mails processados: {total}")
        adicionar_log(f"📁 Categorias utilizadas: {len(categorias_count)}")
        adicionar_log("\n📊 Distribuição por categoria:")
        
        for cat, count in sorted(categorias_count.items(), key=lambda x: x[1], reverse=True):
            icone = icones.get(cat, "📧")
            percentual_cat = (count / total) * 100
            adicionar_log(f"   {icone} {cat}: {count} e-mails ({percentual_cat:.1f}%)")
        
        adicionar_log("=" * 50)
        adicionar_log("🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
        adicionar_log("=" * 50)
        
        # Atualiza interface final
        if progress_container:
            progress_container.progress(1.0, text=f"✅ Concluído! {total} e-mails organizados")
        
        if status_container:
            # Resumo final colorido
            resumo = """
            <div style="padding: 20px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                        color: white; border-radius: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.2);">
                <h3 style="margin: 0 0 15px 0;">✅ Organização Concluída com Sucesso!</h3>
            """
            resumo += f"<p style='font-size: 18px; margin: 10px 0;'><strong>📧 Total:</strong> {total} e-mails organizados</p>"
            resumo += "<p style='font-size: 16px; margin: 10px 0;'><strong>📁 Distribuição:</strong></p><ul style='margin: 10px 0;'>"
            
            for cat, count in sorted(categorias_count.items(), key=lambda x: x[1], reverse=True):
                icone = icones.get(cat, "📧")
                percentual_cat = (count / total) * 100
                resumo += f"<li style='margin: 5px 0;'>{icone} <strong>{cat}:</strong> {count} e-mails ({percentual_cat:.1f}%)</li>"
            
            resumo += "</ul></div>"
            status_container.markdown(resumo, unsafe_allow_html=True)
        
        atualizar_logs_tela()
            
    except Exception as e:
        adicionar_log(f"\n❌ ===== ERRO DURANTE A EXECUÇÃO =====")
        adicionar_log(f"❌ Erro: {str(e)}")
        adicionar_log(f"❌ Tipo: {type(e).__name__}")
        traceback.print_exc()
        
        if log_container:
            log_container.error(f"❌ Erro durante a organização: {e}")
        if status_container:
            status_container.error(f"❌ Erro: {e}\n\nVerifique os logs para mais detalhes.")
        
        atualizar_logs_tela()
    
    return logs

# ===============================
# LOOP AUTOMÁTICO EM THREAD
# ===============================
def agendador(email_usuario, senha, stop_event):
    """
    Executa a organização de emails em background.
    Nota: Esta função roda em uma thread separada, sem ScriptRunContext do Streamlit.
    Os logs são armazenados mas não são exibidos em tempo real durante a execução agendada.
    """
    while not stop_event.is_set():
        # Marca início da execução
        inicio = datetime.datetime.now()
        
        # Executa organização SEM containers do Streamlit (para evitar warnings)
        # Os logs serão salvos mas não exibidos em tempo real
        novos_logs = organizar_emails(email_usuario, senha, None, None, None)
        
        # Salva informações da execução (sem usar st.session_state que causa warnings)
        # Os dados serão atualizados quando o usuário interagir com a interface
        
        # Aguarda próxima execução
        proxima = inicio + datetime.timedelta(seconds=INTERVALO_SEGUNDOS)
        
        while datetime.datetime.now() < proxima:
            if stop_event.is_set():
                break
            time.sleep(1)

# ===============================
# INTERFACE STREAMLIT
# ===============================
def main():
    st.set_page_config(
        page_title="MailNest",
        page_icon="📬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS customizado para aparência profissional
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            color: #666;
            font-size: 1.1rem;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
        }
        
        /* Responsividade para Mobile */
        @media (max-width: 768px) {
            .main-header {
                font-size: 1.8rem;
            }
            .subtitle {
                font-size: 0.9rem;
            }
            .stButton>button {
                font-size: 0.85rem;
                padding: 0.5rem 1rem;
            }
            div[data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.2rem;
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.8rem;
            }
        }
        
        /* Responsividade para Tablets */
        @media (min-width: 769px) and (max-width: 1024px) {
            .main-header {
                font-size: 2rem;
            }
            .subtitle {
                font-size: 1rem;
            }
            div[data-testid="stSidebar"] {
                min-width: 250px;
            }
        }
        
        /* Responsividade para Desktop */
        @media (min-width: 1025px) {
            .main-header {
                font-size: 2.5rem;
            }
            div[data-testid="stSidebar"] {
                min-width: 300px;
            }
        }
        
        /* Ajustes gerais de responsividade */
        .element-container {
            width: 100%;
        }
        
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea {
            font-size: 1rem;
        }
        
        @media (max-width: 640px) {
            .stTextInput>div>div>input,
            .stTextArea>div>div>textarea {
                font-size: 0.9rem;
            }
            
            /* Stack das colunas em mobile */
            [data-testid="column"] {
                width: 100% !important;
                flex-basis: 100% !important;
            }
            
            /* Ajusta tabs para mobile */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }
            
            .stTabs [data-baseweb="tab"] {
                font-size: 0.85rem;
                padding: 0.5rem 0.75rem;
            }
        }
        
        /* Container fluido */
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }
        
        @media (min-width: 768px) {
            .block-container {
                padding-left: 2rem;
                padding-right: 2rem;
            }
        }
        
        /* Ajustes para textarea de logs */
        .stTextArea textarea {
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        @media (max-width: 768px) {
            .stTextArea textarea {
                font-size: 0.75rem;
                line-height: 1.3;
            }
        }
        
        /* Melhora exibição em telas pequenas */
        @media (max-width: 480px) {
            .main-header {
                font-size: 1.5rem;
            }
            .subtitle {
                font-size: 0.85rem;
            }
            h2, h3 {
                font-size: 1.2rem;
            }
            .stMarkdown {
                font-size: 0.9rem;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown('<h1 class="main-header">📬 MailNest</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Organize seus e-mails automaticamente com inteligência artificial</p>', unsafe_allow_html=True)
    
    # Sidebar com configurações
    with st.sidebar:
        st.markdown("### ⚙️ Configurações")
        st.markdown("---")
        
        # Credenciais
        st.markdown("#### 🔐 Credenciais Gmail")
        email_usuario = st.text_input(
            "E-mail",
            placeholder="seuemail@gmail.com",
            help="Seu endereço de e-mail do Gmail"
        )
        senha = st.text_input(
            "Senha de aplicativo",
            type="password",
            help="Gere uma senha de aplicativo em: https://myaccount.google.com/apppasswords"
        )
        
        st.markdown("---")
        
        # Opções de organização
        st.markdown("#### 🎛️ Opções de Organização")
        
        excluir_inbox = st.checkbox(
            "Remover da INBOX após organizar",
            value=True,
            help="Remove e-mails da caixa de entrada após movê-los para pastas"
        )
        
        limite_emails = st.slider(
            "Limite de e-mails por execução",
            min_value=100,
            max_value=5000,
            value=2000,
            step=100,
            help="Máximo de e-mails a processar por vez"
        )
        
        st.markdown("---")
        
        # Agendamento
        st.markdown("#### ⏰ Agendamento Automático")
        
        intervalo_horas = st.selectbox(
            "Intervalo de execução",
            options=[1, 3, 6, 12, 24],
            index=1,
            format_func=lambda x: f"{x} hora(s)",
            help="Frequência de execução automática"
        )
        
        st.markdown("---")
        
        # Informações
        st.markdown("#### ℹ️ Sobre")
        st.info(
            "**MailNest** usa IA para classificar "
            "automaticamente seus e-mails em categorias, "
            "mantendo sua caixa de entrada sempre organizada."
        )
        
        st.markdown("---")
        st.markdown("**Versão:** 2.0.0")
        st.markdown("**Status:** 🟢 Online")

    # Inicializa session state
    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "rodando" not in st.session_state:
        st.session_state.rodando = False
        st.session_state.stop_event = threading.Event()
        st.session_state.thread = None
    if "ultima_execucao" not in st.session_state:
        st.session_state.ultima_execucao = "—"
    if "total_organizados" not in st.session_state:
        st.session_state.total_organizados = 0

    # Dashboard com métricas
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric(
            label="📧 Total Organizados",
            value=st.session_state.total_organizados,
            delta="Sessão atual"
        )
    
    with col_m2:
        st.metric(
            label="� Última Execução",
            value=st.session_state.ultima_execucao
        )
    
    with col_m3:
        status_icon = "🟢" if st.session_state.rodando else "⚪"
        status_text = "Ativo" if st.session_state.rodando else "Inativo"
        st.metric(
            label="⚙️ Agendador",
            value=status_text,
            delta=status_icon
        )
    
    with col_m4:
        st.metric(
            label="📊 Execuções",
            value=len([l for l in st.session_state.logs if "CONCLUÍDO" in l])
        )

    st.markdown("---")
    
    # Área principal com tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Executar", "📊 Logs", "📚 Ajuda"])
    
    with tab1:
        st.markdown("### Ações Disponíveis")
        
        # Containers para feedback
        status_container = st.empty()
        progress_container = st.empty()
        
        # Botões de ação em grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 **Organizar Agora**", use_container_width=True, type="primary"):
                if not email_usuario or not senha:
                    st.error("⚠️ Configure suas credenciais na barra lateral primeiro.")
                else:
                    log_container_temp = st.empty()
                    with st.spinner("🔄 Organizando seus e-mails..."):
                        novos_logs = organizar_emails(
                            email_usuario, 
                            senha, 
                            progress_container, 
                            log_container_temp, 
                            status_container,
                            excluir_da_inbox=excluir_inbox
                        )
                        st.session_state.logs.extend(novos_logs)
                        st.session_state.ultima_execucao = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        st.session_state.total_organizados += sum(1 for log in novos_logs if "📧 E-mail" in log)
                        st.balloons()
                        st.rerun()
        
        with col2:
            if st.button("🔍 **Limpar Duplicatas**", use_container_width=True):
                if not email_usuario or not senha:
                    st.error("⚠️ Configure suas credenciais na barra lateral primeiro.")
                else:
                    log_container_temp = st.empty()
                    with st.spinner("🔍 Verificando duplicatas..."):
                        logs_duplicatas = []
                        
                        def log_temp(msg):
                            logs_duplicatas.append(msg)
                        
                        try:
                            status_container.info("� Conectando ao Gmail...")
                            imap = conectar_email(email_usuario, senha, log_callback=log_temp)
                            
                            status_container.info("🔍 Analisando pastas e removendo duplicatas...")
                            
                            def progress_temp(progresso, texto):
                                progress_container.progress(progresso, text=texto)
                            
                            def status_temp(msg):
                                status_container.info(msg)
                            
                            duplicatas = verificar_e_remover_duplicatas(
                                imap, 
                                log_callback=log_temp,
                                progress_callback=progress_temp,
                                status_callback=status_temp
                            )
                            
                            imap.logout()
                            
                            log_container_temp.text_area(
                                "📋 Resultado da Verificação:",
                                value="\n".join(logs_duplicatas),
                                height=300
                            )
                            
                            if duplicatas > 0:
                                status_container.success(f"✅ {duplicatas} duplicatas removidas!")
                                st.balloons()
                            else:
                                status_container.info("✅ Nenhuma duplicata encontrada!")
                            
                            st.session_state.logs.extend(logs_duplicatas)
                            
                        except Exception as e:
                            status_container.error(f"❌ Erro: {e}")
        
        with col3:
            if not st.session_state.rodando:
                if st.button(f"⏰ **Ativar Agendador**", use_container_width=True):
                    if not email_usuario or not senha:
                        st.error("⚠️ Configure suas credenciais na barra lateral primeiro.")
                    else:
                        st.session_state.stop_event.clear()
                        st.session_state.thread = threading.Thread(
                            target=agendador,
                            args=(email_usuario, senha, st.session_state.stop_event),
                            daemon=True
                        )
                        st.session_state.thread.start()
                        st.session_state.rodando = True
                        st.success(f"✅ Agendador ativo! Executará a cada {intervalo_horas}h")
                        st.rerun()
            else:
                if st.button("⏹️ **Parar Agendador**", use_container_width=True, type="secondary"):
                    st.session_state.stop_event.set()
                    st.session_state.rodando = False
                    st.warning("⏸️ Agendador desativado")
                    st.rerun()
        
        st.markdown("---")
        
        # Visualização em tempo real
        st.markdown("### 📊 Progresso em Tempo Real")
        result_container = st.container()
    
    with tab2:
        st.markdown("### 📜 Histórico de Execuções")
        
        col_log1, col_log2 = st.columns([3, 1])
        
        with col_log2:
            if st.button("🗑️ Limpar Logs", use_container_width=True):
                st.session_state.logs = []
                st.session_state.total_organizados = 0
                st.success("Logs limpos!")
                st.rerun()
            
            # Filtro de logs
            filtro = st.selectbox(
                "Filtrar por:",
                ["Todos", "Erros", "Sucessos", "Avisos"]
            )
        
        with col_log1:
            if st.session_state.logs:
                logs_filtrados = st.session_state.logs
                
                if filtro == "Erros":
                    logs_filtrados = [l for l in logs_filtrados if "❌" in l or "Erro" in l]
                elif filtro == "Sucessos":
                    logs_filtrados = [l for l in logs_filtrados if "✅" in l or "sucesso" in l.lower()]
                elif filtro == "Avisos":
                    logs_filtrados = [l for l in logs_filtrados if "⚠️" in l]
                
                st.text_area(
                    f"Logs ({len(logs_filtrados)} entradas)",
                    value="\n".join(logs_filtrados[-200:]),  # Últimas 200 linhas
                    height=500,
                    disabled=True
                )
                
                # Botão de download
                st.download_button(
                    label="💾 Baixar Logs Completos",
                    data="\n".join(st.session_state.logs),
                    file_name=f"gmail_organizer_logs_{datetime.datetime.now():%Y%m%d_%H%M%S}.txt",
                    mime="text/plain"
                )
            else:
                st.info("📭 Nenhum log disponível ainda. Execute uma organização para gerar logs.")
    
    with tab3:
        st.markdown("### 📚 Como Usar o MailNest")
        
        st.markdown("""
        #### 🚀 Início Rápido
        
        1. **Configure suas credenciais**
           - Na barra lateral, insira seu e-mail Gmail
           - Gere uma senha de aplicativo em [Google Account](https://myaccount.google.com/apppasswords)
           - Cole a senha gerada no campo "Senha de aplicativo"
        
        2. **Execute a organização**
           - Clique em "Organizar Agora" para processar seus e-mails
           - Acompanhe o progresso em tempo real
           - Veja os resultados na aba "Logs"
        
        3. **Ative o agendador (opcional)**
           - Configure o intervalo desejado na barra lateral
           - Clique em "Ativar Agendador"
           - Seus e-mails serão organizados automaticamente
        
        ---
        
        #### � Categorias Disponíveis
        
        Os e-mails são classificados automaticamente em:
        
        - 💰 **Faturas** - Boletos, pagamentos, notas fiscais
        - 💼 **Trabalho** - Projetos, relatórios, documentos
        - 👤 **Pessoal** - Amigos, família, eventos
        - 📢 **Marketing** - Promoções, newsletters, ofertas
        - ⚙️ **Sistema** - Alertas, erros, notificações
        - ⚠️ **Problemas** - E-mails com sentimento negativo
        - 😊 **Positivos** - E-mails com sentimento positivo
        - 📄 **Neutros** - Outros e-mails
        
        ---
        
        #### 🔧 Funcionalidades
        
        - ✅ Organização automática com IA
        - ✅ Detecção e remoção de duplicatas
        - ✅ Agendamento automático
        - ✅ Logs detalhados em tempo real
        - ✅ Interface profissional e responsiva
        - ✅ Métricas e estatísticas
        
        ---
        
        #### ⚠️ Importante
        
        - Use uma **senha de aplicativo**, não sua senha normal do Gmail
        - O aplicativo não armazena suas credenciais
        - Todos os dados são processados em tempo real
        - E-mails são movidos, não excluídos permanentemente
        """)
        
        st.markdown("---")
        
        with st.expander("❓ Perguntas Frequentes"):
            st.markdown("""
            **Como gero uma senha de aplicativo?**
            1. Acesse https://myaccount.google.com/apppasswords
            2. Faça login com sua conta Google
            3. Selecione "E-mail" e "Outro dispositivo"
            4. Copie a senha gerada (16 caracteres)
            
            **Os e-mails são excluídos permanentemente?**
            Não. Eles são movidos para pastas. Você pode recuperá-los a qualquer momento.
            
            **Posso personalizar as categorias?**
            Sim! Edite a função `classificar_email()` no código fonte.
            
            **É seguro?**
            Sim. Usamos protocolo IMAP SSL e não armazenamos suas credenciais.
            """)

if __name__ == "__main__":
    main()
