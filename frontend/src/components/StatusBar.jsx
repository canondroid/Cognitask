import { Badge } from '@/components/ui/badge'
import InfoTip from '@/components/InfoTip'

const LIMIT_TIP = (
  <div className="space-y-1.5">
    <p>Your personal sustainable daily cognitive load — the level where you typically finish the day without feeling wrecked.</p>
    <p>It only updates when something <strong>surprising</strong> happens: succeeding on a day you planned above your limit (limit rises), or failing on a day you planned within it (limit falls). Expected outcomes don't move it.</p>
    <p className="text-muted-foreground">Well-calibrated after about 15 logged days.</p>
  </div>
)

function getConfig(days) {
  if (days >= 15) return {
    badge: 'Fully Personalized',
    variant: 'success',
    headline: 'Your planner knows you',
    subtext: 'Keep logging to stay calibrated',
  }
  if (days === 0) return {
    badge: 'Getting Started',
    variant: 'secondary',
    headline: 'Ready to plan your first day',
    subtext: 'Log 15 days to unlock risk prediction',
  }
  const toML = 15 - days
  return {
    badge: 'Building Your Profile',
    variant: 'secondary',
    headline: 'Capacity tracking is live',
    subtext: `Risk prediction unlocks in ${toML} day${toML === 1 ? '' : 's'}`,
  }
}

export default function StatusBar({ status }) {
  if (!status) return null

  const days = status.days_recorded ?? 0
  const { badge, variant, headline, subtext } = getConfig(days)
  const pct = Math.min((days / 15) * 100, 100)

  return (
    <div className="rounded-lg border bg-muted/40 px-4 py-3 space-y-2.5 text-sm">
      {/* Top row: badge + headline + capacity */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Badge variant={variant}>{badge}</Badge>
          <span className="text-muted-foreground truncate">{headline}</span>
        </div>
        <span className="flex items-center gap-1 text-muted-foreground whitespace-nowrap shrink-0">
          {status.current_limit != null
            ? `Capacity limit: ${status.current_limit.toFixed(1)}`
            : 'Capacity calibrating…'}
          {status.current_limit != null && <InfoTip below content={LIMIT_TIP} />}
        </span>
      </div>

      {/* Progress bar */}
      <div className="space-y-1">
        <div className="relative h-1.5 w-full rounded-full bg-muted-foreground/20">
          <div
            className="h-1.5 rounded-full bg-primary transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{subtext}</span>
          <span>{days >= 15 ? '✓ Day 15' : `Day ${days} / 15`}</span>
        </div>
      </div>
    </div>
  )
}
