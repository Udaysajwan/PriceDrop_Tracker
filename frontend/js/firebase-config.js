// Firebase Web Client Initialization and Auth Helpers
const firebaseConfig = window.FIREBASE_CONFIG || {
  projectId: "backend--api",
  authDomain: "backend--api.firebaseapp.com",
  storageBucket: "backend--api.firebasestorage.app",
  appId: "1:846328447309:web:9ba37faf133d6c02c87704",
  apiKey: window.FIREBASE_API_KEY || "AIzaSyBR-V4fnW5-aVskMlJCvl9rQHIXvbOlsJA",
};

let auth = null;
let googleProvider = null;

function initFirebase() {
  if (typeof firebase === "undefined") {
    console.warn("Firebase SDK script not loaded.");
    return null;
  }
  if (!firebase.apps || !firebase.apps.length) {
    try {
      firebase.initializeApp(firebaseConfig);
    } catch (e) {
      console.warn("Firebase initialization notice:", e);
    }
  }
  auth = firebase.auth();
  googleProvider = new firebase.auth.GoogleAuthProvider();
  return auth;
}

// Sign in with Google Popup
async function signInWithGoogle() {
  if (!auth) initFirebase();
  if (!auth) {
    throw new Error("Firebase Auth is not initialized. Please ensure Firebase SDK is loaded.");
  }
  try {
    const result = await auth.signInWithPopup(googleProvider);
    const idToken = await result.user.getIdToken();
    if (window.api) {
      window.api.setToken(idToken);
    }
    return result.user;
  } catch (error) {
    console.error("Firebase Sign-In Error:", error);
    throw error;
  }
}

// Sign in with Email and Password via Firebase
async function signInWithEmail(email, password) {
  if (!auth) initFirebase();
  if (!auth) throw new Error("Firebase Auth is not initialized.");
  const result = await auth.signInWithEmailAndPassword(email, password);
  const idToken = await result.user.getIdToken();
  if (window.api) {
    window.api.setToken(idToken);
  }
  return result.user;
}

// Sign up with Email and Password via Firebase
async function signUpWithEmail(email, password) {
  if (!auth) initFirebase();
  if (!auth) throw new Error("Firebase Auth is not initialized.");
  const result = await auth.createUserWithEmailAndPassword(email, password);
  const idToken = await result.user.getIdToken();
  if (window.api) {
    window.api.setToken(idToken);
  }
  return result.user;
}

// Send Password Reset Email via Firebase
async function sendPasswordReset(email) {
  if (!auth) initFirebase();
  if (!auth) throw new Error("Firebase Auth is not initialized.");
  return auth.sendPasswordResetEmail(email);
}

// Sign out
async function signOutFirebase() {
  if (!auth) initFirebase();
  if (auth) {
    await auth.signOut();
  }
  if (window.api) {
    window.api.setToken(null);
  }
}

// Listen to Auth state changes
function onFirebaseAuthStateChanged(callback) {
  if (!auth) initFirebase();
  if (auth) {
    auth.onAuthStateChanged(async (user) => {
      if (user) {
        try {
          const idToken = await user.getIdToken();
          if (window.api) {
            window.api.setToken(idToken);
          }
        } catch (err) {
          console.error("Failed to retrieve Firebase ID token:", err);
        }
        callback(user);
      } else {
        if (window.api) {
          window.api.setToken(null);
        }
        callback(null);
      }
    });
  } else {
    callback(null);
  }
}

window.firebaseAuth = {
  initFirebase,
  signInWithGoogle,
  signInWithEmail,
  signUpWithEmail,
  sendPasswordReset,
  signOutFirebase,
  onFirebaseAuthStateChanged,
};
