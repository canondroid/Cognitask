import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getHistory } from '@/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function History() {
  const [history, setHistory] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getHistory()
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setHistory([...data.history].reverse()))
      .catch(() => navigate('/login'))
  }, [])

  const fmt = (iso) => new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })

  return (
    <div className="min-h-screen bg-muted/20">
      <header className="border-b bg-background px-6 py-3 flex items-center justify-between">
        <h1 className="text-lg font-semibold">History</h1>
        <Link to="/"><Button variant="ghost" size="sm">← Dashboard</Button></Link>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">All recorded days</CardTitle>
          </CardHeader>
          <CardContent>
            {history === null && <p className="text-sm text-muted-foreground">Loading…</p>}
            {history?.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No days recorded yet. Plan and record your first day on the Dashboard.
              </p>
            )}
            {history?.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground text-left">
                    <th className="pb-2">Date</th>
                    <th className="pb-2">Load</th>
                    <th className="pb-2">Tasks</th>
                    <th className="pb-2">Completion</th>
                    <th className="pb-2">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h, i) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-2">{fmt(h.date)}</td>
                      <td className="py-2 font-mono">{h.planned_load.toFixed(1)}</td>
                      <td className="py-2">{h.task_count}</td>
                      <td className="py-2">{Math.round(h.actual_completion_rate * 100)}%</td>
                      <td className="py-2">
                        <Badge variant={h.success ? 'success' : 'destructive'}>
                          {h.success ? 'Success' : 'Overloaded'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
