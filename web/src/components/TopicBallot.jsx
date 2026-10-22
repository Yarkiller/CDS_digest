import { materialCountLabel, voteCountLabel } from '../utils/ruCount.js'

export default function TopicBallot({ topics, selectedId, onSelect, disabled = false }) {
  return (
    <div role="radiogroup" aria-label="Темы для голосования" className="border-t border-border">
      {topics.map((topic) => {
        const checked = selectedId === topic.id
        const description = (topic.description ?? '').trim()
        return (
          <button
            key={topic.id}
            type="button"
            role="radio"
            aria-checked={checked}
            disabled={disabled}
            onClick={() => onSelect(topic.id)}
            className={[
              'grid w-full grid-cols-[1.5rem_minmax(0,1fr)] gap-4 border-b border-border py-5 text-left',
              checked ? 'bg-primary/15' : 'hover:bg-bg-surface',
              disabled ? 'cursor-not-allowed opacity-70' : '',
            ].join(' ')}
          >
            <span
              className={[
                'mt-1 inline-block size-5 rounded-full border-2',
                checked ? 'border-primary bg-primary' : 'border-field-border bg-bg-app',
              ].join(' ')}
              aria-hidden="true"
            />
            <span>
              <span className="block font-display text-lg font-semibold">{topic.title}</span>
              {description ? (
                <span className="mt-1 block text-sm text-text-secondary">{description}</span>
              ) : null}
              <span className="mt-1 block text-xs text-text-secondary">
                {materialCountLabel(topic.materialsCount ?? 0)} · {voteCountLabel(topic.votes ?? 0)}
              </span>
            </span>
          </button>
        )
      })}
    </div>
  )
}
