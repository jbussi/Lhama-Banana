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
            const shouldVerify = confirm(
                "Seu email ainda não foi verificado. " +
                "Deseja receber um novo email de verificação? " +
                "Você pode continuar, mas algumas funcionalidades podem estar limitadas."
            );
            
            if (shouldVerify) {
                await sendEmailVerification(user);
                const container = document.getElementById('login-messages-container') || document.body;
                MessageHelper.showSuccess("Email de verificação enviado! Verifique sua caixa de entrada.", container);
            }
        }
        
        // Obter token (forçar refresh para garantir token válido)
        let id_token;
        try {
            id_token = await user.getIdToken(true); // true = force refresh
            console.log("ID Token obtido:", id_token.substring(0, 50) + "...");
        } catch (tokenError) {
            console.error("Erro ao obter token:", tokenError);
            throw new Error("Erro ao obter token de autenticação. Tente novamente.");
        }

        // Decodificar token para verificar expiração (sem verificar assinatura)
        let tokenExp;
        try {
            const tokenParts = id_token.split('.');
            if (tokenParts.length === 3) {
                const payload = JSON.parse(atob(tokenParts[1]));
                tokenExp = payload.exp;
                const now = Math.floor(Date.now() / 1000);
                const timeUntilValid = tokenExp - now;
                
                console.log(`Token expira em: ${new Date(tokenExp * 1000).toLocaleString()}`);
                console.log(`Tempo até válido: ${timeUntilValid}s`);
                
                // Se o token ainda não é válido (iat > now), aguardar
                const tokenIat = payload.iat;
                if (tokenIat && tokenIat > now) {
                    const waitTime = (tokenIat - now + 1) * 1000; // +1 segundo de margem (reduzido de 2s)
                    console.log(`Token ainda não é válido. Aguardando ${waitTime/1000}s...`);
                    await new Promise((resolve) => setTimeout(resolve, waitTime));
                } else {
                    // Delay padrão para clock skew (reduzido de 3s para 1.5s)
                    await new Promise((resolve) => setTimeout(resolve, 1500));
                }
            } else {
                // Se não conseguir decodificar, usar delay padrão (reduzido)
                await new Promise((resolve) => setTimeout(resolve, 1500));
            }
        } catch (decodeError) {
            console.warn("Erro ao decodificar token para verificar timing:", decodeError);
            // Se houver erro ao decodificar, usar delay padrão
            await new Promise((resolve) => setTimeout(resolve, 3000));
        }

        // Enviar para backend
        let response;
        try {
            response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
                    id_token: id_token
        })
      });
        } catch (fetchError) {
            console.error("Erro na requisição:", fetchError);
            throw new Error("Erro ao comunicar com o servidor. Verifique sua conexão.");
        }

        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error("Erro ao parsear resposta:", jsonError);
            throw new Error("Resposta inválida do servidor. Tente novamente.");
        }

    if (!response.ok) {
            console.error("Erro do servidor:", data);
            // Verificar se é erro de email não verificado
            if (data.requer_verificacao) {
                const resend = confirm(
                    "Seu email não está verificado. " +
                    "Deseja receber um novo email de verificação?"
                );
                if (resend) {
                    await sendEmailVerification(user);
                    const container = document.getElementById('login-messages-container') || document.body;
                    MessageHelper.showSuccess("Email de verificação enviado! Verifique sua caixa de entrada.", container);
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
            await handleMFAVerification(user);
            return; // Não redirecionar ainda - aguardar verificação 2FA
        } else {
            console.log("2FA não necessário - redirecionando para perfil");
        }
        
        // Redirecionar
        window.location.href = "/perfil";
        
    } catch (error) {
    console.error("Erro no fluxo de login:", error.message);
    const container = document.getElementById('login-messages-container') || document.body;
    MessageHelper.showError("Erro ao logar: " + error.message, container);
    }
}

// Login com email/senha
if (submit) {
    submit.addEventListener("click", async function(event) {
  event.preventDefault();

        const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

        if (!email || !password) {
            const container = document.getElementById('login-messages-container') || document.body;
            MessageHelper.showError('Por favor, preencha todos os campos.', container);
            return;
        }

        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            await handleLogin(userCredential);
        } catch (error) {
            console.error("Erro no login:", error);
            let errorMessage = "Erro ao fazer login. ";
            
            switch (error.code) {
                case 'auth/user-not-found':
                    errorMessage += "Usuário não encontrado.";
                    break;
                case 'auth/wrong-password':
                    errorMessage += "Senha incorreta.";
                    break;
                case 'auth/invalid-email':
                    errorMessage += "Email inválido.";
                    break;
                case 'auth/user-disabled':
                    errorMessage += "Conta desabilitada.";
                    break;
                case 'auth/too-many-requests':
                    errorMessage += "Muitas tentativas. Tente novamente mais tarde.";
                    break;
                default:
                    errorMessage += error.message;
            }
            
            alert(errorMessage);
        }
    });
}

// Login com Google
if (googleLoginBtn) {
    googleLoginBtn.addEventListener("click", async function(event) {
        event.preventDefault();
        
        try {
            const userCredential = await signInWithPopup(auth, googleProvider);
            await handleLogin(userCredential);
        } catch (error) {
            console.error("Erro no login Google:", error);
            let errorMessage = "Erro ao fazer login com Google. ";
            
            if (error.code === 'auth/popup-closed-by-user') {
                errorMessage = "Login cancelado.";
            } else if (error.code === 'auth/popup-blocked') {
                errorMessage = "Popup bloqueado. Permita popups para este site.";
            } else {
                errorMessage += error.message;
            }
            
            const container = document.getElementById('login-messages-container') || document.body;
            MessageHelper.showError(errorMessage, container);
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
            let errorMessage = "Erro ao enviar email. ";
            
            if (error.code === 'auth/user-not-found') {
                errorMessage = "Email não encontrado em nossa base de dados.";
            } else if (error.code === 'auth/invalid-email') {
                errorMessage = "Email inválido. Verifique o formato.";
            } else if (error.code === 'auth/too-many-requests') {
                errorMessage = "Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.";
            } else {
                errorMessage += error.message;
            }
            
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
                <form id="mfa-login-form">
                    <div class="form-group">
                        <label for="mfa-login-code">Código 2FA</label>
                        <i class="fas fa-key"></i>
                        <input type="text" id="mfa-login-code" name="code" placeholder="000000" maxlength="6" pattern="[0-9]{6}" required autofocus>
                    </div>
                    <button type="submit" class="auth-button" id="mfa-verify-submit">
                        <i class="fas fa-check"></i> Verificar
                    </button>
                </form>
                <div id="mfa-login-message" style="margin-top: 1rem; display: none;"></div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
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
            messageDiv.innerHTML = '<div style="background: #d4edda; color: #155724; padding: 1rem; border-radius: 6px; border: 1px solid #c3e6cb;"><i class="fas fa-check-circle"></i> <strong>2FA verificado com sucesso!</strong></div>';
            messageDiv.style.display = 'block';
            
            // Redirecionar após 1 segundo
            setTimeout(() => {
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
