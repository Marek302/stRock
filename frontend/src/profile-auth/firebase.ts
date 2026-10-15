import { initializeApp } from 'firebase/app';
import { getAuth, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider, signOut, onAuthStateChanged, type User, browserLocalPersistence } from 'firebase/auth';
import { getFirestore, doc, getDoc, setDoc } from 'firebase/firestore';
import firebaseConfig from './config.json';
import { getAnalytics } from 'firebase/analytics';

export interface UserProfile {
  uid: string;
  email: string;
  displayName: string;
  photoURL: string;
}

export interface AuthUser {
  uid: string;
  email: string;
  displayName: string;
  photoURL?: string;
}

const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
console.log(app)
export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

export const FirebaseService = {
  get currentUser(): User | null {
    return auth.currentUser;
  },
  onAuthChange(callback: (user: User | null) => void) {
    return onAuthStateChanged(auth, callback);
  },
  async signInWithGoogle(): Promise<User> {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  },
  async signInWithEmail(email: string, password: string): Promise<User> {
    const result = await signInWithEmailAndPassword(auth, email, password);
    return result.user;
  },
  async signOut(): Promise<void> {
    if (auth.currentUser) await signOut(auth);
  },
  async getProfile(uid: string): Promise<UserProfile | null> {
    if (!auth.currentUser || auth.currentUser.uid !== uid) return null;
    const snapshot = await getDoc(doc(db, 'users', uid));
    if (snapshot.exists()) {
      const data = snapshot.data();
      return { uid: data.uid || uid, email: data.email || '', displayName: data.displayName || '', photoURL: data.photoURL || '' };
    }
    return null;
  },
  async saveProfile(profile: UserProfile): Promise<void> {
    if (!profile.uid || !auth.currentUser || auth.currentUser.uid !== profile.uid) return;
    await setDoc(doc(db, 'users', profile.uid), {
      uid: profile.uid,
      email: profile.email || auth.currentUser.email || '',
      displayName: profile.displayName || '',
      photoURL: profile.photoURL || '',
      updatedAt: new Date().toISOString(),
    }, { merge: true });
  },
};