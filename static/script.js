// Conexão WebSocket
const socket = io();

// Variáveis globais
let totalOrganizados = 0;
let totalDuplicatas = 0;
let totalCategorias = 0;

// Função auxiliar para garantir scroll automático
function forcarScrollParaBaixo(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        // Usa requestAnimationFrame para garantir que o DOM foi atualizado
        requestAnimationFrame(() => {
            container.scrollTop = container.scrollHeight;
        });
    }
}

// ==================== TABS ====================
function openTab(tabName) {
    // Esconde todos os conteúdos
    const contents = document.querySelectorAll('.tab-content');
    contents.forEach(content => content.classList.remove('active'));

    // Desativa todos os botões
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(button => button.classList.remove('active'));

    // Ativa o tab selecionado
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');

    // Carrega logs se for a aba de logs
    if (tabName === 'logs') {
        carregarLogs();
    }
}

// ==================== ACTIONS ====================
async function organizarEmails() {
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const excluirInbox = document.getElementById('excluir_inbox').checked;

    if (!email || !senha) {
        mostrarErro('Por favor, preencha o e-mail e a senha!');
        return;
    }

    // Limpa logs anteriores
    const logsContainer = document.getElementById('logs-container');
    logsContainer.innerHTML = '';
    
    // Mostra seção de progresso
    document.getElementById('progress-section').style.display = 'block';
    
    // Atualiza status e mostra feedback imediato
    document.getElementById('metric-status').textContent = '⚙️';
    
    // Adiciona log inicial imediatamente
    const logInicial = document.createElement('div');
    logInicial.className = 'log-entry';
    logInicial.textContent = `[${new Date().toLocaleTimeString()}] 🚀 Iniciando organização...`;
    logsContainer.appendChild(logInicial);
    
    // Inicia progresso
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    
    progressFill.style.width = '5%';
    progressText.textContent = '🔌 Conectando ao servidor...';
    progressPercent.textContent = '5%';

    try {
        const response = await fetch('/api/organizar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                senha: senha,
                excluir_inbox: excluirInbox
            })
        });

        if (!response.ok) {
            const error = await response.json();
            mostrarErro('Erro: ' + error.error);
            document.getElementById('metric-status').textContent = '❌';
            progressFill.style.width = '0%';
            progressText.textContent = 'Erro';
            progressPercent.textContent = '0%';
        } else {
            // Log de confirmação
            const logConfirm = document.createElement('div');
            logConfirm.className = 'log-entry success';
            logConfirm.textContent = `[${new Date().toLocaleTimeString()}] ✅ Requisição enviada, aguarde...`;
            logsContainer.appendChild(logConfirm);
            forcarScrollParaBaixo('logs-container');
        }
    } catch (error) {
        mostrarErro('Erro ao conectar com o servidor: ' + error.message);
        document.getElementById('metric-status').textContent = '❌';
        progressFill.style.width = '0%';
        progressText.textContent = 'Erro';
        progressPercent.textContent = '0%';
    }
}

async function verificarDuplicatas() {
    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;

    if (!email || !senha) {
        mostrarErro('Por favor, preencha o e-mail e a senha!');
        return;
    }
    
    // Feedback visual imediato
    const logsContainer = document.getElementById('logs-container');
    logsContainer.innerHTML = '';
    
    document.getElementById('progress-section').style.display = 'block';
    document.getElementById('metric-status').textContent = '⚙️';
    
    const logInicial = document.createElement('div');
    logInicial.className = 'log-entry';
    logInicial.textContent = `[${new Date().toLocaleTimeString()}] 🔍 Iniciando verificação de duplicatas...`;
    logsContainer.appendChild(logInicial);
    
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    
    progressFill.style.width = '5%';
    progressText.textContent = '🔌 Conectando...';
    progressPercent.textContent = '5%';
    
    // Auto-scroll inicial
    forcarScrollParaBaixo('logs-container');

    try {
        const response = await fetch('/api/verificar-duplicatas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                senha: senha
            })
        });

        if (!response.ok) {
            const error = await response.json();
            mostrarErro('Erro: ' + error.error);
            document.getElementById('metric-status').textContent = '❌';
            progressFill.style.width = '0%';
            progressText.textContent = 'Erro';
            progressPercent.textContent = '0%';
        } else {
            // Log de confirmação
            const logConfirm = document.createElement('div');
            logConfirm.className = 'log-entry success';
            logConfirm.textContent = `[${new Date().toLocaleTimeString()}] ✅ Requisição enviada, aguarde...`;
            logsContainer.appendChild(logConfirm);
            forcarScrollParaBaixo('logs-container');
        }
    } catch (error) {
        mostrarErro('Erro ao conectar com o servidor: ' + error.message);
        document.getElementById('metric-status').textContent = '❌';
        progressFill.style.width = '0%';
        progressText.textContent = 'Erro';
        progressPercent.textContent = '0%';
    }
}

