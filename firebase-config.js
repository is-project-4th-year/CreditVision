

// TODO: Add SDKs for Firebase products that you want to use

// https://firebase.google.com/docs/web/setup#available-libraries


// Your web app's Firebase configuration

const firebaseConfig = {

  apiKey: "AIzaSyA5apRWxsCdKmX2HaqJHsoYoA_-JsP_IwM",

  authDomain: "my-app-auth-ca94a.firebaseapp.com",

  projectId: "my-app-auth-ca94a",

  storageBucket: "my-app-auth-ca94a.firebasestorage.app",

  messagingSenderId: "794497015602",

  appId: "1:794497015602:web:fdc4b5e1eaf2138071012b"

};
// firebase-config.js


// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Make auth and googleProvider globally available
window.auth = firebase.auth();
window.googleProvider = new firebase.auth.GoogleAuthProvider();

console.log("Firebase initialized successfully!");