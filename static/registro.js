document.getElementById('registroForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const nome = document.getElementById('nome').value.trim();
    const email = document.getElementById('email').value.trim();
    const senha = document.getElementById('senha').value;
    const confirmar_senha = document.getElementById('confirmar_senha').value;
    const invite_code = document.getElementById('invite_code').value;
    
    const errorDiv = document.getElementById('error-message');
    const registroBtn = document.getElementById('registroBtn');
    const btnText = registroBtn.querySelector('.btn-text');
    const btnLoading = registroBtn.querySelector('.btn-loading');
    
    // Validações
    if (!nome || !email || !senha || !confirmar_senha) {
        showError('Preencha todos os campos');
        return;
    }
    
    if (senha.length < 6) {
        showError('A senha deve ter no mínimo 6 caracteres');
        return;
    }
    
    if (senha !== confirmar_senha) {
        showError('As senhas não coincidem');
        return;
    }
    
    // Validar formato de email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('Digite um e-mail válido');
        return;
    }
    
    // Esconder mensagem de erro
    errorDiv.style.display = 'none';
    
    // Desabilitar botão e mostrar loading
    registroBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';
    
    try {
        const response = await fetch('/registrar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nome: nome,
                email: email,
                senha: senha,
                invite_code: invite_code
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Registro bem-sucedido
            // Mostrar mensagem de sucesso temporária
            errorDiv.className = 'success-message';
            errorDiv.textContent = '✅ Conta criada com sucesso! Redirecionando...';
            errorDiv.style.display = 'flex';
            
            // Redirecionar após 2 segundos
            setTimeout(() => {
                window.location.href = data.redirect || '/';
            }, 2000);
        } else {
            // Erro no registro
            showError(data.error || 'Erro ao criar conta');
        }
    } catch (error) {
        showError('Erro de conexão. Verifique sua internet e tente novamente.');
        console.error('Erro:', error);
    } finally {
        // Reabilitar botão (apenas se não foi sucesso)
        if (errorDiv.className !== 'success-message') {
            registroBtn.disabled = false;
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
        }
    }
});

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.display = 'flex';
    
    // Focar no primeiro campo
    document.getElementById('nome').focus();
}

// Limpar erro ao começar a digitar
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', () => {
        document.getElementById('error-message').style.display = 'none';
    });
});

// Validar senhas em tempo real
document.getElementById('confirmar_senha').addEventListener('input', function() {
    const senha = document.getElementById('senha').value;
    const confirmar = this.value;
    
    if (confirmar && senha !== confirmar) {
        this.setCustomValidity('As senhas não coincidem');
        this.style.borderColor = '#ef4444';
    } else {
        this.setCustomValidity('');
        this.style.borderColor = '#667eea';
    }
});
