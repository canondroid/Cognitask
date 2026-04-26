import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Plus, X } from 'lucide-react'
import InfoTip from '@/components/InfoTip'

const EFFORT_TIP = (
  <div className="space-y-1.5">
    <p>How much mental energy this task consumes — not how important it is or how long it takes.</p>
    <p>🟢 <strong>Low</strong> — Routine, automatic. Emails, admin, catch-up calls. You could do it half-asleep.</p>
    <p>🟡 <strong>Medium</strong> — Needs real focus but won't drain you. Code reviews, writing, planning sessions.</p>
    <p>🔴 <strong>High</strong> — Genuinely exhausting. Complex debugging, system design, deep creative work.</p>
    <p className="text-muted-foreground">Quick test: "Would I need a break after this?" → If yes, it's High.</p>
    <p className="font-medium">⚠️ This is your most important input — it drives everything else.</p>
  </div>
)

const DURATION_TIP = (
  <div className="space-y-1.5">
    <p>How long you plan to spend on this task.</p>
    <p>Duration amplifies the cognitive cost — especially for High effort tasks. A 3-hour deep-work session costs significantly more than a 1-hour one of the same effort level.</p>
    <p className="text-muted-foreground">Tip: Be realistic. Underestimating leads to underestimating your day's load.</p>
  </div>
)

const EFFORT_OPTIONS = ['LOW', 'MEDIUM', 'HIGH']
const EFFORT_LABELS = { LOW: '🟢 Low', MEDIUM: '🟡 Medium', HIGH: '🔴 High' }

const blank = () => ({ name: '', effort: 'MEDIUM', hours: 1, minutes: 0 })

export default function TaskForm({ onChange, initialTasks }) {
  const [tasks, setTasks] = useState(initialTasks ?? [blank()])

  useEffect(() => {
    onChange(tasks.map(({ hours, minutes, ...rest }) => ({
      ...rest,
      duration: Math.max(5, hours * 60 + minutes),
    })))
  }, [tasks])

  const update = (i, field, value) =>
    setTasks((prev) => prev.map((t, idx) => (idx === i ? { ...t, [field]: value } : t)))

  const add = () => setTasks((prev) => [...prev, blank()])
  const remove = (i) => setTasks((prev) => prev.filter((_, idx) => idx !== i))

  return (
    <div className="space-y-3">
      {tasks.map((task, i) => (
        <div key={i} className="flex flex-wrap gap-2 items-end">
          <div className="flex flex-col gap-1 w-full sm:flex-1">
            {i === 0 && <label className="text-xs text-muted-foreground">Task Name</label>}
            <Input
              placeholder="Task name"
              value={task.name}
              onChange={(e) => update(i, 'name', e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            {i === 0 && <label className="flex items-center gap-1 text-xs text-muted-foreground">Mental Effort <InfoTip below content={EFFORT_TIP} /></label>}
            <select
              value={task.effort}
              onChange={(e) => update(i, 'effort', e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {EFFORT_OPTIONS.map((o) => (
                <option key={o} value={o}>{EFFORT_LABELS[o]}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            {i === 0 && <label className="flex items-center gap-1 text-xs text-muted-foreground">Duration <InfoTip below content={DURATION_TIP} /></label>}
            <div className="flex items-center gap-1">
              <Input
                type="number"
                min={0}
                max={23}
                value={task.hours}
                onChange={(e) => update(i, 'hours', Math.max(0, Math.min(23, Number(e.target.value))))}
                className="w-14 text-center"
              />
              <span className="text-sm text-muted-foreground">hr</span>
              <Input
                type="number"
                min={0}
                max={55}
                step={5}
                value={task.minutes}
                onChange={(e) => update(i, 'minutes', Math.max(0, Math.min(55, Number(e.target.value))))}
                className="w-14 text-center"
              />
              <span className="text-sm text-muted-foreground">min</span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => remove(i)}
            disabled={tasks.length === 1}
            className="mb-0.5"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button variant="outline" size="sm" onClick={add} className="w-full">
        <Plus className="h-4 w-4 mr-1" /> Add Task
      </Button>
    </div>
  )
}