async function limparLogs() {
    if (!confirm('Tem certeza que deseja limpar todos os logs?')) {
        return;
    }

    try {
        const response = await fetch('/api/limpar-logs', {
            method: 'POST'
        });

        if (response.ok) {
            document.getElementById('historico-logs').innerHTML = '<p class="log-empty">Nenhum log disponível</p>';
        }
    } catch (error) {
        alert('Erro ao limpar logs: ' + error.message);
    }
}

async function carregarLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();

        const container = document.getElementById('historico-logs');
        
        if (data.logs && data.logs.length > 0) {
            container.innerHTML = data.logs.map(log => {
                let cssClass = 'log-entry';
                if (log.includes('❌') || log.includes('Erro')) {
                    cssClass += ' error';
                } else if (log.includes('✅') || log.includes('sucesso')) {
                    cssClass += ' success';
                } else if (log.includes('⚠️')) {
                    cssClass += ' warning';
                }
                return `<div class="${cssClass}">${escapeHtml(log)}</div>`;
            }).join('');
        } else {
            container.innerHTML = '<p class="log-empty">Nenhum log disponível</p>';
        }

        // Scroll para o final - FORÇADO
        forcarScrollParaBaixo('historico-logs');
    } catch (error) {
        console.error('Erro ao carregar logs:', error);
    }
}

// ==================== WEBSOCKET EVENTS ====================
socket.on('connect', function() {
    console.log('Conectado ao servidor via WebSocket');
});

socket.on('log', function(data) {
    console.log('📩 Evento LOG recebido:', data);  // Debug
    const container = document.getElementById('logs-container');
    
    // Remove mensagem de vazio se existir
    const emptyMsg = container.querySelector('.log-empty');
    if (emptyMsg) {
        emptyMsg.remove();
    }

    // Adiciona novo log
    const logDiv = document.createElement('div');
    let cssClass = 'log-entry';
    
    if (data.message.includes('❌') || data.message.includes('Erro')) {
        cssClass += ' error';
    } else if (data.message.includes('✅') || data.message.includes('sucesso')) {
        cssClass += ' success';
    } else if (data.message.includes('⚠️')) {
        cssClass += ' warning';
    }
    
    logDiv.className = cssClass;
    logDiv.textContent = data.message;
    container.appendChild(logDiv);

    // Auto-scroll FORÇADO para o final
    forcarScrollParaBaixo('logs-container');
});

socket.on('progresso', function(data) {
    console.log('📊 Evento PROGRESSO recebido:', data);  // Debug
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');

    const percentual = Math.round(data.progresso * 100);
    
    progressFill.style.width = percentual + '%';
    progressText.textContent = data.texto;
    progressPercent.textContent = percentual + '%';
});

socket.on('conclusao', function(data) {
    // Atualiza métricas
    totalOrganizados = data.total;
    totalCategorias = Object.keys(data.categorias || {}).length;
    totalDuplicatas = data.duplicatas || 0;

    document.getElementById('metric-total').textContent = totalOrganizados;
    document.getElementById('metric-categorias').textContent = totalCategorias;
    document.getElementById('metric-duplicatas').textContent = totalDuplicatas;
    document.getElementById('metric-status').textContent = '✅';

    // Mostra resumo
    let resumo = `\n✅ ORGANIZAÇÃO CONCLUÍDA!\n`;
    resumo += `📊 Total: ${data.total} e-mails\n`;
    resumo += `📁 Categorias: ${totalCategorias}\n`;
    
    if (data.categorias) {
        resumo += `\nDistribuição:\n`;
        for (const [categoria, count] of Object.entries(data.categorias)) {
            resumo += `  • ${categoria}: ${count} e-mails\n`;
        }
    }
    
    if (data.duplicatas > 0) {
        resumo += `\n🗑️ Duplicatas removidas: ${data.duplicatas}\n`;
    }

    alert(resumo);
});

