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

      // Obter token
      const id_token = await user.getIdToken();
      console.log("ID Token obtido:", id_token);

      // Enviar para backend
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          id_token: id_token
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.erro || "Erro ao salvar no banco de dados");
      }

      console.log("Dados salvos no backend:", data);

      // SEMPRE enviar email de verificação após cadastro (exceto Google OAuth que já vem verificado)
      // Verificar se é login Google (providerId === 'google.com')
      const isGoogleAuth = user.providerData && user.providerData.some(provider => provider.providerId === 'google.com');
      
      if (!isGoogleAuth && (!user.emailVerified || data.requer_verificacao)) {
        try {
          // Aguardar um pouco para garantir que o usuário foi criado no Firebase
          await new Promise(resolve => setTimeout(resolve, 500));
          
          await sendEmailVerification(user);
          
          alert(
            "Conta criada com sucesso!\n\n" +
            "Um email de verificação foi enviado para " + user.email + ".\n\n" +
            "Por favor, verifique sua caixa de entrada e também a pasta de spam.\n" +
            "O link de verificação expira em 3 dias."
          );
        } catch (emailError) {
          console.error("Erro ao enviar email de verificação:", emailError);
          
          // Mesmo se falhar, informar o usuário
          alert(
            "Conta criada com sucesso!\n\n" +
            "Por favor, verifique seu email para confirmar sua conta.\n" +
            "Se não receber o email, você pode solicitar um novo na página de login."
          );
        }
      } else if (isGoogleAuth) {
        // Login Google já vem com email verificado
        alert("Conta criada com sucesso! Seu email já está verificado.");
      } else {
        alert("Conta criada com sucesso!");
      }

      // Redirecionar para login
      window.location.href = "/auth/login";
      
    } catch (error) {
      console.error("Erro no fluxo de registro:", error);
      alert("Erro ao criar conta: " + error.message);
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
      alert('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    if (password !== confirmPassword) {
      alert('As senhas não coincidem.');
      return;
    }

    if (!terms || !terms.checked) {
      alert('Você precisa aceitar os Termos de Uso e Política de Privacidade.');
      return;
    }

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
      
      alert(errorMessage);
    }
  });

  // Registro com Google
  if (googleRegisterBtn) {
    googleRegisterBtn.addEventListener("click", async function(event) {
      event.preventDefault();
      
      const terms = document.querySelector('input[name="terms"]');
      
      if (!terms || !terms.checked) {
        alert('Você precisa aceitar os Termos de Uso e Política de Privacidade.');
        return;
      }
      
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
        
        alert(errorMessage);
      }
    });
  }
});
