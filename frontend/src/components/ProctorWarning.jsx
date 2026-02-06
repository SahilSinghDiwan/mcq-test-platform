import React from 'react'

const ProctorWarning = ({ warningCount, maxWarnings, onClose }) => {
  const remainingWarnings = maxWarnings - warningCount
  const isFinal = remainingWarnings <= 0

  return (
    <div className="modal-overlay">
      <div className={`modal-content ${isFinal ? 'final-warning' : ''}`}>
        <div className="warning-icon">⚠️</div>
        
        <h2>{isFinal ? 'Test Auto-Submitted' : 'Warning!'}</h2>
        
        <p className="warning-message">
          {isFinal ? (
            'Your test has been automatically submitted due to excessive warnings.'
          ) : (
            <>
              You switched tabs or lost focus!
              <br />
              <strong>Warning {warningCount} of {maxWarnings}</strong>
            </>
          )}
        </p>

        {!isFinal && (
          <div className="warning-details">
            <p>
              <strong>{remainingWarnings}</strong> warning{remainingWarnings !== 1 ? 's' : ''} remaining
            </p>
            <p className="warning-note">
              Next warning will auto-submit your test!
            </p>
          </div>
        )}

        <button className="modal-btn" onClick={onClose}>
          {isFinal ? 'View Results' : 'I Understand'}
        </button>
      </div>
    </div>
  )
}

export default ProctorWarning