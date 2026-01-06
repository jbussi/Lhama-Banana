import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { 
    getAuth, 
    createUserWithEmailAndPassword,
    signInWithPopup,
    GoogleAuthProvider,
    sendEmailVerification
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
 * Função auxiliar para fazer requisição com retry automático em caso de clock skew
 * Implementa retry silencioso: se receber erro de clock skew, faz refresh de token e tenta novamente
 * 
 * @param {Function} requestFn - Função que retorna uma Promise com a requisição fetch
 * @param {Object} user - Objeto do usuário Firebase para obter novo token
 * @param {number} maxRetries - Número máximo de tentativas (padrão: 1)
 * @returns {Promise<Response>} Resposta da requisição
 */
async function fetchWithClockSkewRetry(requestFn, user, maxRetries = 1) {
    let retryCount = 0;
    
    while (retryCount <= maxRetries) {
        try {
            const response = await requestFn();
            
            // Se sucesso, retornar resposta
            if (response.ok) {
                return response;
            }
            
            // Verificar se é erro de clock skew
            const data = await response.json().catch(() => ({}));
            if (data.clock_skew_error && retryCount < maxRetries) {
                console.log(`[CLOCK_SKEW_RETRY] Erro de clock skew detectado (diferença: ${data.time_diff}s). Fazendo refresh de token e tentando novamente...`);
                
                // Forçar refresh do token
                const newToken = await user.getIdToken(true);
                
                // Aguardar um pouco para o token ficar válido
                await new Promise(resolve => setTimeout(resolve, 500));
                
                // Retry com novo token (a função requestFn deve usar o novo token)
                retryCount++;
                continue;
            }
            
            // Se não for clock skew ou já tentou todas as vezes, retornar resposta original
            return response;
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

// Aguarda o DOM estar pronto
document.addEventListener('DOMContentLoaded', function() {
  const submit = document.getElementById("submit");
  const googleRegisterBtn = document.getElementById("google-register-btn");

  if (!submit) {
    console.error("Botão de submit não encontrado");
    return;
  }

  // Função para processar registro
  async function handleRegister(userCredential, username = null) {
    try {
      const user = userCredential.user;
      console.log("Usuário criado no Firebase:", user);

      // Se for login Google, usar displayName ou email como username
      if (!username) {
        username = user.displayName || user.email.split('@')[0];
      }

      // Obter token (sempre forçar refresh para evitar clock skew)
      let id_token;
      try {
        id_token = await user.getIdToken(true);
        console.log("ID Token obtido (refresh):", id_token);
      } catch (tokenError) {
        console.error("Erro ao obter token:", tokenError);
        throw new Error("Erro ao obter token de autenticação. Tente novamente.");
      }

      // Enviar para backend com retry automático em caso de clock skew
      let response;
      try {
        response = await fetchWithClockSkewRetry(async () => {
          // Obter token atualizado a cada tentativa
          const currentToken = await user.getIdToken(true);
          return fetch("/api/auth/register", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              username: username,
              id_token: currentToken
            })
          });
        }, user, 1); // 1 retry adicional
      } catch (fetchError) {
        console.error("Erro na requisição:", fetchError);
        throw new Error("Erro ao comunicar com o servidor. Verifique sua conexão.");
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.erro || "Erro ao salvar no banco de dados");
      }

      console.log("Dados salvos no backend:", data);

      // SEMPRE enviar email de verificação após cadastro (exceto Google OAuth que já vem verificado)
      // Verificar se é login Google (providerId === 'google.com')
      const isGoogleAuth = user.providerData && user.providerData.some(provider => provider.providerId === 'google.com');
      
      // Esconder loader se estiver visível
      LoadingHelper.hidePageLoader();
      
      if (!isGoogleAuth && (!user.emailVerified || data.requer_verificacao)) {
        try {
          // REMOVIDO: Delay de 500ms - não é necessário, o Firebase já criou o usuário
          await sendEmailVerification(user);
          
          const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
          if (container && window.MessageHelper) {
            MessageHelper.showSuccess(
              `Conta criada com sucesso! Um email de verificação foi enviado para ${user.email}. Verifique sua caixa de entrada e também a pasta de spam. O link expira em 3 dias.`,
              container,
              10000
            );
          }
        } catch (emailError) {
          console.error("Erro ao enviar email de verificação:", emailError);
          
          // Mesmo se falhar, informar o usuário
          const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
          if (container && window.MessageHelper) {
            MessageHelper.showWarning(
              "Conta criada com sucesso! Por favor, verifique seu email para confirmar sua conta. Se não receber o email, você pode solicitar um novo na página de login.",
              container,
              10000
            );
          }
        }
      } else if (isGoogleAuth) {
        // Login Google já vem com email verificado
        const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
        if (container && window.MessageHelper) {
          MessageHelper.showSuccess("Conta criada com sucesso! Seu email já está verificado.", container);
        }
      } else {
        const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
        if (container && window.MessageHelper) {
          MessageHelper.showSuccess("Conta criada com sucesso!", container);
        }
      }

      // Redirecionar para login após 2 segundos
      setTimeout(() => {
        window.location.href = "/auth/login";
      }, 2000);
      
    } catch (error) {
      console.error("Erro no fluxo de registro:", error);
      LoadingHelper.hidePageLoader();
      const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
      if (container && window.MessageHelper) {
        MessageHelper.showError("Erro ao criar conta: " + error.message, container);
      }
    }
  }

  // Registro com email/senha
  submit.addEventListener("click", async function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;
    const terms = document.querySelector('input[name="terms"]');

    // Validações
    if (!username || !email || !password || !confirmPassword) {
      const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
      if (container && window.MessageHelper) {
        MessageHelper.showError('Por favor, preencha todos os campos obrigatórios.', container);
      }
      return;
    }

    if (password !== confirmPassword) {
      const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
      if (container && window.MessageHelper) {
        MessageHelper.showError('As senhas não coincidem.', container);
      }
      return;
    }

    if (!terms || !terms.checked) {
      const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
      if (container && window.MessageHelper) {
        MessageHelper.showError('Você precisa aceitar os Termos de Uso e Política de Privacidade.', container);
      }
      return;
    }

    // Mostrar loading no botão
    const buttonState = LoadingHelper.setButtonLoading(submit, "Criando conta...");

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      await handleRegister(userCredential, username);
    } catch (error) {
      console.error("Erro no registro:", error);
      let errorMessage = "Erro ao criar conta. ";
      
      switch (error.code) {
        case 'auth/email-already-in-use':
          errorMessage = "Este email já está em uso.";
          break;
        case 'auth/invalid-email':
          errorMessage = "Email inválido.";
          break;
        case 'auth/weak-password':
          errorMessage = "Senha muito fraca. Use pelo menos 6 caracteres.";
          break;
        case 'auth/operation-not-allowed':
          errorMessage = "Operação não permitida.";
          break;
        default:
          errorMessage += error.message;
      }
      
      const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
      if (container && window.MessageHelper) {
        MessageHelper.showError(errorMessage, container);
      }
    } finally {
      LoadingHelper.restoreButton(submit, buttonState);
    }
  });

  // Registro com Google
  if (googleRegisterBtn) {
    googleRegisterBtn.addEventListener("click", async function(event) {
      event.preventDefault();
      
      const terms = document.querySelector('input[name="terms"]');
      
      if (!terms || !terms.checked) {
        const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
        if (container && window.MessageHelper) {
          MessageHelper.showError('Você precisa aceitar os Termos de Uso e Política de Privacidade.', container);
        }
        return;
      }
      
      // Mostrar page loader e desabilitar botão
      LoadingHelper.showPageLoader();
      const buttonState = LoadingHelper.setButtonLoading(googleRegisterBtn, "Conectando...");
      
      try {
        const userCredential = await signInWithPopup(auth, googleProvider);
        await handleRegister(userCredential);
      } catch (error) {
        console.error("Erro no registro Google:", error);
        let errorMessage = "Erro ao fazer registro com Google. ";
        
        if (error.code === 'auth/popup-closed-by-user') {
          errorMessage = "Registro cancelado.";
        } else if (error.code === 'auth/popup-blocked') {
          errorMessage = "Popup bloqueado. Permita popups para este site.";
        } else if (error.code === 'auth/account-exists-with-different-credential') {
          errorMessage = "Já existe uma conta com este email usando outro método de login.";
        } else {
          errorMessage += error.message;
        }
        
        const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
        if (container && window.MessageHelper) {
          MessageHelper.showError(errorMessage, container);
        }
        LoadingHelper.hidePageLoader();
      } finally {
        LoadingHelper.restoreButton(googleRegisterBtn, buttonState);
      }
    });
  }
});
