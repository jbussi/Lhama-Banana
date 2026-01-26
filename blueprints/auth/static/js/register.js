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
        'auth/popup-closed-by-user': 'Cadastro cancelado. Você fechou a janela de autenticação.',
        'auth/popup-blocked': 'A janela de cadastro foi bloqueada pelo navegador. Permita popups para este site nas configurações do navegador.',
        'auth/cancelled-popup-request': 'Outra solicitação de cadastro está em andamento. Aguarde um momento.',
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
        }, user, 3); // 3 retries adicionais para clock skew grande
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
          
          // Mesmo se falhar, informar o usuário com mensagem amigável
          const container = document.getElementById('register-messages-container') || document.querySelector('.auth-container');
          if (container && window.MessageHelper) {
            const emailErrorMessage = getFriendlyErrorMessage(emailError.code, null);
            MessageHelper.showWarning(
              `Conta criada com sucesso! Porém, não foi possível enviar o email de verificação: ${emailErrorMessage}. Você pode solicitar um novo email de verificação na página de login.`,
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
        // Se for erro do backend, usar mensagem do backend; se for erro do Firebase, traduzir
        const errorMessage = error.code ? getFriendlyErrorMessage(error.code, error.message) : 
                            (error.message || 'Ocorreu um erro ao criar sua conta. Tente novamente.');
        MessageHelper.showError(errorMessage, container);
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
      const errorMessage = getFriendlyErrorMessage(error.code, error.message);
      
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
        const errorMessage = getFriendlyErrorMessage(error.code, error.message);
        
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
