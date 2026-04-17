import { useState, useEffect } from 'react'
import { getCurrentUser, signIn, signOut, fetchAuthSession } from 'aws-amplify/auth'

interface AuthState {
  isAuthenticated: boolean
  isLoading: boolean
  user: { username: string; email?: string } | null
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    isLoading: true,
    user: null,
  })

  useEffect(() => {
    checkAuth()
  }, [])

  async function checkAuth() {
    try {
      const user = await getCurrentUser()
      const session = await fetchAuthSession()
      const email = session.tokens?.idToken?.payload?.email as string | undefined
      setState({ isAuthenticated: true, isLoading: false, user: { username: user.username, email } })
    } catch {
      setState({ isAuthenticated: false, isLoading: false, user: null })
    }
  }

  async function login(username: string, password: string) {
    const result = await signIn({ username, password })
    if (result.isSignedIn) {
      await checkAuth()
    }
    return result
  }

  async function logout() {
    await signOut()
    setState({ isAuthenticated: false, isLoading: false, user: null })
  }

  return { ...state, login, logout }
}
