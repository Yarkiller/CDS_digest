import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function SearchPill() {
  const inputId = useId()
  const inputRef = useRef(null)
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  useEffect(() => {
    function onKeyDown(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        inputRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  function onSubmit(event) {
    event.preventDefault()
    const q = query.trim()
    navigate(q ? `/knowledge?q=${encodeURIComponent(q)}` : '/knowledge')
  }

  return (
    <form role="search" onSubmit={onSubmit} className="min-w-0 flex-1 basis-[12rem] sm:max-w-xs md:max-w-sm">
      <label htmlFor={inputId} className="sr-only">
        Поиск Digest CDS
      </label>
      <input
        ref={inputRef}
        id={inputId}
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Поиск по базе"
        className="box-border min-h-12 w-full min-w-0 rounded-full border border-rule bg-paper-2 px-4 py-3 text-sm text-ink outline-none placeholder:text-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent sm:min-w-[240px]"
      />
    </form>
  )
}
