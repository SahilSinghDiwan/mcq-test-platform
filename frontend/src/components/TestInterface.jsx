import React, { useState, useEffect } from 'react'
import { startTest, getQuestion, submitAnswer, completeTest } from '../utils/api'
import { useProctor } from '../hooks/useProctor'
import { useTimer } from '../hooks/useTimer'
import QuestionCard from './QuestionCard'
import Timer from './Timer'
import ProctorWarning from './ProctorWarning'

const TestInterface = ({ user }) => {
  const [testState, setTestState] = useState('pre-start')
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [questionNumber, setQuestionNumber] = useState(1)
  const [totalQuestions, setTotalQuestions] = useState(20)
  const [timeLimit, setTimeLimit] = useState(120)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)
  const [showWarning, setShowWarning] = useState(false)

  const { blurCount, warningCount, shouldAutoSubmit } = useProctor(testState === 'in-progress')
  
  const timer = useTimer(timeLimit, async () => {
    await handleSubmitAnswer(null, true)
  })

  useEffect(() => {
    if (shouldAutoSubmit && testState === 'in-progress') {
      handleCompleteTest('auto_blur')
    }
  }, [shouldAutoSubmit])

  useEffect(() => {
    if (warningCount > 0 && testState === 'in-progress') {
      setShowWarning(true)
    }
  }, [warningCount])

  const handleStartTest = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await startTest()
      setTotalQuestions(response.total_questions)
      setTimeLimit(response.time_limit_per_question)
      setTestState('in-progress')
      await loadQuestion(1, response.time_limit_per_question)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start test')
    } finally {
      setLoading(false)
    }
  }

  const loadQuestion = async (qNum, tLimit) => {
    setLoading(true)
    setError('')

    try {
      const question = await getQuestion(qNum)
      setCurrentQuestion(question)
      setQuestionNumber(qNum)
      timer.reset(tLimit || question.time_limit_seconds)
      timer.start()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load question')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitAnswer = async (selectedOption, isAutoSubmit = false) => {
    if (!selectedOption && !isAutoSubmit) return

    setLoading(true)
    timer.stop()

    try {
      const timeTaken = timer.getElapsedTime()
      const response = await submitAnswer(
        questionNumber,
        selectedOption || 'A',
        timeTaken
      )

      if (response.next_question_number) {
        await loadQuestion(response.next_question_number, timeLimit)
      } else {
        await handleCompleteTest('user_completed')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit answer')
      timer.start()
    } finally {
      setLoading(false)
    }
  }

  const handleCompleteTest = async (reason) => {
    setLoading(true)

    try {
      const result = await completeTest(reason)
      setResults(result)
      setTestState('completed')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to complete test')
    } finally {
      setLoading(false)
    }
  }

  if (testState === 'pre-start') {
    return (
      <div className="test-interface">
        <div className="pre-start-screen">
          <h1>Ready to Begin?</h1>
          <p>Welcome, {user.email}</p>

          <div className="test-info">
            <div className="info-item">
              <span className="info-label">Total Questions:</span>
              <span className="info-value">{totalQuestions}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Time per Question:</span>
              <span className="info-value">{timeLimit}s</span>
            </div>
            <div className="info-item">
              <span className="info-label">Attempts:</span>
              <span className="info-value">1</span>
            </div>
          </div>

          <div className="rules-box">
            <h3>Critical Rules</h3>
            <ul>
              <li>No tab switching</li>
              <li>Strict time limits</li>
              <li>One attempt only</li>
              <li>Auto-submit after 2 warnings</li>
            </ul>
          </div>

          {error && <div className="error-message">{error}</div>}

          <button
            className="start-test-btn"
            onClick={handleStartTest}
            disabled={loading}
          >
            {loading ? 'Starting...' : 'Start Test'}
          </button>
        </div>
      </div>
    )
  }

  if (testState === 'completed') {
    return (
      <div className="test-interface">
        <div className="results-screen">
          <div className="results-icon">✓</div>
          <h1>Test Completed!</h1>
          
          {results && (
            <div className="results-summary">
              <div className="result-item">
                <span className="result-label">Score:</span>
                <span className="result-value">
                  {results.correct_answers} / {results.total_questions}
                </span>
              </div>
              <div className="result-item">
                <span className="result-label">Accuracy:</span>
                <span className="result-value">{results.accuracy_percentage}%</span>
              </div>
              <div className="result-item">
                <span className="result-label">Total Time:</span>
                <span className="result-value">
                  {Math.floor(results.total_time_seconds / 60)} min
                </span>
              </div>
              {results.blur_count > 0 && (
                <div className="result-item warning">
                  <span className="result-label">Warnings:</span>
                  <span className="result-value">{results.warnings_issued}</span>
                </div>
              )}
            </div>
          )}

          <p className="results-message">
            Thank you for completing the assessment.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="test-interface lockdown">
      <div className="test-header">
        <div className="test-progress">
          Question {questionNumber} of {totalQuestions}
        </div>
        <Timer seconds={timer.seconds} totalSeconds={timeLimit} />
      </div>

      {currentQuestion && (
        <QuestionCard
          questionNumber={currentQuestion.question_number}
          totalQuestions={currentQuestion.total_questions}
          options={currentQuestion.options}
          onSubmit={handleSubmitAnswer}
          timeLimit={currentQuestion.time_limit_seconds}
        />
      )}

      {loading && <div className="loading-overlay">Loading...</div>}
      {error && <div className="error-banner">{error}</div>}

      {showWarning && (
        <ProctorWarning
          warningCount={warningCount}
          maxWarnings={2}
          onClose={() => setShowWarning(false)}
        />
      )}
    </div>
  )
}

export default TestInterface