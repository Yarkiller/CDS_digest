import { Link } from 'react-router-dom'

/**
 * Knowledge / issue hit row. Links by slug (KNOW-01 / D-59).
 * cover_url/cover may be null — degrade without thumbnail (Q2).
 */
export default function MaterialListRow({ material }) {
  const slug = material.slug ?? material.id
  const cover = material.cover_url ?? material.cover ?? null
  const tags = material.tags ?? []

  return (
    <Link
      to={`/materials/${slug}`}
      className="grid grid-cols-[4rem_minmax(0,1fr)] gap-4 border-b border-rule py-5 text-inherit no-underline hover:bg-paper-2 sm:grid-cols-[5rem_minmax(0,1fr)]"
    >
      {cover ? (
        <img
          src={cover}
          alt=""
          width={480}
          height={270}
          className="h-10 w-16 rounded-md border border-rule object-cover sm:h-11 sm:w-20"
        />
      ) : (
        <div
          aria-hidden="true"
          className="h-10 w-16 rounded-md border border-rule bg-paper-2 sm:h-11 sm:w-20"
        />
      )}
      <div className="min-w-0">
        <h3 className="font-display text-lg font-semibold">{material.title}</h3>
        {material.snippet ? (
          <p className="mt-1 text-sm text-ink-2">{material.snippet}</p>
        ) : null}
        {tags.length > 0 ? (
          <div className="mt-2 flex flex-wrap gap-2">
            {tags.map((tag) => (
              <span key={tag} className="rounded-full bg-paper-2 px-2 py-0.5 text-xs text-accent">
                #{tag}
              </span>
            ))}
          </div>
        ) : null}
      </div>
    </Link>
  )
}
