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

const submit = document.getElementById("submit");

submit.addEventListener("click", function(event) {
  event.preventDefault();

  const username = document.getElementById("username").value;
  const email    = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  createUserWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    const user = userCredential.user;

    // Pega o ID Token JWT do Firebase, que deve ser enviado para backend
    return user.getIdToken().then((id_token) => {
      console.log("Usuário criado com sucesso:", user);
      alert(`Bem-vindo, ${username}!`);

      // Agora sim, fetch com os dados corretos, enviando o token para validação no backend
      return fetch("http://localhost:80/api/register_user", {
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
  .then(response => {
    if (!response.ok) throw new Error("Erro ao salvar no banco de dados");
    return response.json();
  })
  .then(data => {
    console.log("Dados salvos no backend:", data);
    window.location.href = "/login";
  })
  .catch(error => {
    console.error("Erro no backend ou criação:", error.message);
  });
});

