import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getAuth, createUserWithEmailAndPassword } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
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

// Aguarda o DOM estar pronto
document.addEventListener('DOMContentLoaded', function() {
  const submit = document.getElementById("submit");

  if (!submit) {
    console.error("Botão de submit não encontrado");
    return;
  }

  submit.addEventListener("click", function(event) {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const email    = document.getElementById("email").value;
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

    createUserWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    const user = userCredential.user;

    // Pega o ID Token JWT do Firebase, que deve ser enviado para backend
    return user.getIdToken().then((id_token) => {
      console.log("Usuário criado com sucesso:", user);
      alert(`Bem-vindo, ${username}!`);

      // Agora sim, fetch com os dados corretos, enviando o token para validação no backend
      return fetch("/api/register_user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          username: username,
          id_token: id_token  // Token para backend validar
        })
      });
    });
  })
  .then(async response => {
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.erro || "Erro ao salvar no banco de dados");
    }
    console.log("Dados salvos no backend:", data);
    alert("Conta criada com sucesso!");
    window.location.href = "/auth/login";
  })
  .catch(error => {
    console.error("Erro no backend ou criação:", error);
    alert("Erro ao criar conta: " + error.message);
  });
  });
});

