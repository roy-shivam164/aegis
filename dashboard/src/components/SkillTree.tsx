/**
 * SkillTree — Brain 1 panel showing skill evolution, success rates, and tree structure.
 */
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface Skill {
  id: string
  skill_name: string
  version: number
  success_rate: number
  total_uses: number
  last_evolved?: string
}

interface SkillTreeData {
  skills: Skill[]
  total_skills: number
  avg_success_rate: number
}

interface Props {
  data: SkillTreeData | null
}

export default function SkillTree({ data }: Props) {
  if (!data) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span className="icon">🔨</span> SkillForge
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🔨</div>
          <div>Loading skill tree…</div>
        </div>
      </div>
    )
  }

  const radarData = data.skills.slice(0, 8).map((s) => ({
    skill: s.skill_name.replace('_', ' '),
    successRate: Math.round(s.success_rate * 100),
    uses: Math.min(s.total_uses, 100),
  }))

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="icon">🔨</span> SkillForge — Skill Tree
        </div>
        <span className="card-badge">{data.total_skills} skills</span>
      </div>

      {/* ── Stats ────────────────────────────────────── */}
      <div className="stat-row">
        <div className="stat-chip">
          <div className="stat-value">{data.total_skills}</div>
          <div className="stat-label">Skills</div>
        </div>
        <div className="stat-chip">
          <div className="stat-value" style={{ color: 'var(--green)' }}>
            {Math.round(data.avg_success_rate * 100)}%
          </div>
          <div className="stat-label">Avg Success</div>
        </div>
        <div className="stat-chip">
          <div className="stat-value" style={{ color: 'var(--cyan)' }}>
            {data.skills.reduce((s, sk) => s + sk.total_uses, 0)}
          </div>
          <div className="stat-label">Total Uses</div>
        </div>
      </div>

      {/* ── Radar chart ──────────────────────────────── */}
      {radarData.length > 0 && (
        <div style={{ height: 200, marginBottom: 16 }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fill: 'var(--text-secondary)', fontSize: 10 }}
              />
              <Radar
                name="Success Rate"
                dataKey="successRate"
                stroke="var(--cyan)"
                fill="var(--cyan)"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                }}
                formatter={(v: number) => [`${v}%`, 'Success Rate']}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* ── Skill list ────────────────────────────────── */}
      <ul className="data-list">
        {data.skills.map((skill) => (
          <li className="data-item" key={skill.id}>
            <span className="item-icon">⚙️</span>
            <div className="item-body">
              <div className="item-title">
                {skill.skill_name}
                <span
                  style={{
                    marginLeft: 6,
                    fontSize: 10,
                    color: 'var(--text-dim)',
                    fontFamily: 'var(--font-mono)',
                  }}
                >
                  v{skill.version}
                </span>
              </div>
              <div style={{ marginTop: 4 }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: 10,
                    color: 'var(--text-secondary)',
                    marginBottom: 4,
                  }}
                >
                  <span>{Math.round(skill.success_rate * 100)}% success</span>
                  <span>{skill.total_uses} uses</span>
                </div>
                <div className="progress-bar-container">
                  <div
                    className="progress-bar-fill cyan"
                    style={{ width: `${skill.success_rate * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </li>
        ))}
        {data.skills.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">🌱</div>
            <div>No skills yet — failures will create them</div>
          </div>
        )}
      </ul>
    </div>
  )
}
