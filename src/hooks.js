import { useRef, useState, useEffect, useCallback } from 'preact/hooks'

const useEventListener = (eventName, handler, element = global) => {
  const savedHandler = useRef()

  useEffect(() => { savedHandler.current = handler }, [handler])

  useEffect(
    () => {
      const isSupported = element && element.addEventListener
      if (!isSupported) return

      const eventListener = event => savedHandler.current(event)
      element.addEventListener(eventName, eventListener)
      return () => {
        element.removeEventListener(eventName, eventListener)
      }
    },
    [eventName, element]
  )
}

function computeSwipeDirection (gesture, tolerance) {
  const dx = gesture.x.pop() - gesture.x[0]
  const dy = gesture.y.pop() - gesture.y[0]
  const absdx = Math.abs(dx)
  const absdy = Math.abs(dy)

  if (absdx < tolerance && dy > tolerance) {
    return 'down'
  } else if (dy < tolerance && absdx < tolerance && absdy > tolerance) {
    return 'up'
  } else if (dx < tolerance && absdx > tolerance && absdy < tolerance) {
    return 'left'
  } else if (dx > tolerance && absdy < tolerance) {
    return 'right'
  }
  return null
}

const useSwipe = (handler, element, tolerance = 100) => {
  const [gesture, setGesture] = useState({ x: [], y: [] })
  const savedHandler = useRef()

  useEffect(() => { savedHandler.current = handler }, [handler])

  const trace = useCallback(
    (ev) => {
      gesture.x.push(ev.touches[0].clientX)
      gesture.y.push(ev.touches[0].clientY)
      setGesture(gesture)
    },
    [gesture, setGesture]
  )

  const compute = useCallback(
    (ev) => {
      ev.preventDefault()
      const direction = computeSwipeDirection(gesture, tolerance)
      if (direction !== null) { savedHandler.current(direction) }
      setGesture({ x: [], y: [] })
    },
    [gesture, setGesture]
  )

  useEventListener('touchstart', trace, element)
  useEventListener('touchmove', trace, element)
  useEventListener('touchend', compute, element)
}

export {
  useEventListener,
  useSwipe
}
