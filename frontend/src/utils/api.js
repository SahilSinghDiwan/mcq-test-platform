import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user_email')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export const requestOTP = async (email) => {
  const response = await api.post('/auth/request-otp', { email })
  return response.data
}

export const verifyOTP = async (email, otp) => {
  const response = await api.post('/auth/verify-otp', { email, otp })
  localStorage.setItem('access_token', response.data.access_token)
  localStorage.setItem('user_email', response.data.email)
  return response.data
}

export const startTest = async () => {
  const response = await api.post('/test/start')
  return response.data
}

export const getQuestion = async (questionNumber) => {
  const response = await api.get(`/test/question/${questionNumber}`)
  return response.data
}

export const getQuestionImage = (questionNumber) => {
  const token = localStorage.getItem('access_token')
  return `${API_BASE_URL}/test/image/${questionNumber}?token=${token}&t=${Date.now()}`
}

export const submitAnswer = async (questionNumber, selectedOption, timeTaken) => {
  const response = await api.post('/test/submit-answer', {
    question_number: questionNumber,
    selected_option: selectedOption,
    time_taken_seconds: timeTaken,
  })
  return response.data
}

export const getTestStatus = async () => {
  const response = await api.get('/test/status')
  return response.data
}

export const completeTest = async (reason = 'user_completed') => {
  const response = await api.post('/test/complete', { reason })
  return response.data
}

export const logProctorEvent = async (eventType, details = null) => {
  const response = await api.post('/test/proctor-event', {
    event_type: eventType,
    details,
    timestamp: new Date().toISOString(),
  })
  return response.data
}

export default api