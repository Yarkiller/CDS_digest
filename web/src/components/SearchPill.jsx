import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * New id per submission. The quantity lives in the id's *history*, not in the URL.
 * A plain marker: never a variant of the URL, never a query fragment.
 */
let submitSeq = 0

function createSubmitId() {
  submitSeq += 1
  return `${Date.now()}-${submitSeq}`
}

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
    if (!q) {
      navigate('/knowledge')
      return
    }
    // The pill knows nothing about the search layer: it hands over a URL and an opaque
    // one-shot marker (D-05). KnowledgePage decides what the marker means.
    // `state` must ride in the SECOND argument: the data router builds the location with
    // `createLocation(loc, path, opts && opts.state, …)` and silently ignores `to.state`.
    navigate({ pathname: '/knowledge', search: `?q=${encodeURIComponent(q)}` }, {
      // C-07: a submission REPLACES — Back must leave /knowledge instead of walking back
      // through query variants.
      replace: true,
      state: { submitId: createSubmitId() },
    })
  }

  return (
    <form
      role="search"
      onSubmit={onSubmit}
      className="min-w-0 flex-1 basis-[12rem] sm:min-w-[280px] sm:max-w-sm"
    >
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
        className="box-border min-h-12 w-full min-w-0 rounded-full border border-field-border bg-bg-surface px-4 py-3 text-sm text-text-primary outline-none placeholder:text-text-disabled focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary sm:min-w-[240px]"
      />
    </form>
  )
}
