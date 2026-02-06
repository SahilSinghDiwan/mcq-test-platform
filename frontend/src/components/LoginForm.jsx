import React, { useState } from 'react'
import { requestOTP, verifyOTP } from '../utils/api'

const LoginForm = ({ onLoginSuccess }) => {
  const [step, setStep] = useState('email')
  const [email, setEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const handleRequestOTP = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      const response = await requestOTP(email)
      setMessage(response.message)
      setStep('otp')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP')
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOTP = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await verifyOTP(email, otp)
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('user_email', response.email)
      onLoginSuccess(response)
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>MCQ Technical Test</h1>
          <p>Assessment Platform</p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleRequestOTP} className="login-form">
            <div className="form-group">
              <label htmlFor="email">Email Address</label>
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
                autoFocus
                disabled={loading}
              />
            </div>

            {error && <div className="error-message">{error}</div>}
            {message && <div className="success-message">{message}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Sending...' : 'Request OTP'}
            </button>

            <div className="info-box">
              <p><strong>Important:</strong></p>
              <ul>
                <li>Single attempt only</li>
                <li>Strict time limits per question</li>
                <li>Tab switching triggers warnings</li>
                <li>Auto-submit after 2 warnings</li>
              </ul>
            </div>
          </form>
        ) : (
          <form onSubmit={handleVerifyOTP} className="login-form">
            <div className="form-group">
              <label htmlFor="otp">Enter OTP</label>
              <input
                type="text"
                id="otp"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength={6}
                required
                autoFocus
                disabled={loading}
                className="otp-input"
              />
              <small>Sent to: {email}</small>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading || otp.length !== 6}>
              {loading ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              className="back-btn"
              onClick={() => {
                setStep('email')
                setOtp('')
                setError('')
              }}
              disabled={loading}
            >
              Back
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default LoginForm