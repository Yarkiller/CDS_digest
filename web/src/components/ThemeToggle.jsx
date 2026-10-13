import { useEffect, useState } from 'react'

const THEME_KEY = 'digest-cds-theme'

export default function ThemeToggle({ className = '', ...rest }) {
  const [isLight, setIsLight] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(THEME_KEY)
    const root = document.documentElement
    if (saved === 'light') {
      root.setAttribute('data-theme', 'light')
      setIsLight(true)
    } else {
      root.removeAttribute('data-theme')
      setIsLight(false)
    }
  }, [])

  function toggle() {
    const root = document.documentElement
    const next = !isLight
    setIsLight(next)
    if (next) {
      root.setAttribute('data-theme', 'light')
      localStorage.setItem(THEME_KEY, 'light')
    } else {
      root.removeAttribute('data-theme')
      localStorage.setItem(THEME_KEY, 'dark')
    }
  }

  return (
    <button
      type="button"
      {...rest}
      onClick={toggle}
      aria-label={isLight ? 'Тёмная тема' : 'Светлая тема'}
      className={`flex h-8 w-8 items-center justify-center rounded-lg border border-border bg-bg-elevated text-text-secondary ${className}`}
    >
      {isLight ? '☽' : '☀'}
    </button>
  )
}
