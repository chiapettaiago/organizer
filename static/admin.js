// Carregar códigos ao iniciar
document.addEventListener('DOMContentLoaded', function() {
    atualizarLista();
});

// Gerar novo código
async function gerarCodigo() {
    try {
        const response = await fetch('/api/admin/gerar-convite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Mostrar modal com o código
            document.getElementById('codigo-gerado').textContent = data.codigo;
            document.getElementById('codigo-modal').classList.add('show');
            
            // Atualizar lista
            await atualizarLista();
        } else {
            alert('Erro ao gerar código: ' + (data.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão ao gerar código');
    }
}

// Atualizar lista de códigos
async function atualizarLista() {
    try {
        const response = await fetch('/api/admin/listar-convites');
        const data = await response.json();

        if (response.ok) {
            // Atualizar stats
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-disponiveis').textContent = data.disponiveis;
            document.getElementById('stat-usados').textContent = data.usados;

            // Atualizar tabela
            const tbody = document.getElementById('convites-tbody');
            
            if (data.convites.length === 0) {
                tbody.innerHTML = `
                    <tr class="empty-state">
                        <td colspan="7">
                            <div class="empty-message">
                                <svg width="64" height="64" viewBox="0 0 24 24" fill="none">
                                    <path d="M20 6H12L10 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6ZM20 18H4V6H9.17L11.17 8H20V18ZM6 12H18V14H6V12ZM6 16H14V18H6V16Z" fill="currentColor"/>
                                </svg>
                                <p>Nenhum código de convite gerado ainda</p>
                                <small>Clique em "Gerar Novo Código" para criar o primeiro</small>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                tbody.innerHTML = data.convites.map(c => `
                    <tr>
                        <td class="codigo-cell">${c.codigo}</td>
                        <td>${c.criado_por}</td>
                        <td>${c.criado_em}</td>
                        <td>
                            <span class="badge ${c.usado ? 'usado' : 'disponivel'}">
                                ${c.usado ? '✓ Utilizado' : '○ Disponível'}
                            </span>
                        </td>
                        <td>${c.usado_por || '-'}</td>
                        <td>${c.usado_em || '-'}</td>
                        <td>
                            <button 
                                class="btn-revogar" 
                                onclick="revogarCodigo('${c.codigo}')"
                                ${c.usado ? 'disabled' : ''}
                            >
                                ${c.usado ? '🔒 Usado' : '🗑️ Revogar'}
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } else {
            alert('Erro ao carregar códigos: ' + (data.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão ao carregar códigos');
    }
}

// Revogar código
async function revogarCodigo(codigo) {
    if (!confirm(`Tem certeza que deseja revogar o código ${codigo}?\n\nEle não poderá mais ser utilizado.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/admin/revogar-convite/${codigo}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message);
            await atualizarLista();
        } else {
            alert('Erro ao revogar código: ' + (data.error || 'Erro desconhecido'));
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro de conexão ao revogar código');
    }
}

// Copiar código
function copiarCodigo() {
    const codigo = document.getElementById('codigo-gerado').textContent;
    
    navigator.clipboard.writeText(codigo).then(() => {
        const btn = event.target.closest('.btn-copy');
        const originalText = btn.innerHTML;
        
        btn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="currentColor"/>
            </svg>
            Copiado!
        `;
        
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);
    }).catch(err => {
        alert('Erro ao copiar código');
        console.error('Erro:', err);
    });
}

// Fechar modal
function fecharModal() {
    document.getElementById('codigo-modal').classList.remove('show');
}

// Fechar modal ao clicar fora
document.getElementById('codigo-modal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        fecharModal();
    }
});