socket.on('duplicatas_resultado', function(data) {
    totalDuplicatas += data.duplicatas;
    document.getElementById('metric-duplicatas').textContent = totalDuplicatas;
    document.getElementById('metric-status').textContent = '✅';

    alert(`✅ Verificação concluída!\n🗑️ ${data.duplicatas} duplicatas removidas.`);
});

socket.on('erro', function(data) {
    document.getElementById('metric-status').textContent = '❌';
    mostrarErro(data.message);
});

// ==================== HELPERS ====================
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function mostrarErro(mensagem) {
    // Criar modal de erro se não existir
    let modal = document.getElementById('erro-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'erro-modal';
        modal.className = 'erro-modal';
        modal.innerHTML = `
            <div class="erro-modal-content">
                <span class="erro-modal-close" onclick="fecharErroModal()">&times;</span>
                <h2>⚠️ Erro</h2>
                <p id="erro-modal-mensagem"></p>
                <button onclick="fecharErroModal()" class="btn-fechar-erro">Fechar</button>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Fechar ao clicar fora do modal
        modal.onclick = function(event) {
            if (event.target === modal) {
                fecharErroModal();
            }
        };
    }
    
    // Mostrar mensagem de erro (preserva quebras de linha)
    const mensagemElement = document.getElementById('erro-modal-mensagem');
    mensagemElement.textContent = mensagem;
    mensagemElement.style.whiteSpace = 'pre-wrap';
    modal.style.display = 'block';
}

function fecharErroModal() {
    const modal = document.getElementById('erro-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ==================== LOGOUT ====================
function logout() {
    if (confirm('Deseja realmente sair?')) {
        window.location.href = '/logout';
    }
}

// ==================== CREDENCIAIS GMAIL ====================
async function carregarCredenciais() {
    try {
        const response = await fetch('/api/gmail/credenciais');
        const data = await response.json();
        
        if (data.success && data.gmail_email) {
            document.getElementById('email').value = data.gmail_email;
            // Preenche a senha também
            if (data.has_password && data.gmail_password) {
                document.getElementById('senha').value = data.gmail_password;
                document.getElementById('btn-remover-creds').style.display = 'inline-block';
            }
        }
    } catch (error) {
        console.error('Erro ao carregar credenciais:', error);
    }
}

async function salvarCredenciais() {
    const gmail_email = document.getElementById('email').value;
    const gmail_password = document.getElementById('senha').value;
    
    if (!gmail_email || !gmail_password) {
        alert('⚠️ Preencha o e-mail e a senha antes de salvar!');
        return;
    }
    
    if (!confirm('💾 Deseja salvar estas credenciais para uso futuro?\n\nIsso permitirá que você não precise digitá-las novamente.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/gmail/credenciais', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                gmail_email: gmail_email,
                gmail_password: gmail_password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Credenciais salvas com sucesso!');
            document.getElementById('btn-remover-creds').style.display = 'inline-block';
            document.getElementById('senha').placeholder = '••••••••••••••••';
        } else {
            alert('❌ Erro ao salvar credenciais: ' + (data.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao salvar credenciais:', error);
        alert('❌ Erro ao salvar credenciais. Veja o console para detalhes.');
    }
}

async function removerCredenciais() {
    if (!confirm('🗑️ Deseja realmente remover as credenciais salvas?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/gmail/credenciais', {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Credenciais removidas com sucesso!');
            document.getElementById('email').value = '';
            document.getElementById('senha').value = '';
            document.getElementById('senha').placeholder = 'Senha de aplicativo';
            document.getElementById('btn-remover-creds').style.display = 'none';
        } else {
            alert('❌ Erro ao remover credenciais: ' + (data.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro ao remover credenciais:', error);
        alert('❌ Erro ao remover credenciais. Veja o console para detalhes.');
    }
}

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('MailNest carregado!');
    // Carregar credenciais salvas ao iniciar
    carregarCredenciais();
});
