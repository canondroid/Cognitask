import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import InfoTip from '@/components/InfoTip'

const LOAD_TIP = (
  <div className="space-y-1.5">
    <p>Your total mental workload for the day — calculated from every task's effort level and duration.</p>
    <p>This number means nothing in isolation. What matters is how it compares to your personal capacity limit shown above.</p>
    <p>Below limit → manageable &nbsp;&nbsp; Near limit → tight &nbsp;&nbsp; Above limit → risk of overload</p>
  </div>
)

const CAPACITY_TIP = (
  <div className="space-y-1.5">
    <p>Shows how your planned load compares to your current capacity limit — which is still calibrating from your onboarding answers.</p>
    <p>Within your capacity — comfortable, room to spare.</p>
    <p>Near your capacity — manageable, no buffer.</p>
    <p>Slightly / Well over capacity — above your current estimate, but the limit may still be adjusting to you.</p>
    <p className="text-muted-foreground">Personalised risk prediction unlocks after 15 logged days.</p>
  </div>
)

const RISK_TIP = (
  <div className="space-y-1.5">
    <p>A personalised prediction of how likely this day is to feel overwhelming, based on your own history.</p>
    <p>It considers: total load, number of tasks, how many are High effort, day of the week, and your load vs. capacity ratio.</p>
    <p className="text-muted-foreground">This is a second opinion — not a rule. Use it to prompt reflection, not to decide for you.</p>
  </div>
)

const NUDGE_STYLES = {
  info:    'bg-blue-50 border-blue-200 text-blue-800',
  caution: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  warning: 'bg-red-50 border-red-200 text-red-800',
}

const riskColor = (score) => {
  if (score < 0.4) return 'bg-green-500'
  if (score < 0.7) return 'bg-yellow-500'
  return 'bg-red-500'
}

const capacityLabel = (ratio) => {
  if (ratio < 0.85) return 'Within your capacity'
  if (ratio <= 1.0)  return 'Near your capacity'
  if (ratio <= 1.3)  return 'Slightly over capacity'
  return 'Well over capacity'
}

export default function PlanResult({ result }) {
  if (!result) return null
  const { daily_load, current_limit, ml_risk_score, nudge_message, nudge_severity, breakdown, feature_importance } = result
  const mlAvailable = ml_risk_score != null

  return (
    <div className="space-y-4">
      {/* Load score + risk/capacity */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
            <span className="flex items-center gap-1">Cognitive Load <InfoTip content={LOAD_TIP} /></span>
          </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">{daily_load.toFixed(1)}</p>
            <p className="text-xs text-muted-foreground mt-1">{breakdown.total_time_minutes} min total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              <span className="flex items-center gap-1">
                {mlAvailable ? 'Overload Risk' : 'vs. Your Capacity'}
                <InfoTip content={mlAvailable ? RISK_TIP : CAPACITY_TIP} />
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {mlAvailable ? (
              <>
                <p className="text-4xl font-bold">{Math.round(ml_risk_score * 100)}%</p>
                <div className="mt-2 h-2 w-full rounded-full bg-muted">
                  <div
                    className={`h-2 rounded-full ${riskColor(ml_risk_score)}`}
                    style={{ width: `${ml_risk_score * 100}%` }}
                  />
                </div>
              </>
            ) : current_limit != null ? (
              <>
                <p className="text-2xl font-semibold">{capacityLabel(daily_load / current_limit)}</p>
                <div className="mt-2 h-2 w-full rounded-full bg-muted">
                  <div
                    className="h-2 rounded-full bg-muted-foreground/40"
                    style={{ width: `${Math.min((daily_load / current_limit) * 100, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {daily_load.toFixed(1)} planned · {current_limit.toFixed(1)} limit · calibrating
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground mt-2">Complete onboarding to see capacity</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Nudge alert */}
      {nudge_message && (
        <div className={`rounded-lg border p-4 text-sm ${NUDGE_STYLES[nudge_severity] ?? NUDGE_STYLES.info}`}>
          {nudge_message}
        </div>
      )}

      {/* Effort distribution */}
      <div className="flex gap-2">
        <Badge variant="success">Low: {breakdown.effort_distribution.low}</Badge>
        <Badge variant="warning">Medium: {breakdown.effort_distribution.medium}</Badge>
        <Badge variant="destructive">High: {breakdown.effort_distribution.high}</Badge>
      </div>

      {/* Task breakdown table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Task Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground">
                <th className="pb-2 text-left">Task</th>
                <th className="pb-2 text-right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {breakdown.task_costs.map(([name, cost]) => (
                <tr key={name} className="border-b last:border-0">
                  <td className="py-2">{name}</td>
                  <td className="py-2 text-right font-mono">{cost.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
