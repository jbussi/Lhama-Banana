import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword,
    signInWithPopup,
    GoogleAuthProvider,
    sendEmailVerification,
    sendPasswordResetEmail
} from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

const firebaseConfig = {
  apiKey: "AIzaSyDd13Tl9dJaUqIvNhGWakoEbpYqw7ZrB7Y",
  authDomain: "lhamabanana-981d5.firebaseapp.com",
  projectId: "lhamabanana-981d5",
  storageBucket: "lhamabanana-981d5.firebasestorage.app",
  messagingSenderId: "209130422039",
  appId: "1:209130422039:web:70fcf2089fa90715364152",
  measurementId: "G-4XQSZZB0JK"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

// Adicionar escopo de email para Google
googleProvider.addScope('email');
googleProvider.addScope('profile');

/**
 * Traduz códigos de erro do Firebase para mensagens amigáveis em português
 * @param {string} errorCode - Código de erro do Firebase
 * @param {string} defaultMessage - Mensagem padrão caso o código não seja reconhecido
 * @returns {string} Mensagem amigável em português
 */
function getFriendlyErrorMessage(errorCode, defaultMessage = null) {
    const errorMessages = {
        // Erros de autenticação geral
        'auth/user-not-found': 'Não encontramos uma conta com este email. Verifique se o email está correto ou crie uma nova conta.',
        'auth/wrong-password': 'Senha incorreta. Verifique sua senha e tente novamente.',
        'auth/invalid-email': 'O formato do email é inválido. Por favor, verifique e tente novamente.',
        'auth/user-disabled': 'Esta conta foi desativada. Entre em contato com o suporte para mais informações.',
        'auth/email-already-in-use': 'Este email já está cadastrado. Tente fazer login ou use outro email.',
        'auth/weak-password': 'A senha é muito fraca. Use pelo menos 6 caracteres e combine letras, números e símbolos.',
        'auth/operation-not-allowed': 'Este método de autenticação não está habilitado. Entre em contato com o suporte.',
        'auth/too-many-requests': 'Muitas tentativas de login falharam. Por segurança, aguarde alguns minutos antes de tentar novamente.',
        'auth/network-request-failed': 'Erro de conexão. Verifique sua internet e tente novamente.',
        'auth/internal-error': 'Ocorreu um erro interno. Por favor, tente novamente em alguns instantes.',
        'auth/invalid-credential': 'Email ou senha incorretos. Verifique suas credenciais e tente novamente.',
        'auth/invalid-verification-code': 'Código de verificação inválido ou expirado. Solicite um novo código.',
        'auth/invalid-verification-id': 'Link de verificação inválido ou expirado. Solicite um novo link.',
        'auth/missing-email': 'Email é obrigatório. Por favor, preencha o campo de email.',
        'auth/missing-password': 'Senha é obrigatória. Por favor, preencha o campo de senha.',
        
        // Erros de popup/redirect
        'auth/popup-closed-by-user': 'Login cancelado. Você fechou a janela de autenticação.',
        'auth/popup-blocked': 'A janela de login foi bloqueada pelo navegador. Permita popups para este site nas configurações do navegador.',
        'auth/cancelled-popup-request': 'Outra solicitação de login está em andamento. Aguarde um momento.',
        'auth/account-exists-with-different-credential': 'Já existe uma conta com este email usando outro método de login. Tente fazer login com o método original.',
        
        // Erros de token
        'auth/invalid-user-token': 'Sua sessão expirou. Por favor, faça login novamente.',
        'auth/user-token-expired': 'Sua sessão expirou. Por favor, faça login novamente.',
        'auth/invalid-api-key': 'Erro de configuração. Entre em contato com o suporte.',
        
        // Erros de verificação de email
        'auth/email-already-verified': 'Este email já foi verificado.',
        'auth/invalid-action-code': 'O link de verificação é inválido ou expirou. Solicite um novo link.',
        'auth/expired-action-code': 'O link de verificação expirou. Solicite um novo link.',
        
        // Erros de redefinição de senha
        'auth/invalid-continue-uri': 'Link de redirecionamento inválido.',
        'auth/missing-continue-uri': 'Link de redirecionamento não fornecido.',
        
        // Outros erros
        'auth/requires-recent-login': 'Por segurança, faça login novamente antes de realizar esta ação.',
        'auth/unauthorized-domain': 'Este domínio não está autorizado. Entre em contato com o suporte.',
        'auth/credential-already-in-use': 'Esta credencial já está associada a outra conta.',
        'auth/timeout': 'A operação demorou muito para responder. Tente novamente.',
        'auth/app-deleted': 'A aplicação foi desativada. Entre em contato com o suporte.',
        'auth/app-not-authorized': 'Aplicação não autorizada. Entre em contato com o suporte.',
        'auth/argument-error': 'Erro nos dados fornecidos. Verifique os campos e tente novamente.',
        'auth/invalid-app-credential': 'Credencial da aplicação inválida. Entre em contato com o suporte.',
        'auth/invalid-app-id': 'ID da aplicação inválido. Entre em contato com o suporte.',
        'auth/invalid-phone-number': 'Número de telefone inválido. Verifique o formato.',
        'auth/missing-phone-number': 'Número de telefone é obrigatório.',
        'auth/quota-exceeded': 'Limite de requisições excedido. Tente novamente mais tarde.',
        'auth/session-cookie-expired': 'Sua sessão expirou. Por favor, faça login novamente.',
        'auth/too-many-requests': 'Muitas tentativas. Por segurança, aguarde alguns minutos antes de tentar novamente.',
        'auth/unverified-email': 'Email não verificado. Verifique sua caixa de entrada e confirme seu email.',
        'auth/web-storage-unsupported': 'Seu navegador não suporta armazenamento local. Atualize seu navegador ou use outro dispositivo.'
    };
    
    return errorMessages[errorCode] || defaultMessage || 'Ocorreu um erro inesperado. Por favor, tente novamente ou entre em contato com o suporte.';
}

/**
 * Função auxiliar para fazer requisição com retry automático em caso de clock skew
 * Implementa retry silencioso: se receber erro de clock skew, faz refresh de token e tenta novamente
 * 
 * @param {Function} requestFn - Função que retorna uma Promise com a requisição fetch
 * @param {Object} user - Objeto do usuário Firebase para obter novo token
 * @param {number} maxRetries - Número máximo de tentativas (padrão: 1)
 * @returns {Promise<{response: Response, data: Object}>} Resposta e dados parseados
 */
async function fetchWithClockSkewRetry(requestFn, user, maxRetries = 1) {
    let retryCount = 0;
    
    while (retryCount <= maxRetries) {
        try {
            const response = await requestFn();
            
            // Clonar resposta antes de ler o JSON para evitar "body stream already read"
            const responseClone = response.clone();
            
            // Tentar parsear JSON (pode falhar se não for JSON)
            let data = {};
            try {
                data = await responseClone.json();
            } catch (e) {
                // Se não for JSON, usar objeto vazio
                data = {};
            }
            
            // Se sucesso, retornar resposta e dados
            if (response.ok) {
                return { response, data };
            }
            
            // Verificar se é erro de clock skew
            if (data.clock_skew_error && retryCount < maxRetries) {
                console.log(`[CLOCK_SKEW_RETRY] Erro de clock skew detectado (diferença: ${data.time_diff}s). Fazendo refresh de token e tentando novamente...`);
                
                // Delay otimizado: apenas o tempo necessário + margem mínima
                const timeDiff = data.time_diff || 1;
                // Delay reduzido: diferença + 500ms (margem mínima), máximo 3s
                const delay = Math.min(timeDiff * 1000 + 500, 3000);
                console.log(`[CLOCK_SKEW_RETRY] Aguardando ${delay}ms antes de tentar novamente...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                
                // Forçar refresh do token apenas quando necessário
                console.log(`[CLOCK_SKEW_RETRY] Obtendo novo token...`);
                const newToken = await user.getIdToken(true);
                
                // Delay mínimo após refresh (500ms é suficiente)
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Retry com novo token (a função requestFn deve usar o novo token)
                retryCount++;
                console.log(`[CLOCK_SKEW_RETRY] Tentativa ${retryCount + 1}/${maxRetries + 1}...`);
                continue;
            }
            
            // Se não for clock skew ou já tentou todas as vezes, retornar resposta original
            return { response, data };
        } catch (error) {
            // Se for erro de rede ou outro erro, retornar
            if (retryCount >= maxRetries) {
                throw error;
            }
            retryCount++;
        }
    }
    
    throw new Error("Falha após múltiplas tentativas");
}

const submit = document.getElementById("submit");
const googleLoginBtn = document.getElementById("google-login-btn");

// Toggle password visibility
const togglePasswordLogin = document.getElementById("toggle-password-login");
if (togglePasswordLogin) {
    const passwordInput = document.getElementById("password");
    const eyeIcon = togglePasswordLogin.querySelector("i");
    
    togglePasswordLogin.addEventListener("click", function() {
        const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
        passwordInput.setAttribute("type", type);
        
        if (eyeIcon) {
            eyeIcon.classList.toggle("fa-eye");
            eyeIcon.classList.toggle("fa-eye-slash");
        }
    });
}
const forgotPasswordLink = document.getElementById("forgot-password-link");

// Função para fazer login
async function handleLogin(userCredential) {
    try {
        const user = userCredential.user;
        console.log("Usuário autenticado no Firebase:", user);
        
        // Verificar se email está verificado
        if (!user.emailVerified) {
            // Mostrar aviso mas permitir login
            const container = document.getElementById('login-messages-container');
            if (container) {
                MessageHelper.showWarning(
                    "Seu email ainda não foi verificado. Algumas funcionalidades podem estar limitadas. " +
                    "Você pode solicitar um novo email de verificação no seu perfil.",
                    container,
                    8000
                );
            }
        }
        
        // Obter token (sem force refresh inicial - mais rápido)
        let id_token;
        try {
            // Obter token sem forçar refresh primeiro (mais rápido)
            // Se houver clock skew, o retry fará o refresh
            id_token = await user.getIdToken(false);
            console.log("ID Token obtido:", id_token.substring(0, 50) + "...");
        } catch (tokenError) {
            console.error("Erro ao obter token:", tokenError);
            throw new Error("Erro ao obter token de autenticação. Tente novamente.");
        }

        // Enviar para backend com retry automático em caso de clock skew
        let response, data;
        try {
            const result = await fetchWithClockSkewRetry(async () => {
                // Obter token atualizado apenas se necessário (primeira tentativa usa o token já obtido)
                const currentToken = await user.getIdToken(false);
                return fetch("/api/auth/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        id_token: currentToken
                    })
                });
            }, user, 2); // Reduzido para 2 retries (suficiente na maioria dos casos)
            
            response = result.response;
            data = result.data;
        } catch (fetchError) {
            console.error("Erro na requisição:", fetchError);
            throw new Error("Erro ao comunicar com o servidor. Verifique sua conexão.");
        }

    if (!response.ok) {
            console.error("Erro do servidor:", data);
            // Verificar se é erro de email não verificado
            if (data.requer_verificacao) {
                const container = document.getElementById('login-messages-container');
                if (container) {
                    MessageHelper.showWarning(
                        "Seu email não está verificado. Você pode solicitar um novo email de verificação no seu perfil.",
                        container,
                        8000
                    );
                }
            }
            throw new Error(data.erro || "Erro desconhecido no backend");
        }

    console.log("Resposta do servidor:", data);
    console.log("Requer MFA?", data.requer_mfa);
        
        // Verificar se precisa verificar email
        if (data.usuario && !data.usuario.email_verificado) {
            const container = document.getElementById('login-messages-container') || document.body;
            MessageHelper.showWarning("Por favor, verifique seu email antes de continuar.", container);
        }
        
        // Verificar se 2FA é necessário
        if (data.requer_mfa === true) {
            console.log("2FA necessário - chamando handleMFAVerification");
            // Esconder loader antes de mostrar modal 2FA
            LoadingHelper.hidePageLoader();
            await handleMFAVerification(user);
            return; // Não redirecionar ainda - aguardar verificação 2FA
        } else {
            console.log("2FA não necessário - redirecionando para perfil");
            // Esconder loader se estiver visível
            LoadingHelper.hidePageLoader();
            // Redirecionar
            window.location.href = "/perfil";
        }
        
    } catch (error) {
        console.error("Erro no fluxo de login:", error.message);
        const container = document.getElementById('login-messages-container') || document.body;
        // Se for erro do backend, usar mensagem do backend; se for erro do Firebase, traduzir
        const errorMessage = error.code ? getFriendlyErrorMessage(error.code, error.message) : 
                            (error.message || 'Ocorreu um erro ao fazer login. Tente novamente.');
        MessageHelper.showError(errorMessage, container);
    }
}

// Login com email/senha
if (submit) {
    submit.addEventListener("click", async function(event) {
        event.preventDefault();
        
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        if (!email || !password) {
            const container = document.getElementById('login-messages-container');
            if (container) {
                MessageHelper.showError('Por favor, preencha todos os campos.', container);
            }
            return;
        }

        // Mostrar loading no botão
        const buttonState = LoadingHelper.setButtonLoading(submit, "Entrando...");

        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            await handleLogin(userCredential);
        } catch (error) {
            console.error("Erro no login:", error);
            const errorMessage = getFriendlyErrorMessage(error.code, error.message);
            
            const container = document.getElementById('login-messages-container');
            if (container) {
                MessageHelper.showError(errorMessage, container);
            }
        } finally {
            LoadingHelper.restoreButton(submit, buttonState);
        }
    });
}

// Login com Google
if (googleLoginBtn) {
    googleLoginBtn.addEventListener("click", async function(event) {
        event.preventDefault();
        
        // Mostrar page loader e desabilitar botão
        LoadingHelper.showPageLoader();
        const buttonState = LoadingHelper.setButtonLoading(googleLoginBtn, "Conectando...");
        
        try {
            const userCredential = await signInWithPopup(auth, googleProvider);
            // REMOVIDO: Delay de 500ms - não é necessário
            await handleLogin(userCredential);
        } catch (error) {
            console.error("Erro no login Google:", error);
            const errorMessage = getFriendlyErrorMessage(error.code, error.message);
            
            const container = document.getElementById('login-messages-container');
            if (container) {
                MessageHelper.showError(errorMessage, container);
            }
            LoadingHelper.hidePageLoader();
        } finally {
            LoadingHelper.restoreButton(googleLoginBtn, buttonState);
        }
    });
}

// Recuperação de senha - Abrir modal
if (forgotPasswordLink) {
    forgotPasswordLink.addEventListener("click", function(event) {
        event.preventDefault();
        const modal = document.getElementById("forgot-password-modal");
        const emailInput = document.getElementById("forgot-email");
        const loginEmail = document.getElementById("email").value;
        
        // Preencher email do campo de login se existir
        if (loginEmail) {
            emailInput.value = loginEmail;
        }
        
        modal.style.display = "flex";
        emailInput.focus();
    });
}

// Fechar modal
const closeForgotModal = document.getElementById("close-forgot-modal");
const forgotModal = document.getElementById("forgot-password-modal");

if (closeForgotModal) {
    closeForgotModal.addEventListener("click", function() {
        forgotModal.style.display = "none";
        document.getElementById("forgot-password-form").reset();
        document.getElementById("forgot-message").style.display = "none";
    });
}

// Fechar modal ao clicar fora
if (forgotModal) {
    forgotModal.addEventListener("click", function(event) {
        if (event.target === forgotModal) {
            forgotModal.style.display = "none";
            document.getElementById("forgot-password-form").reset();
            document.getElementById("forgot-message").style.display = "none";
        }
    });
}

// Enviar email de recuperação
const forgotPasswordForm = document.getElementById("forgot-password-form");
if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async function(event) {
        event.preventDefault();
        
        const email = document.getElementById("forgot-email").value;
        const sendBtn = document.getElementById("send-reset-btn");
        const messageDiv = document.getElementById("forgot-message");
        
        if (!email) {
            messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Por favor, digite seu email.</div>';
            messageDiv.style.display = "block";
            return;
        }
        
        // Desabilitar botão e mostrar loading
        sendBtn.disabled = true;
        const originalText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        messageDiv.style.display = "none";
        
        try {
            // Enviar email via Firebase
            await sendPasswordResetEmail(auth, email);
            
            // Notificar backend (opcional, para logs)
            try {
                await fetch("/api/auth/password-reset", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ email: email })
                });
            } catch (backendError) {
                console.warn("Erro ao notificar backend:", backendError);
                // Não bloqueia o fluxo se o backend falhar
            }
            
            // Mostrar mensagem de sucesso
            messageDiv.innerHTML = `
                <div style="background: #d4edda; color: #155724; padding: 1rem; border-radius: 6px; border: 1px solid #c3e6cb;">
                    <i class="fas fa-check-circle"></i> 
                    <strong>Email enviado com sucesso!</strong><br>
                    Verifique sua caixa de entrada e também a pasta de spam. 
                    O link expira em 1 hora.
                </div>
            `;
            messageDiv.style.display = "block";
            
            // Limpar formulário após 3 segundos
        setTimeout(() => {
                forgotPasswordForm.reset();
                forgotModal.style.display = "none";
                messageDiv.style.display = "none";
            }, 3000);
            
        } catch (error) {
            console.error("Erro ao enviar email de recuperação:", error);
            const errorMessage = getFriendlyErrorMessage(error.code, error.message);
            
            messageDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${errorMessage}</div>`;
            messageDiv.style.display = "block";
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalText;
        }
    });
}

// Função para verificar 2FA durante login
async function handleMFAVerification(user) {
    // Flag para rastrear se a verificação foi completada (usar objeto para referência compartilhada)
    const mfaState = { completed: false };
    
    // Função para fazer logout de segurança
    const performSecurityLogout = async () => {
        if (!mfaState.completed) {
            try {
                const { signOut } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
                await signOut(auth);
                // Limpar sessão no backend também
                try {
                    await fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
                } catch (e) {}
                console.log('[2FA] Logout automático: verificação não completada');
            } catch (error) {
                console.error('[2FA] Erro ao fazer logout automático:', error);
            }
        }
    };
    
    // Adicionar listener para detectar quando o usuário sai da página sem completar 2FA
    const beforeUnloadHandler = async (event) => {
        await performSecurityLogout();
    };
    
    // Adicionar listener para quando a página está sendo descarregada
    window.addEventListener('beforeunload', beforeUnloadHandler);
    
    // Também adicionar listener para quando a aba perde o foco
    let visibilityTimeout = null;
    const visibilityChangeHandler = async () => {
        if (document.hidden && !mfaState.completed) {
            // Usuário mudou de aba ou minimizou - fazer logout após um tempo
            visibilityTimeout = setTimeout(async () => {
                if (!mfaState.completed && document.hidden) {
                    await performSecurityLogout();
                }
            }, 30000); // 30 segundos após perder foco
        } else if (!document.hidden && visibilityTimeout) {
            // Usuário voltou - cancelar timeout
            clearTimeout(visibilityTimeout);
            visibilityTimeout = null;
        }
    };
    
    document.addEventListener('visibilitychange', visibilityChangeHandler);
    
    // Criar modal para 2FA
    const modal = document.createElement('div');
    modal.id = 'mfa-verification-modal';
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-shield-alt"></i> Verificação 2FA Necessária</h2>
            </div>
            <div class="modal-body">
                <p>Digite o código de 6 dígitos do seu app autenticador:</p>
                <p style="font-size: 0.9rem; color: #856404; margin-top: 0.5rem;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    <strong>Importante:</strong> Complete a verificação ou sua sessão será encerrada por segurança.
                </p>
                <form id="mfa-login-form">
                    <div class="form-group">
                        <label for="mfa-login-code">Código 2FA</label>
                        <i class="fas fa-key"></i>
                        <input type="text" id="mfa-login-code" name="code" placeholder="000000" maxlength="6" pattern="[0-9]{6}" required autofocus>
                    </div>
                    <button type="submit" class="auth-button" id="mfa-verify-submit">
                        <i class="fas fa-check"></i> Verificar
                    </button>
                    <button type="button" class="auth-button" id="mfa-cancel-btn" style="background: #6c757d; margin-top: 0.5rem;">
                        <i class="fas fa-times"></i> Cancelar e Fazer Logout
                    </button>
                </form>
                <div id="mfa-login-message" style="margin-top: 1rem; display: none;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Botão de cancelar - fazer logout
    const cancelBtn = document.getElementById('mfa-cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', async () => {
            try {
                const { signOut } = await import('https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js');
                await signOut(auth);
                // Limpar sessão no backend também
                await fetch('/api/auth/logout', { method: 'POST' }).catch(() => {});
                window.location.href = '/auth/login';
            } catch (error) {
                console.error('Erro ao fazer logout:', error);
                window.location.href = '/auth/login';
            }
        });
    }
    
    // Focar no campo de código
    const codeInput = document.getElementById('mfa-login-code');
    if (codeInput) {
        codeInput.focus();
    }
    
    // Handler do formulário
    document.getElementById('mfa-login-form').addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const code = document.getElementById('mfa-login-code').value;
        const submitBtn = document.getElementById('mfa-verify-submit');
        const messageDiv = document.getElementById('mfa-login-message');
        
        if (!code || code.length !== 6) {
            messageDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Por favor, digite o código de 6 dígitos.</div>';
            messageDiv.style.display = 'block';
            return;
        }
        
        // Desabilitar botão e mostrar loading
        submitBtn.disabled = true;
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verificando...';
        messageDiv.style.display = 'none';
        
        try {
            const idToken = await user.getIdToken(true);
            
            const response = await fetch("/api/auth/mfa/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
                    id_token: idToken,
                    code: code
        })
      });
            
            const data = await response.json();
            
    if (!response.ok) {
                throw new Error(data.erro || "Código 2FA inválido");
            }
            
            // 2FA verificado com sucesso
            mfaState.completed = true;
            
            // Remover listeners de segurança
            window.removeEventListener('beforeunload', beforeUnloadHandler);
            document.removeEventListener('visibilitychange', visibilityChangeHandler);
            if (visibilityTimeout) {
                clearTimeout(visibilityTimeout);
            }
            
            messageDiv.innerHTML = '<div style="background: #d4edda; color: #155724; padding: 1rem; border-radius: 6px; border: 1px solid #c3e6cb;"><i class="fas fa-check-circle"></i> <strong>2FA verificado com sucesso!</strong></div>';
            messageDiv.style.display = 'block';
            
            // Esconder loader se estiver visível
            LoadingHelper.hidePageLoader();
            
            // Remover modal após 1 segundo e redirecionar
            setTimeout(() => {
                modal.remove();
                window.location.href = "/perfil";
            }, 1000);
            
        } catch (error) {
            console.error("Erro ao verificar 2FA:", error);
            messageDiv.innerHTML = `<div class="error-message"><i class="fas fa-exclamation-circle"></i> ${error.message}</div>`;
            messageDiv.style.display = 'block';
            codeInput.value = '';
            codeInput.focus();
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}
