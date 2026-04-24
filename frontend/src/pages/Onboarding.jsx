import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { onboarding } from '@/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const STEPS = [
  {
    key: 'hours',
    question: 'How many hours of deep, focused work can you sustain in a day?',
    hint: 'Think about studying, coding, writing — tasks that take real mental effort.',
    options: [
      { value: '1-2', label: '1–2 hours', description: 'I tire quickly on heavy tasks' },
      { value: '3-4', label: '3–4 hours', description: 'I can push through a solid half-day' },
      { value: '5+',  label: '5+ hours',  description: 'I can sustain deep work most of the day' },
    ],
  },
  {
    key: 'tendency',
    question: 'When planning your day, how do you tend to behave?',
    hint: 'Be honest — this helps the system calibrate faster.',
    options: [
      { value: 'over',  label: 'I often take on too much', description: 'My to-do list is usually longer than my day' },
      { value: 'right', label: 'I usually get it about right', description: 'I finish most of what I plan' },
      { value: 'under', label: 'I tend to plan less than I can do', description: 'I often have energy left over' },
    ],
  },
  {
    key: 'schedule',
    question: 'How would you describe your typical daily schedule?',
    hint: 'Consider your classes, work, and commitments combined.',
    options: [
      { value: 'light',    label: 'Light',    description: 'Few commitments, lots of free time' },
      { value: 'moderate', label: 'Moderate', description: 'Balanced — busy but manageable' },
      { value: 'heavy',    label: 'Heavy',    description: 'Back-to-back — packed from morning to night' },
    ],
  },
]

export default function Onboarding() {
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({ hours: null, tendency: null, schedule: null })
  const [loading, setLoading] = useState(false)
  const [confirmed, setConfirmed] = useState(null)
  const navigate = useNavigate()

  const current = STEPS[step]
  const selected = answers[current.key]

  const handleSkip = async () => {
    setLoading(true)
    await onboarding({ skip: true })
    navigate('/')
  }

  const handleNext = () => {
    if (step < STEPS.length - 1) {
      setStep(step + 1)
    } else {
      handleSubmit()
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    const res = await onboarding(answers)
    const data = await res.json()
    setConfirmed(data.starting_limit)
    setLoading(false)
  }

  if (confirmed !== null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-muted/30">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <CardTitle className="text-2xl">You're all set 🎯</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              Based on your answers, your starting cognitive capacity is:
            </p>
            <p className="text-5xl font-bold">{confirmed.toFixed(1)}</p>
            <p className="text-sm text-muted-foreground">
              The system will refine this as you record your days. It gets more accurate over time.
            </p>
            <Button className="w-full" onClick={() => navigate('/')}>
              Go to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-muted-foreground">
              Step {step + 1} of {STEPS.length}
            </span>
            <button
              onClick={handleSkip}
              disabled={loading}
              className="text-xs text-muted-foreground underline hover:text-foreground"
            >
              Skip for now
            </button>
          </div>
          {/* Progress bar */}
          <div className="h-1.5 w-full rounded-full bg-muted">
            <div
              className="h-1.5 rounded-full bg-primary transition-all"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
          <CardTitle className="text-lg mt-4">{current.question}</CardTitle>
          <p className="text-sm text-muted-foreground">{current.hint}</p>
        </CardHeader>
        <CardContent className="space-y-3">
          {current.options.map((opt) => (
            <label
              key={opt.value}
              className={`flex items-start gap-3 rounded-lg border p-4 cursor-pointer transition-colors ${
                selected === opt.value
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-muted/50'
              }`}
            >
              <input
                type="radio"
                name={current.key}
                value={opt.value}
                checked={selected === opt.value}
                onChange={() => setAnswers({ ...answers, [current.key]: opt.value })}
                className="mt-0.5 accent-primary"
              />
              <div>
                <p className="font-medium text-sm">{opt.label}</p>
                <p className="text-xs text-muted-foreground">{opt.description}</p>
              </div>
            </label>
          ))}

          <div className="flex gap-3 pt-2">
            {step > 0 && (
              <Button variant="outline" onClick={() => setStep(step - 1)} className="flex-1">
                Back
              </Button>
            )}
            <Button
              onClick={handleNext}
              disabled={!selected || loading}
              className="flex-1"
            >
              {loading ? 'Saving…' : step < STEPS.length - 1 ? 'Next' : 'See my estimate'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
