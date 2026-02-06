import { useState, useEffect, useCallback } from 'react'

export const useTimer = (initialSeconds, onExpire) => {
  const [seconds, setSeconds] = useState(initialSeconds)
  const [isRunning, setIsRunning] = useState(false)
  const [hasExpired, setHasExpired] = useState(false)

  useEffect(() => {
    setSeconds(initialSeconds)
    setHasExpired(false)
  }, [initialSeconds])

  useEffect(() => {
    if (!isRunning || hasExpired) return

    if (seconds <= 0) {
      setHasExpired(true)
      setIsRunning(false)
      if (onExpire) onExpire()
      return
    }

    const interval = setInterval(() => {
      setSeconds((prev) => {
        if (prev <= 1) {
          setHasExpired(true)
          setIsRunning(false)
          if (onExpire) onExpire()
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [isRunning, seconds, hasExpired, onExpire])

  const start = useCallback(() => {
    setIsRunning(true)
  }, [])

  const stop = useCallback(() => {
    setIsRunning(false)
  }, [])

  const reset = useCallback((newSeconds) => {
    setSeconds(newSeconds || initialSeconds)
    setIsRunning(false)
    setHasExpired(false)
  }, [initialSeconds])

  const getElapsedTime = useCallback(() => {
    return initialSeconds - seconds
  }, [initialSeconds, seconds])

  return {
    seconds,
    isRunning,
    hasExpired,
    start,
    stop,
    reset,
    getElapsedTime,
  }
}