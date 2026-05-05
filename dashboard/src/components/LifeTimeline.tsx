/**
 * LifeTimeline — Brain 2 panel showing recent life log entries and detected patterns.
 */
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface LogEntry {
  id: string
  raw_text: string
  mood: string
  category: string
  importance: number
  timestamp: string
  actionable: boolean
  deadline_mentioned?: string
}

interface Pattern {
  id: string
  pattern_type: string
  description: string
  confidence: number
  category: string
}

interface Props {
  data: { entries: LogEntry[] } | null
  patterns: { patterns: Pattern[] } | null
}

const MOOD_EMOJI: Record<string, string> = {
  happy: '😊',
  stressed: '😰',
  sad: '😔',
  motivated: '💪',
  neutral: '😐',
}

const MOOD_SCORE: Record<string, number> = {
  happy: 85,
  motivated: 80,
  neutral: 50,
  sad: 25,
  stressed: 20,
}

export default function LifeTimeline({ data, patterns }: Props) {
  if (!data) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span className="icon">🪞</span> MirrorSelf
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🪞</div>
          <div>Loading life timeline…</div>
        </div>
      </div>
    )
  }

  const entries = data.entries as LogEntry[]
  const patternList = patterns?.patterns as Pattern[] | undefined

  // Build mood chart data from recent entries
  const chartData = entries
    .slice(0, 14)
    .reverse()
    .map((e, i) => ({
      idx: i + 1,
      mood: MOOD_SCORE[e.mood] ?? 50,
      importance: Math.round(e.importance * 100),
      label: e.mood,
    }))

  const recentMoods = entries.slice(0, 5).map((e) => e.mood)
  const dominantMood = recentMoods.length
    ? recentMoods.reduce((a, b) =>
        recentMoods.filter((m) => m === a).length >= recentMoods.filter((m) => m === b).length
          ? a
          : b
      )
    : 'neutral'

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="icon">🪞</span> MirrorSelf — Life Timeline
        </div>
        <span className="card-badge">{entries.length} entries</span>
      </div>

      {/* ── Mood chart ────────────────────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 11,
            color: 'var(--text-secondary)',
            marginBottom: 6,
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <span>Mood trajectory (recent 14 entries)</span>
          <span>
            Current: {MOOD_EMOJI[dominantMood]} {dominantMood}
          </span>
        </div>
        <div style={{ height: 80 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="moodGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--cyan)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="var(--cyan)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="idx" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  fontSize: 11,
                }}
                formatter={(v: number, _: string, props: { payload?: { label?: string } }) => [
                  `${props.payload?.label ?? ''} (${v})`,
                  'Mood',
                ]}
              />
              <Area
                type="monotone"
                dataKey="mood"
                stroke="var(--cyan)"
                fill="url(#moodGrad)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Patterns ─────────────────────────────────── */}
      {patternList && patternList.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div
            style={{ fontSize: 11, color: 'var(--gold)', marginBottom: 6, fontWeight: 600 }}
          >
            ✨ Detected Patterns
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {patternList.slice(0, 3).map((p) => (
              <div
                key={p.id}
                style={{
                  fontSize: 11,
                  color: 'var(--text-secondary)',
                  background: 'var(--bg-secondary)',
                  borderRadius: 6,
                  padding: '4px 8px',
                  borderLeft: '3px solid var(--gold)',
                }}
              >
                {p.description.slice(0, 80)}
                {p.description.length > 80 ? '…' : ''}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Recent entries ────────────────────────────── */}
      <ul className="data-list">
        {entries.slice(0, 8).map((entry) => (
          <li className="data-item" key={entry.id}>
            <span className="item-icon">{MOOD_EMOJI[entry.mood] ?? '📝'}</span>
            <div className="item-body">
              <div
                className="item-title"
                style={{ display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {entry.raw_text.slice(0, 60)}
                  {entry.raw_text.length > 60 ? '…' : ''}
                </span>
                <span className={`mood-badge mood-${entry.mood}`}>{entry.mood}</span>
              </div>
              <div className="item-meta">
                {entry.category} •{' '}
                {new Date(entry.timestamp).toLocaleDateString()}{' '}
                {entry.deadline_mentioned && (
                  <span style={{ color: 'var(--orange)' }}>⏰ {entry.deadline_mentioned}</span>
                )}
                {entry.actionable && <span style={{ color: 'var(--cyan)' }}> · actionable</span>}
              </div>
            </div>
          </li>
        ))}
        {entries.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📖</div>
            <div>No life log entries yet</div>
            <div style={{ fontSize: 11 }}>Use /aegis-mirror to start logging</div>
          </div>
        )}
      </ul>
    </div>
  )
}
