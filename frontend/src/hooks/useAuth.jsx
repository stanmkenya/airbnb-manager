import { useState, useEffect, createContext, useContext } from 'react'
import {
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  sendPasswordResetEmail,
} from 'firebase/auth'
import { doc, getDoc, setDoc, updateDoc } from 'firebase/firestore'
import { auth, googleProvider, firestore } from '../firebase'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [userProfile, setUserProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      try {
        if (firebaseUser) {
          console.log('[Auth] User logged in:', firebaseUser.uid, firebaseUser.email)

          // Fetch user profile from Firestore
          const userRef = doc(firestore, 'users', firebaseUser.uid)
          console.log('[Auth] Fetching user profile from Firestore...')
          const snapshot = await getDoc(userRef)

          if (snapshot.exists()) {
            const profile = { id: snapshot.id, ...snapshot.data() }
            console.log('[Auth] User profile loaded:', profile)
            setUserProfile(profile)
            setUser(firebaseUser)

            // Update last login (non-blocking - don't fail login if this fails)
            try {
              await updateDoc(userRef, {
                lastLogin: Date.now()
              })
              console.log('[Auth] Last login timestamp updated')
            } catch (updateError) {
              console.warn('[Auth] Failed to update lastLogin (non-critical):', updateError.message)
              // Don't fail the entire login process if lastLogin update fails
            }
          } else {
            console.log('[Auth] No profile found, creating new profile...')
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
            await setDoc(userRef, newProfile)
            console.log('[Auth] New profile created:', newProfile)
            setUserProfile({ id: firebaseUser.uid, ...newProfile })
            setUser(firebaseUser)
          }
        } else {
          console.log('[Auth] No user logged in')
          setUser(null)
          setUserProfile(null)
        }
      } catch (error) {
        console.error('[Auth] Error in auth state change:', error)
        toast.error('Failed to load user profile. Please try again.')
        setUser(null)
        setUserProfile(null)
      } finally {
        setLoading(false)
      }
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
      await signInWithEmailAndPassword(auth, email, password)
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

      // Create user profile in Firestore
      const userRef = doc(firestore, 'users', result.user.uid)
      await setDoc(userRef, {
        email,
        displayName: displayName || email.split('@')[0],
        photoURL: null,
        role: 'viewer',
        assignedListings: {},
        createdAt: Date.now(),
        lastLogin: Date.now(),
        isActive: true,
      })

      toast.success('Account created successfully! You can now sign in.')
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
