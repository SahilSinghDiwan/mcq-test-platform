import React, { useState, useEffect } from 'react'
import LoginForm from './components/LoginForm'
import TestInterface from './components/TestInterface'
import './styles/index.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    const email = localStorage.getItem('user_email')

    if (token && email) {
      setUser({ email })
    }

    setLoading(false)
  }, [])

  const handleLoginSuccess = (userData) => {
    setUser({
      id: userData.user_id,
      email: userData.email,
      status: userData.status,
    })
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_email')
    setUser(null)
  }

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
      </div>
    )
  }

  return (
    <div className="app">
      {!user ? (
        <LoginForm onLoginSuccess={handleLoginSuccess} />
      ) : (
        <TestInterface user={user} onLogout={handleLogout} />
      )}
    </div>
  )
}

export default App