export default function XpBar({ level = 7, current = 340, max = 500, className = '', ...rest }) {
  const ratio = Math.min(1, Math.max(0, current / max))
  return (
    <div {...rest} className={`flex items-center gap-2 ${className}`}>
      <span className="whitespace-nowrap text-[11px] font-bold text-xp">Ур. {level}</span>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-xp-muted">
        <div className="h-full rounded-full bg-xp" style={{ width: `${ratio * 100}%` }} />
      </div>
    </div>
  )
}
