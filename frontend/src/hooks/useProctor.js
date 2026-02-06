import { useEffect, useState } from 'react'
import { logProctorEvent } from '../utils/api'

export const useProctor = (isActive = false) => {
  const [blurCount, setBlurCount] = useState(0)
  const [warningCount, setWarningCount] = useState(0)
  const [shouldAutoSubmit, setShouldAutoSubmit] = useState(false)

  useEffect(() => {
    if (!isActive) return

    const handleContextMenu = (e) => {
      e.preventDefault()
      logProctorEvent('right_click', 'Right-click attempted')
    }

    document.addEventListener('contextmenu', handleContextMenu)
    return () => document.removeEventListener('contextmenu', handleContextMenu)
  }, [isActive])

  useEffect(() => {
    if (!isActive) return

    const handleCopy = (e) => {
      e.preventDefault()
      logProctorEvent('copy_attempt', 'Copy attempted')
    }

    const handlePaste = (e) => {
      e.preventDefault()
      logProctorEvent('paste_attempt', 'Paste attempted')
    }

    const handleCut = (e) => {
      e.preventDefault()
      logProctorEvent('cut_attempt', 'Cut attempted')
    }

    document.addEventListener('copy', handleCopy)
    document.addEventListener('paste', handlePaste)
    document.addEventListener('cut', handleCut)

    return () => {
      document.removeEventListener('copy', handleCopy)
      document.removeEventListener('paste', handlePaste)
      document.removeEventListener('cut', handleCut)
    }
  }, [isActive])

  useEffect(() => {
    if (!isActive) return

    const handleKeyDown = (e) => {
      if (
        e.key === 'F12' ||
        (e.ctrlKey && e.shiftKey && e.key === 'I') ||
        (e.ctrlKey && e.shiftKey && e.key === 'J') ||
        (e.ctrlKey && e.key === 'U')
      ) {
        e.preventDefault()
        logProctorEvent('devtools_attempt', `Key: ${e.key}`)
      }

      if (e.ctrlKey && (e.key === 'c' || e.key === 'v' || e.key === 'x')) {
        e.preventDefault()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isActive])

  useEffect(() => {
    if (!isActive) return

    const handleVisibilityChange = async () => {
      if (document.hidden) {
        const newBlurCount = blurCount + 1
        setBlurCount(newBlurCount)

        try {
          const response = await logProctorEvent('blur', `Tab switch #${newBlurCount}`)
          setWarningCount(response.warning_count)
          setShouldAutoSubmit(response.should_auto_submit)
        } catch (error) {
          console.error('Failed to log blur event:', error)
        }
      }
    }

    const handleBlur = async () => {
      const newBlurCount = blurCount + 1
      setBlurCount(newBlurCount)

      try {
        const response = await logProctorEvent('blur', `Focus lost #${newBlurCount}`)
        setWarningCount(response.warning_count)
        setShouldAutoSubmit(response.should_auto_submit)
      } catch (error) {
        console.error('Failed to log blur event:', error)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('blur', handleBlur)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('blur', handleBlur)
    }
  }, [isActive, blurCount])

  useEffect(() => {
    if (!isActive) return

    document.body.style.userSelect = 'none'
    document.body.style.webkitUserSelect = 'none'
    document.body.style.mozUserSelect = 'none'
    document.body.style.msUserSelect = 'none'

    return () => {
      document.body.style.userSelect = ''
      document.body.style.webkitUserSelect = ''
      document.body.style.mozUserSelect = ''
      document.body.style.msUserSelect = ''
    }
  }, [isActive])

  return {
    blurCount,
    warningCount,
    shouldAutoSubmit,
  }
}