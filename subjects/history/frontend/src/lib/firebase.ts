import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';


// REPLACE THESE WITH YOUR FIREBASE CONFIG KEYS
const firebaseConfig = {
  apiKey: "AIzaSyAPK9luTBa3w3DQXjxmCQxNZ8mJcURO_Eg",

  authDomain: "easylearn-fyp-2026.firebaseapp.com",

  projectId: "easylearn-fyp-2026",

  storageBucket: "easylearn-fyp-2026.firebasestorage.app",

  messagingSenderId: "739065040200",

  appId: "1:739065040200:web:357523a69a6d186853377d"

};



const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app);