import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { plan, record, getStatus, getTodayPlan, commitPlan, logout, getHistory } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import StatusBar from '@/components/StatusBar'
import TaskForm from '@/components/TaskForm'
import PlanResult from '@/components/PlanResult'
import InfoTip from '@/components/InfoTip'

const OUTCOME_TIP = (
  <div className="space-y-1.5">
    <p className="font-medium">The limit only updates when your outcome is surprising — be honest.</p>
    <p>If you planned <strong>above</strong> your limit: only a success (≥70% done) updates the limit upward. Failing was already expected — limit stays put.</p>
    <p>If you planned <strong>within</strong> your limit: only a failure (&lt;70% done) updates the limit downward. Succeeding was already expected — limit stays put.</p>
    <p className="text-muted-foreground">Picking a rosier option than reality means the system won't learn when you genuinely underperformed.</p>
  </div>
)

const COMPLETION_LABELS = [
  { value: 1.0,  label: 'Everything done ✅' },
  { value: 0.85, label: 'Most things done 👍' },
  { value: 0.65, label: 'Struggled a bit 😓' },
  { value: 0.4,  label: 'Overloaded 🚨' },
]

const EFFORT_LABELS = { LOW: '🟢 Low', MEDIUM: '🟡 Medium', HIGH: '🔴 High' }

const DAY_STEPS = ['Plan', 'Analyse', 'Commit', 'Record']

