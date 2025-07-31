import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getAuth, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";
// TODO: Add SDKs for Firebase products that you want to use
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

  const email    = document.getElementById("email").value;
  const password = document.getElementById("password").value;

signInWithEmailAndPassword(auth, email, password)
  .then((userCredential) => {
    const user = userCredential.user;
    const uid = user.uid;
    console.log("Usuário logado com sucesso:", user);
    alert("Bem-vindo!");

    // Agora que o UID está definido, você pode usá-lo aqui
    return fetch("http://localhost:80/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ uid: uid })
    });
  })
  .then((response) => {
    if (!response.ok) {
      throw new Error("Erro no backend");
    }
    return response.text();
  })
  .then((data) => {
    console.log("Resposta do servidor:", data);
  })
  .catch((error) => {
    console.error("Erro ao logar usuário ou enviar UID:", error.message);
    alert("Erro: " + error.message);
  });
});