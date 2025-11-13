// Estado do tipo de login
let currentLoginType = 'credentials';

// Toggle entre tipos de login
document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const type = this.dataset.type;
        currentLoginType = type;
        
        // Atualizar botões
        document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        // Atualizar formulários
        document.querySelectorAll('.login-method').forEach(m => m.classList.remove('active'));
        document.getElementById(`${type}-form`).classList.add('active');
        
        // Limpar erro
        document.getElementById('error-message').style.display = 'none';
    });
});

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const errorDiv = document.getElementById('error-message');
    const loginBtn = document.getElementById('loginBtn');
    const btnText = loginBtn.querySelector('.btn-text');
    const btnLoading = loginBtn.querySelector('.btn-loading');
    
    // Esconder mensagem de erro anterior
    errorDiv.style.display = 'none';
    
    // Desabilitar botão e mostrar loading
    loginBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'flex';
    
    try {
        let body;
        
        if (currentLoginType === 'invite') {
            // Login com código de convite
            const invite_code = document.getElementById('invite_code').value.trim();
            
            if (!invite_code) {
                showError('Digite o código de convite');
                return;
            }
            
            body = JSON.stringify({ 
                login_type: 'invite',
                invite_code: invite_code 
            });
        } else {
            // Login com credenciais
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;
            
            if (!username || !password) {
                showError('Preencha usuário e senha');
                return;
            }
            
            body = JSON.stringify({ 
                login_type: 'credentials',
                username: username, 
                password: password 
            });
        }
        
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: body
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Login bem-sucedido
            window.location.href = data.redirect || '/';
        } else {
            // Erro de autenticação
            showError(data.error || 'Erro ao fazer login');
        }
    } catch (error) {
        showError('Erro de conexão. Verifique sua internet e tente novamente.');
        console.error('Erro:', error);
    } finally {
        // Reabilitar botão
        loginBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
});

function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'flex';
    
    // Focar no campo apropriado
    if (currentLoginType === 'invite') {
        document.getElementById('invite_code').focus();
    } else {
        document.getElementById('username').focus();
    }
}

// Limpar erro ao começar a digitar
document.getElementById('username').addEventListener('input', () => {
    document.getElementById('error-message').style.display = 'none';
});

document.getElementById('password').addEventListener('input', () => {
    document.getElementById('error-message').style.display = 'none';
});

document.getElementById('invite_code').addEventListener('input', (e) => {
    document.getElementById('error-message').style.display = 'none';
    // Converter para maiúsculas automaticamente
    e.target.value = e.target.value.toUpperCase();
});

// Enter para submeter
document.getElementById('password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('loginForm').dispatchEvent(new Event('submit'));
    }
});

document.getElementById('invite_code').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('loginForm').dispatchEvent(new Event('submit'));
    }
});
