import React from 'react'

const Timer = ({ seconds, totalSeconds }) => {
  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60)
    const remainingSecs = secs % 60
    return `${mins}:${remainingSecs.toString().padStart(2, '0')}`
  }

  const percentage = (seconds / totalSeconds) * 100
  const isWarning = percentage < 25
  const isCritical = percentage < 10

  return (
    <div className={`timer ${isWarning ? 'warning' : ''} ${isCritical ? 'critical' : ''}`}>
      <div className="timer-circle">
        <svg viewBox="0 0 100 100">
          <circle
            className="timer-bg"
            cx="50"
            cy="50"
            r="45"
          />
          <circle
            className="timer-progress"
            cx="50"
            cy="50"
            r="45"
            style={{
              strokeDashoffset: 283 - (283 * percentage) / 100,
            }}
          />
        </svg>
        <div className="timer-text">
          {formatTime(seconds)}
        </div>
      </div>
    </div>
  )
}

export default Timer