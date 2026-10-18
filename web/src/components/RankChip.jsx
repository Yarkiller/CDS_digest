import { Link } from 'react-router-dom'

export default function RankChip({ rank = 8, className = '', ...rest }) {
  return (
    <Link
      {...rest}
      to="/leaderboard"
      className={`rounded-md border border-primary/30 bg-primary/15 px-2.5 py-1 font-mono text-xs font-semibold text-primary no-underline ${className}`}
    >
      #{rank}
    </Link>
  )
}
