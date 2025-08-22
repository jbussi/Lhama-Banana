import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js';
import { getAuth, signInWithEmailAndPassword } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js';

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

const submit = document.getElementById("submit");

submit.addEventListener("click", function(event) {
  event.preventDefault();

  const email    = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  signInWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    const user = userCredential.user;
    // const uid = user.uid; // UID já é acessível via user.uid se necessário

    console.log("Usuário logado com sucesso no Firebase:", user);
    
    // CORREÇÃO: Use user.displayName ou user.email para a mensagem de boas-vindas
    const userNameOrEmail = user.displayName || user.email;
    alert(`Bem-vindo, ${userNameOrEmail}!`); // Use a variável definida

    // Pega o ID Token JWT do Firebase, que deve ser enviado para backend
    return user.getIdToken(); // Retorna a Promise do token diretamente
  })
  .then((id_token) => { // id_token é o resultado da Promise anterior
      console.log("ID Token obtido:", id_token);

      // Fetch com os dados corretos, enviando o token para validação no backend
      return fetch("http://localhost:80/api/login_user", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          id_token: id_token  // Token para backend validar
        })
      });
  })
  .then((response) => {
    if (!response.ok) {
      // Se a resposta não for OK (status 4xx ou 5xx), tenta ler a mensagem de erro do backend
      return response.json().then(err => { throw new Error(err.erro || "Erro desconhecido no backend"); });
    }
    return response.json(); // CORREÇÃO: Espere JSON, não texto
  })
  .then((data) => {
    console.log("Resposta do servidor:", data);
    window.location.href = "/perfil"; // Redireciona para a página de perfil
  })
  .catch((error) => {
    console.error("Erro no fluxo de login:", error.message);
    alert("Erro ao logar: " + error.message);
  });
});