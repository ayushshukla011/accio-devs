
import { initializeApp } from "firebase/app";
import {
    getAuth,
    GoogleAuthProvider,
    signInWithRedirect,
    signOut,
  } from "firebase/auth";
  
import {
    getFirestore,
    addDoc,
    collection,
    getDocs,
    doc,
  } from "firebase/firestore";

  const firebaseConfig = {
    apiKey: "AIzaSyBCm2j-pWB2cSlfJ3KPTtgHTwNZYrZOdZQ",
    authDomain: "accio-2f266.firebaseapp.com",
    projectId: "accio-2f266",
    storageBucket: "accio-2f266.appspot.com",
    messagingSenderId: "49985640801",
    appId: "1:49985640801:web:b902284195aff880f70d20"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);

export const auth = getAuth(app);

const googleProvider = new GoogleAuthProvider();
// Sign in and sign out functions
export const signInWithGoogleRedirect = () =>
signInWithRedirect(auth, googleProvider);

export const signUserAccountOut = () => signOut(auth);

//create cloud database
export const db=getFirestore(app);

const location = collection(db, "locations");
// Add location to firestore database
export const addLocationtoDb = async (lati,longi) => {
    await addDoc(location, {
      lati,
      longi,
      date: new Date().toJSON().slice(0, 10).replace(/-/g, "/"),
    });
  };

  // Get coordinate from firestore database
export const getCoordinate = async () => {
    const data = await getDocs(location);
    return data.docs.map((doc) => ({ ...doc.data(), id: doc.id }));
  };
