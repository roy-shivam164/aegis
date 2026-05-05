import { useState, useEffect, useCallback } from 'react'
import SkillTree from './components/SkillTree'
import LifeTimeline from './components/LifeTimeline'
import PersonRadar from './components/PersonRadar'
import SystemStatus from './components/SystemStatus'

const API_BASE = '/api'

// ── API hooks ────────────────────────────────────────────────────────────────

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

interface SystemStatus {
  aegis_version: string
  qdrant_url: string
  collections: Record<string, { points_count?: number; status?: string; error?: string }>
  hermes: {
    hermes_home_exists: boolean
    aegis_skills_dir_exists: boolean
    installed_skills: string[]
    telegram_configured: boolean
    discord_configured: boolean
  }
}

// ── App component ─────────────────────────────────────────────────────────────

export default function App() {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null)
  const [statusData, setStatusData] = useState<SystemStatus | null>(null)
  const [skillTree, setSkillTree] = useState<{ skills: unknown[]; total_skills: number; avg_success_rate: number } | null>(null)
  const [lifeLog, setLifeLog] = useState<{ entries: unknown[] } | null>(null)
  const [profiles, setProfiles] = useState<{ profiles: unknown[] } | null>(null)
  const [patterns, setPatterns] = useState<{ patterns: unknown[] } | null>(null)
  const [heartbeatRunning, setHeartbeatRunning] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const loadAll = useCallback(async () => {
    try {
      await fetchJson('/health')
      setApiOnline(true)
    } catch {
      setApiOnline(false)
      return
    }

    const [status, skills, log, profs, pats] = await Promise.allSettled([
      fetchJson<SystemStatus>('/status'),
      fetchJson<{ skills: unknown[]; total_skills: number; avg_success_rate: number }>('/skill-tree'),
      fetchJson<{ entries: unknown[] }>('/life-log?limit=30'),
      fetchJson<{ profiles: unknown[] }>('/profiles'),
      fetchJson<{ patterns: unknown[] }>('/patterns'),
    ])

    if (status.status === 'fulfilled') setStatusData(status.value)
    if (skills.status === 'fulfilled') setSkillTree(skills.value)
    if (log.status === 'fulfilled') setLifeLog(log.value)
    if (profs.status === 'fulfilled') setProfiles(profs.value)
    if (pats.status === 'fulfilled') setPatterns(pats.value)
    setLastRefresh(new Date())
  }, [])

  useEffect(() => {
    loadAll()
    const interval = setInterval(loadAll, 30_000) // auto-refresh every 30s
    return () => clearInterval(interval)
  }, [loadAll])

  const runHeartbeat = async () => {
    if (heartbeatRunning) return
    setHeartbeatRunning(true)
    try {
      await fetch(`${API_BASE}/heartbeat`, { method: 'POST' })
      await loadAll()
    } finally {
      setHeartbeatRunning(false)
    }
  }

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="header">
        <div className="header-logo">
          <span style={{ fontSize: 24 }}>🧠</span>
          <div>
            <div className="logo-text">AEGIS</div>
            <div className="logo-sub">Adaptive Evolving General Intelligence System</div>
          </div>
        </div>

        <div className="header-status">
          <div className={`status-dot ${apiOnline ? '' : 'offline'}`} />
          <span>{apiOnline === null ? 'Connecting…' : apiOnline ? 'Online' : 'API Offline'}</span>
          {lastRefresh && (
            <span style={{ color: 'var(--text-dim)', marginLeft: 8 }}>
              Updated {lastRefresh.toLocaleTimeString()}
            </span>
          )}
          <button
            className="btn btn-ghost"
            onClick={loadAll}
            style={{ marginLeft: 8 }}
          >
            ↻ Refresh
          </button>
          <button
            className="btn btn-primary"
            onClick={runHeartbeat}
            disabled={heartbeatRunning || !apiOnline}
          >
            {heartbeatRunning ? '⚡ Running…' : '⚡ Heartbeat'}
          </button>
        </div>
      </header>

      {/* ── Main grid ──────────────────────────────────────── */}
      <main className="main-content">
        <SkillTree data={skillTree} />
        <LifeTimeline data={lifeLog} patterns={patterns} />
        <PersonRadar data={profiles} />
        <SystemStatus data={statusData} apiOnline={apiOnline} />
      </main>
    </div>
  )
}
