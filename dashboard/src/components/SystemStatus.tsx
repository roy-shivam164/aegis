/**
 * SystemStatus — Shows overall AEGIS health: Qdrant collections,
 * Hermes integration, and configuration status.
 */

interface CollectionInfo {
  points_count?: number
  vectors_count?: number
  status?: string
  error?: string
}

interface StatusData {
  aegis_version: string
  qdrant_url: string
  collections: Record<string, CollectionInfo>
  hermes: {
    hermes_home_exists: boolean
    aegis_skills_dir_exists: boolean
    installed_skills: string[]
    telegram_configured: boolean
    discord_configured: boolean
  }
}

interface Props {
  data: StatusData | null
  apiOnline: boolean | null
}

const COLLECTION_ICONS: Record<string, string> = {
  failure_traces: '❌',
  skill_documents: '📚',
  user_life_log: '📔',
  user_patterns: '🧩',
  person_profiles: '👤',
}

function StatusRow({ label, ok, detail }: { label: string; ok: boolean; detail?: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 0',
        borderBottom: '1px solid var(--border)',
      }}
    >
      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {detail && (
          <span style={{ fontSize: 11, color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
            {detail}
          </span>
        )}
        <span
          style={{
            fontSize: 16,
            lineHeight: 1,
          }}
        >
          {ok ? '✅' : '❌'}
        </span>
      </div>
    </div>
  )
}

export default function SystemStatus({ data, apiOnline }: Props) {
  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">
          <span className="icon">⚡</span> System Status
        </div>
        <span className="card-badge">
          v{data?.aegis_version ?? '—'}
        </span>
      </div>

      {/* ── API / Qdrant ─────────────────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 11,
            color: 'var(--cyan)',
            fontWeight: 600,
            marginBottom: 4,
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}
        >
          Core Services
        </div>
        <StatusRow
          label="AEGIS API"
          ok={apiOnline === true}
          detail={apiOnline ? 'localhost:8000' : 'offline'}
        />
        <StatusRow
          label="Qdrant Vector DB"
          ok={!!data?.qdrant_url}
          detail={data?.qdrant_url?.replace('http://', '') ?? '—'}
        />
      </div>

      {/* ── Collections ──────────────────────────────── */}
      <div style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 11,
            color: 'var(--cyan)',
            fontWeight: 600,
            marginBottom: 4,
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}
        >
          Qdrant Collections
        </div>
        {data?.collections
          ? Object.entries(data.collections).map(([name, info]) => (
              <div
                key={name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '5px 0',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                <span style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', gap: 6 }}>
                  <span>{COLLECTION_ICONS[name] ?? '📦'}</span>
                  <span>{name}</span>
                </span>
                {info.error ? (
                  <span style={{ fontSize: 11, color: 'var(--red)' }}>error</span>
                ) : (
                  <span
                    style={{
                      fontSize: 11,
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--gold)',
                    }}
                  >
                    {(info.points_count ?? 0).toLocaleString()} pts
                  </span>
                )}
              </div>
            ))
          : Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 28, marginBottom: 4 }} />
            ))}
      </div>

      {/* ── Hermes integration ───────────────────────── */}
      {data?.hermes && (
        <div>
          <div
            style={{
              fontSize: 11,
              color: 'var(--cyan)',
              fontWeight: 600,
              marginBottom: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.1em',
            }}
          >
            Hermes Integration
          </div>
          <StatusRow label="Hermes Home" ok={data.hermes.hermes_home_exists} />
          <StatusRow
            label="Skills Installed"
            ok={data.hermes.aegis_skills_dir_exists}
            detail={`${data.hermes.installed_skills.length} skills`}
          />
          <StatusRow
            label="Telegram Gateway"
            ok={data.hermes.telegram_configured}
            detail={data.hermes.telegram_configured ? 'configured' : 'not set'}
          />
          <StatusRow
            label="Discord Gateway"
            ok={data.hermes.discord_configured}
            detail={data.hermes.discord_configured ? 'configured' : 'not set'}
          />

          {data.hermes.installed_skills.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 11, color: 'var(--text-dim)', marginBottom: 4 }}>
                Installed skills:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {data.hermes.installed_skills.map((s) => (
                  <span
                    key={s}
                    style={{
                      fontSize: 10,
                      padding: '2px 6px',
                      background: 'var(--bg-secondary)',
                      border: '1px solid var(--border)',
                      borderRadius: 4,
                      fontFamily: 'var(--font-mono)',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    /{s}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!data && apiOnline === false && (
        <div className="empty-state">
          <div className="empty-icon">🔌</div>
          <div>API offline</div>
          <div style={{ fontSize: 11 }}>
            Start with: uvicorn aegis.api.server:app --reload
          </div>
        </div>
      )}
    </div>
  )
}
