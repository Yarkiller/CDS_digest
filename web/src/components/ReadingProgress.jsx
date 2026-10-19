import { useEffect, useRef } from 'react'

/**
 * Scroll affordance that sits directly under the sticky header.
 *
 * Mirrors `initReadingProgress()` in design-frontend/scripts/app.js and the
 * `.reading-progress` element in design-frontend/pages/material.html: the bar is
 * collapsed with `scaleX(0)` and scaled to the read fraction of the document.
 * Decorative only, so it is hidden from assistive technology.
 */
export default function ReadingProgress() {
  const barRef = useRef(null)

  useEffect(() => {
    const node = barRef.current
    if (!node) return undefined

    function updateProgress() {
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight
      const ratio = maxScroll > 0 ? window.scrollY / maxScroll : 1
      node.style.transform = `scaleX(${Math.max(0, Math.min(1, ratio))})`
    }

    window.addEventListener('scroll', updateProgress, { passive: true })
    window.addEventListener('resize', updateProgress)
    updateProgress()

    return () => {
      window.removeEventListener('scroll', updateProgress)
      window.removeEventListener('resize', updateProgress)
    }
  }, [])

  return (
    <div
      ref={barRef}
      className="reading-progress"
      data-testid="reading-progress"
      aria-hidden="true"
    />
  )
}
