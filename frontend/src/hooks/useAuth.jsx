import { useState, useEffect, createContext, useContext } from 'react'
import {
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
  sendEmailVerification,
} from 'firebase/auth'
import { ref, get, set } from 'firebase/database'
import { auth, googleProvider, db } from '../firebase'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [userProfile, setUserProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        // Fetch user profile from database
        const userRef = ref(db, `users/${firebaseUser.uid}`)
        const snapshot = await get(userRef)

        if (snapshot.exists()) {
          const profile = snapshot.val()
          setUserProfile(profile)
          setUser(firebaseUser)

          // Update last login
          await set(ref(db, `users/${firebaseUser.uid}/lastLogin`), Date.now())
        } else {
          // First time user - create profile
          const newProfile = {
            email: firebaseUser.email,
            displayName: firebaseUser.displayName || firebaseUser.email?.split('@')[0],
            photoURL: firebaseUser.photoURL || null,
            role: 'viewer', // Default role
            assignedListings: {},
            createdAt: Date.now(),
            lastLogin: Date.now(),
            isActive: true,
          }
          await set(userRef, newProfile)
          setUserProfile(newProfile)
          setUser(firebaseUser)
        }
      } else {
        setUser(null)
        setUserProfile(null)
      }
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const signInWithGoogle = async () => {
    try {
      await signInWithPopup(auth, googleProvider)
      toast.success('Signed in successfully!')
    } catch (error) {
      console.error('Google sign-in error:', error)
      toast.error(error.message || 'Failed to sign in with Google')
      throw error
    }
  }

  const signInWithEmail = async (email, password) => {
    try {
      const result = await signInWithEmailAndPassword(auth, email, password)
      if (!result.user.emailVerified) {
        toast.error('Please verify your email before signing in')
        await firebaseSignOut(auth)
        return
      }
      toast.success('Signed in successfully!')
    } catch (error) {
      console.error('Email sign-in error:', error)
      let errorMessage = 'Failed to sign in'
      if (error.code === 'auth/user-not-found') {
        errorMessage = 'Email not found'
      } else if (error.code === 'auth/wrong-password') {
        errorMessage = 'Wrong password'
      } else if (error.code === 'auth/invalid-email') {
        errorMessage = 'Invalid email address'
      }
      toast.error(errorMessage)
      throw error
    }
  }

  const signUpWithEmail = async (email, password, displayName) => {
    try {
      const result = await createUserWithEmailAndPassword(auth, email, password)
      await sendEmailVerification(result.user)

      // Create user profile in database
      const userRef = ref(db, `users/${result.user.uid}`)
      await set(userRef, {
        email,
        displayName: displayName || email.split('@')[0],
        photoURL: null,
        role: 'viewer',
        assignedListings: {},
        createdAt: Date.now(),
        lastLogin: Date.now(),
        isActive: true,
      })

      toast.success('Account created! Please check your email to verify your account.')
      await firebaseSignOut(auth)
    } catch (error) {
      console.error('Sign-up error:', error)
      let errorMessage = 'Failed to create account'
      if (error.code === 'auth/email-already-in-use') {
        errorMessage = 'Email already in use'
      } else if (error.code === 'auth/weak-password') {
        errorMessage = 'Password is too weak'
      }
      toast.error(errorMessage)
      throw error
    }
  }

  const resetPassword = async (email) => {
    try {
      await sendPasswordResetEmail(auth, email)
      toast.success('Password reset email sent! Check your inbox.')
    } catch (error) {
      console.error('Password reset error:', error)
      let errorMessage = 'Failed to send reset email'
      if (error.code === 'auth/user-not-found') {
        errorMessage = 'Email not found'
      }
      toast.error(errorMessage)
      throw error
    }
  }

  const signOut = async () => {
    try {
      await firebaseSignOut(auth)
      toast.success('Signed out successfully')
    } catch (error) {
      console.error('Sign-out error:', error)
      toast.error('Failed to sign out')
      throw error
    }
  }

  const value = {
    user,
    userProfile,
    loading,
    signInWithGoogle,
    signInWithEmail,
    signUpWithEmail,
    resetPassword,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
