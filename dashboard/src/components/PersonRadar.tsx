/**
 * PersonRadar — Brain 3 panel showing person profiles, trust scores, and archetypes.
 */
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { useState } from 'react'

interface Profile {
  person_name: string
  relationship: string
  trust_score: number
  interaction_count: number
  traits?: string[]
  motive_signals?: string[]
  last_updated?: string
}

interface Props {
  data: { profiles: Profile[] } | null
}

function trustColor(score: number): string {
  if (score >= 0.7) return 'var(--green)'
  if (score >= 0.4) return 'var(--gold)'
  return 'var(--red)'
}

function trustLabel(score: number): string {
  if (score >= 0.7) return 'High Trust'
  if (score >= 0.4) return 'Moderate'
  return 'Low Trust'
}

export default function PersonRadar({ data }: Props) {
  const [selected, setSelected] = useState<Profile | null>(null)

  if (!data) {
    return (
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <span className="icon">🕵️</span> ShadowReader
          </div>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🕵️</div>
          <div>Loading profiles…</div>
        </div>
      </div>
    )
  }

  const profiles = data.profiles as Profile[]
  const displayProfile = selected ?? profiles[0] ?? null

  // Build radar data from traits if available
  const radarData = displayProfile?.traits?.slice(0, 7).map((t) => ({
    trait: t.replace(/_/g, ' '),
    score: 70 + Math.random() * 30, // visual proxy
  })) ?? []

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="icon">🕵️</span> ShadowReader — Person Profiles
        </div>
        <span className="card-badge">{profiles.length} profiles</span>
      </div>

      {/* ── Profile selector ─────────────────────────── */}
      <div
        style={{
          display: 'flex',
          gap: 6,
          marginBottom: 14,
          flexWrap: 'wrap',
        }}
      >
        {profiles.map((p) => (
          <button
            key={p.person_name}
            className={`btn ${selected?.person_name === p.person_name || (!selected && profiles[0]?.person_name === p.person_name) ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setSelected(p)}
            style={{ fontSize: 11, padding: '3px 10px' }}
          >
            {p.person_name}
          </button>
        ))}
      </div>

      {displayProfile ? (
        <>
          {/* ── Profile header ──────────────────────── */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 14,
              background: 'var(--bg-secondary)',
              borderRadius: 8,
              padding: '10px 14px',
            }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: '50%',
                background: `conic-gradient(${trustColor(displayProfile.trust_score)} ${displayProfile.trust_score * 360}deg, var(--border) 0)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
              }}
            >
              👤
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{displayProfile.person_name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {displayProfile.relationship} • {displayProfile.interaction_count} interactions
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 18,
                  fontFamily: 'var(--font-mono)',
                  color: trustColor(displayProfile.trust_score),
                }}
              >
                {Math.round(displayProfile.trust_score * 100)}
              </div>
              <div
                style={{
                  fontSize: 10,
                  color: trustColor(displayProfile.trust_score),
                  textTransform: 'uppercase',
                }}
              >
                {trustLabel(displayProfile.trust_score)}
              </div>
            </div>
          </div>

          {/* ── Radar ────────────────────────────────── */}
          {radarData.length > 2 && (
            <div style={{ height: 160, marginBottom: 14 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="65%">
                  <PolarGrid stroke="var(--border)" />
                  <PolarAngleAxis
                    dataKey="trait"
                    tick={{ fill: 'var(--text-secondary)', fontSize: 9 }}
                  />
                  <Radar
                    dataKey="score"
                    stroke="var(--purple)"
                    fill="var(--purple)"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                  <Tooltip
                    contentStyle={{
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border)',
                      borderRadius: 8,
                      fontSize: 11,
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* ── Motive signals ───────────────────────── */}
          {displayProfile.motive_signals && displayProfile.motive_signals.length > 0 && (
            <div>
              <div
                style={{
                  fontSize: 11,
                  color: 'var(--text-secondary)',
                  marginBottom: 6,
                  fontWeight: 600,
                }}
              >
                🔍 Motive Signals
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {displayProfile.motive_signals.slice(0, 4).map((sig, i) => (
                  <div
                    key={i}
                    style={{
                      fontSize: 11,
                      padding: '3px 8px',
                      background: 'var(--bg-secondary)',
                      borderRadius: 4,
                      borderLeft: '3px solid var(--purple)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {sig}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-icon">👤</div>
          <div>No profiles yet</div>
          <div style={{ fontSize: 11 }}>Use /aegis-shadow to start profiling</div>
        </div>
      )}
    </div>
  )
}