function DayProgress({ currentStep }) {
  return (
    <div className="flex items-center w-full px-1">
      {DAY_STEPS.map((label, i) => {
        const n = i + 1
        const done = n < currentStep
        const active = n === currentStep
        return (
          <div key={label} className={`flex items-center ${i < DAY_STEPS.length - 1 ? 'flex-1' : ''}`}>
            <div className="flex flex-col items-center gap-1 shrink-0">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-colors
                ${done   ? 'bg-primary text-primary-foreground' : ''}
                ${active ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2' : ''}
                ${!done && !active ? 'bg-muted text-muted-foreground' : ''}
              `}>
                {done ? '✓' : n}
              </div>
              <span className={`text-xs whitespace-nowrap ${active ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
                {label}
              </span>
            </div>
            {i < DAY_STEPS.length - 1 && (
              <div className={`flex-1 h-px mx-2 mb-4 transition-colors ${done ? 'bg-primary' : 'bg-muted-foreground/20'}`} />
            )}
          </div>
        )
      })}
    </div>
  )
}

// Convert a saved task (duration in minutes) back to the form shape (hours + minutes)
const toFormTask = (t) => ({
  name: t.name,
  effort: t.effort,
  hours: Math.floor(t.duration / 60),
  minutes: t.duration % 60,
})

const fmtTime = (iso) => {
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const fmtDuration = (mins) => {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h && m) return `${h}h ${m}m`
  if (h) return `${h}h`
  return `${m}m`
}

function RecentDays({ days }) {
  const fmt = (iso) => new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
  return (
    <div className="rounded-lg border bg-background p-4 space-y-3">
      <p className="text-sm font-semibold">Recent Days</p>
      {days.length === 0
        ? <p className="text-xs text-muted-foreground">No days logged yet.</p>
        : <div className="space-y-2">
            {days.map((d, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">{fmt(d.date)}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono">{d.planned_load.toFixed(1)}</span>
                  <span className={`w-2 h-2 rounded-full shrink-0 ${d.success ? 'bg-green-500' : 'bg-red-500'}`} />
                </div>
              </div>
            ))}
          </div>
      }
      <Link to="/history" className="text-xs text-muted-foreground hover:text-foreground block pt-1">
        View all →
      </Link>
    </div>
  )
}

export default function Dashboard() {
  const [status, setStatus]             = useState(null)
  // mode: 'loading' | 'planning' | 'committed'
  const [mode, setMode]                 = useState('loading')
  const [tasks, setTasks]               = useState([])
  const [result, setPlanResult]         = useState(null)
  const [todayPlan, setTodayPlan]       = useState(null)
  const [initialFormTasks, setInitialFormTasks] = useState(null)
  const [editKey, setEditKey]           = useState(0)
  const [completionRate, setCompletionRate] = useState(1.0)
  const [analyzing, setAnalyzing]       = useState(false)
  const [committing, setCommitting]     = useState(false)
  const [recentDays, setRecentDays]     = useState([])
  const [recording, setRecording]       = useState(false)
  const [toast, setToast]               = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      getStatus().then((r) => (r.ok ? r.json() : Promise.reject())),
      getTodayPlan().then((r) => r.json()),
      getHistory().then((r) => (r.ok ? r.json() : { history: [] })),
    ])
      .then(([s, p, h]) => {
        setStatus(s)
        setRecentDays([...h.history].reverse().slice(0, 7))
        if (p) {
          setTodayPlan(p)
          setMode('committed')
        } else {
          setMode('planning')
        }
      })
      .catch(() => navigate('/login'))
  }, [])

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(''), 3000)
  }

  const handleAnalyze = async () => {
    const validTasks = tasks.filter((t) => t.name.trim())
    if (!validTasks.length) return showToast('Add at least one task with a name.')
    setAnalyzing(true)
    try {
      const res = await plan(validTasks)
      const data = await res.json()
      if (!res.ok) return showToast(data.error ?? 'Error analyzing plan')
      setPlanResult(data)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleCommit = async () => {
    const validTasks = tasks.filter((t) => t.name.trim())
    setCommitting(true)
    try {
      const res = await commitPlan(validTasks, result)
      if (!res.ok) return showToast('Error saving plan')
      const saved = {
        tasks: validTasks,
        analysis: result,
        committed_at: new Date().toISOString(),
      }
      setTodayPlan(saved)
      setPlanResult(null)
      setMode('committed')
    } finally {
      setCommitting(false)
    }
  }

  const handleEditPlan = () => {
    setInitialFormTasks(todayPlan.tasks.map(toFormTask))
    setPlanResult(null)
    setEditKey((k) => k + 1)
    setMode('planning')
  }

  const handleRecord = async () => {
    setRecording(true)
    try {
      const res = await record([], completionRate)
      const data = await res.json()
      if (!res.ok) return showToast(data.error ?? 'Error recording outcome')
      showToast(`Outcome recorded! Day ${data.days_recorded} logged.`)
      setTodayPlan(null)
      setInitialFormTasks(null)
      setEditKey((k) => k + 1)
      setMode('planning')
      const [s, h] = await Promise.all([
        getStatus().then((r) => r.json()),
        getHistory().then((r) => r.json()),
      ])
      setStatus(s)
      setRecentDays([...h.history].reverse().slice(0, 7))
    } finally {
      setRecording(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">Cognitask</h1>
        <div className="flex gap-3 items-center">
          <span className="text-sm text-muted-foreground">{status?.username}</span>
          <Link to="/history">
            <Button variant="ghost" size="sm">History</Button>
          </Link>
          <Button variant="ghost" size="sm" onClick={handleLogout}>Logout</Button>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-8 flex gap-6 items-start">
      <main className="flex-1 min-w-0 space-y-6">
        <StatusBar status={status} />

        {mode !== 'loading' && (
          <DayProgress currentStep={
            mode === 'committed' ? 4 :
            result              ? 2 : 1
          } />
        )}

        {mode === 'loading' && (
          <p className="text-sm text-muted-foreground text-center py-8">Loading…</p>
        )}

        {/* ── PLANNING MODE ── */}
        {mode === 'planning' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Today's Tasks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <TaskForm key={editKey} onChange={setTasks} initialTasks={initialFormTasks} />
              <Button onClick={handleAnalyze} className="w-full" disabled={analyzing}>
                {analyzing ? 'Analyzing…' : 'Analyze Plan'}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Analysis result + commit button */}
        {mode === 'planning' && result && (
          <>
            <PlanResult result={result} />
            <Button onClick={handleCommit} className="w-full" variant="default" disabled={committing}>
              {committing ? 'Saving…' : 'Commit Plan for Today'}
            </Button>
          </>
        )}

        {/* ── COMMITTED MODE ── */}
        {mode === 'committed' && todayPlan && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base">Today's Plan</CardTitle>
                  {todayPlan.committed_at && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                      Committed at {fmtTime(todayPlan.committed_at)}
                    </p>
                  )}
                </div>
                <Button variant="outline" size="sm" onClick={handleEditPlan}>
                  Edit Plan
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Task list */}
              <div className="divide-y rounded-md border">
                {todayPlan.tasks.map((t, i) => (
                  <div key={i} className="flex items-center justify-between px-3 py-2 text-sm">
                    <span className="font-medium">{t.name}</span>
                    <div className="flex items-center gap-3 text-muted-foreground">
                      <span>{EFFORT_LABELS[t.effort] ?? t.effort}</span>
                      <span>{fmtDuration(t.duration)}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Analysis summary */}
              {todayPlan.analysis && (
                <div className="flex gap-4 text-sm">
                  <div className="flex-1 rounded-md border px-3 py-2">
                    <p className="text-xs text-muted-foreground">Cognitive Load</p>
                    <p className="text-xl font-bold">{todayPlan.analysis.daily_load?.toFixed(1)}</p>
                  </div>
                  <div className="flex-1 rounded-md border px-3 py-2">
                    <p className="text-xs text-muted-foreground">Overload Risk</p>
                    <p className="text-xl font-bold">
                      {todayPlan.analysis.ml_risk_score != null
                        ? `${Math.round(todayPlan.analysis.ml_risk_score * 100)}%`
                        : '—'}
                    </p>
                  </div>
                </div>
              )}

              {/* Divider */}
              <div className="border-t pt-4">
                <p className="flex items-center gap-1.5 text-sm font-medium mb-3">How did it go? <InfoTip content={OUTCOME_TIP} /></p>
                <div className="space-y-2">
                  {COMPLETION_LABELS.map(({ value, label }) => (
                    <label key={value} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="radio"
                        name="completion"
                        checked={completionRate === value}
                        onChange={() => setCompletionRate(value)}
                        className="accent-primary"
                      />
                      <span className="text-sm">{label}</span>
                    </label>
                  ))}
                </div>
                <Button onClick={handleRecord} disabled={recording} className="w-full mt-4">
                  {recording ? 'Saving…' : 'Record Outcome'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Toast */}
        {toast && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-foreground text-background px-4 py-2 text-sm shadow-lg">
            {toast}
          </div>
        )}
      </main>

      <aside className="hidden lg:block w-64 shrink-0 sticky top-6">
        <RecentDays days={recentDays} />
      </aside>
      </div>
    </div>
  )
}
