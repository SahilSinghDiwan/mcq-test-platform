import React, { useState, useEffect } from 'react'
import { getQuestionImage } from '../utils/api'

const QuestionCard = ({ questionNumber, totalQuestions, options, onSubmit, timeLimit }) => {
  const [selectedOption, setSelectedOption] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    const url = getQuestionImage(questionNumber)
    setImageUrl(url)
    setImageError(false)
  }, [questionNumber])

  const handleSubmit = () => {
    if (selectedOption) {
      onSubmit(selectedOption)
    }
  }

  const handleKeyPress = (e) => {
    const key = e.key.toUpperCase()
    if (['A', 'B', 'C', 'D'].includes(key)) {
      setSelectedOption(key)
    } else if (e.key === 'Enter' && selectedOption) {
      handleSubmit()
    }
  }

  useEffect(() => {
    window.addEventListener('keypress', handleKeyPress)
    return () => window.removeEventListener('keypress', handleKeyPress)
  }, [selectedOption])

  return (
    <div className="question-card">
      <div className="question-header">
        <span className="question-number">
          Question {questionNumber} of {totalQuestions}
        </span>
      </div>

      <div className="question-image-container">
        {!imageError ? (
          <img
            src={imageUrl}
            alt={`Question ${questionNumber}`}
            className="question-image"
            onError={() => setImageError(true)}
            draggable="false"
          />
        ) : (
          <div className="image-error">
            Failed to load question image
          </div>
        )}
        
        <div className="watermark">
          {localStorage.getItem('user_email')}
        </div>
      </div>

      <div className="options-container">
        {options.map((option) => (
          <button
            key={option}
            className={`option-btn ${selectedOption === option ? 'selected' : ''}`}
            onClick={() => setSelectedOption(option)}
          >
            <span className="option-letter">{option}</span>
            <span className="option-indicator">
              {selectedOption === option ? '●' : '○'}
            </span>
          </button>
        ))}
      </div>

      <div className="question-actions">
        <button
          className="submit-answer-btn"
          onClick={handleSubmit}
          disabled={!selectedOption}
        >
          Submit Answer
        </button>
      </div>

      <div className="keyboard-hint">
        Press A, B, C, or D to select • Press Enter to submit
      </div>
    </div>
  )
}

export default QuestionCard