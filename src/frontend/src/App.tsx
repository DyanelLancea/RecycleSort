import { FormEvent, useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  api,
  clearSession,
  isAuthed,
  loadUser,
  saveSession,
  type ScanLog,
  type ScanResult,
  type User,
} from './api'

type View = 'login' | 'register' | 'upload' | 'results' | 'profile' | 'info' | 'admin'

function Field({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div>
      <label>{label}</label>
      {children}
    </div>
  )
}

export default function App() {
  const [view, setView] = useState<View>(isAuthed() ? 'upload' : 'login')
  const [user, setUser] = useState<User | null>(loadUser())
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [result, setResult] = useState<ScanResult | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [logs, setLogs] = useState<ScanLog[]>([])
  const [adminKey, setAdminKey] = useState('dev-admin-api-key-not-for-production')
  const [leaderboard, setLeaderboard] = useState<{ email: string; points: number }[]>([])
  const [adminLogs, setAdminLogs] = useState<ScanLog[]>([])
  const [health, setHealth] = useState<string>('')

  useEffect(() => {
    if (!isAuthed()) return
    api
      .me()
      .then((fresh) => {
        setUser(fresh)
        const token = localStorage.getItem('recyclesort.token')
        if (token) saveSession(token, fresh)
      })
      .catch(() => {
        clearSession()
        setUser(null)
        setView('login')
      })
  }, [])

  const navItems = useMemo(() => {
    const items: { id: View; label: string; needsAuth?: boolean }[] = [
      { id: 'upload', label: 'Scan', needsAuth: true },
      { id: 'results', label: 'Last result', needsAuth: true },
      { id: 'profile', label: 'Profile', needsAuth: true },
      { id: 'info', label: 'Recycling info' },
      { id: 'admin', label: 'Admin' },
    ]
    return items.filter((item) => !item.needsAuth || user)
  }, [user])

  function go(next: View) {
    setError('')
    setNotice('')
    setView(next)
  }

  async function onAuth(event: FormEvent<HTMLFormElement>, mode: 'login' | 'register') {
    event.preventDefault()
    setError('')
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email') || '')
    const password = String(form.get('password') || '')
    setBusy(true)
    try {
      const payload = mode === 'login' ? await api.login(email, password) : await api.register(email, password)
      saveSession(payload.access_token, payload.user)
      setUser(payload.user)
      setNotice(mode === 'login' ? 'Signed in.' : 'Account created.')
      setView('upload')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed')
    } finally {
      setBusy(false)
    }
  }

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    const form = new FormData(event.currentTarget)
    const file = form.get('file')
    if (!(file instanceof File) || file.size === 0) {
      setError('Choose a JPEG, PNG, or WebP image first.')
      return
    }
    setBusy(true)
    try {
      const scan = await api.upload(file)
      setResult(scan)
      setUser((current) => (current ? { ...current, points: scan.total_points } : current))
      const token = localStorage.getItem('recyclesort.token')
      if (token && user) saveSession(token, { ...user, points: scan.total_points })
      setView('results')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  async function loadProfile() {
    setError('')
    try {
      const [profile, mine] = await Promise.all([api.profile(), api.myLogs()])
      setUser(profile)
      setLogs(mine)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load profile')
    }
  }

  async function loadAdmin(event: FormEvent) {
    event.preventDefault()
    setError('')
    try {
      const [board, rows] = await Promise.all([api.adminBoard(adminKey), api.adminLogs(adminKey)])
      setLeaderboard(board)
      setAdminLogs(rows)
      setNotice('Admin data loaded.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Admin request failed')
    }
  }

  async function pingHealth() {
    try {
      const data = await api.health()
      setHealth(data.status)
    } catch {
      setHealth('unreachable')
    }
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand" onClick={() => go(user ? 'upload' : 'login')}>
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <div>
            <h1>RecycleSort</h1>
            <p>Photograph waste. Learn the bin. Earn points.</p>
          </div>
        </div>
        <nav className="nav">
          {!user && (
            <>
              <button className={view === 'login' ? 'active' : ''} onClick={() => go('login')}>
                Sign in
              </button>
              <button className={view === 'register' ? 'active' : ''} onClick={() => go('register')}>
                Register
              </button>
            </>
          )}
          {navItems.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? 'active' : ''}
              onClick={() => {
                go(item.id)
                if (item.id === 'profile') void loadProfile()
              }}
            >
              {item.label}
            </button>
          ))}
          {user && (
            <button
              className="danger"
              onClick={() => {
                clearSession()
                setUser(null)
                setResult(null)
                go('login')
              }}
            >
              Sign out
            </button>
          )}
        </nav>
      </header>

      {error && <div className="banner error">{error}</div>}
      {notice && <div className="banner ok">{notice}</div>}

      {view === 'login' && (
        <section className="card">
          <h2>Sign in</h2>
          <p className="muted">Use the account you registered on this instance. Passwords are hashed with bcrypt; sessions use JWT.</p>
          <form onSubmit={(event) => void onAuth(event, 'login')}>
            <Field label="Email">
              <input name="email" type="email" required autoComplete="email" />
            </Field>
            <Field label="Password">
              <input name="password" type="password" required minLength={8} autoComplete="current-password" />
            </Field>
            <button className="primary" disabled={busy} type="submit">
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </section>
      )}

      {view === 'register' && (
        <section className="card">
          <h2>Create an account</h2>
          <p className="muted">Minimum 8 characters. You start at 0 points; each valid scan adds at least 1.</p>
          <form onSubmit={(event) => void onAuth(event, 'register')}>
            <Field label="Email">
              <input name="email" type="email" required autoComplete="email" />
            </Field>
            <Field label="Password">
              <input name="password" type="password" required minLength={8} autoComplete="new-password" />
            </Field>
            <button className="primary" disabled={busy} type="submit">
              {busy ? 'Creating…' : 'Register'}
            </button>
          </form>
        </section>
      )}

      {view === 'upload' && user && (
        <section className="grid two">
          <form className="card" onSubmit={(event) => void onUpload(event)}>
            <h2>Scan an item</h2>
            <p className="muted">
              JPEG, PNG, or WebP, up to 5 MB. The API rejects missing, oversized, wrong-type, and corrupted files with HTTP 400.
            </p>
            <div className="drop">
              <input
                name="file"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  setPreview(file ? URL.createObjectURL(file) : null)
                }}
              />
              {preview && <p><img className="preview" src={preview} alt="Selected waste item" /></p>}
            </div>
            <div className="row">
              <button className="primary" disabled={busy} type="submit">
                {busy ? 'Classifying…' : 'Classify image'}
              </button>
              <span className="muted">Signed in as {user.email} · {user.points} pts</span>
            </div>
          </form>
          <aside className="card">
            <h3>How scoring works</h3>
            <ul className="info-list">
              <li>+1 point for every successful scan</li>
              <li>+4 bonus if the item is treated as recyclable</li>
              <li>Classes: paper, plastic, metal (mock model until `analytics/` exports weights)</li>
            </ul>
          </aside>
        </section>
      )}

      {view === 'results' && (
        <section className="card">
          <h2>Classification result</h2>
          {!result ? (
            <p className="muted">No scan in this session yet. Upload an image from the Scan page.</p>
          ) : (
            <div className="result-hero">
              <div>
                <span className="pill">{result.is_recyclable ? 'Recyclable' : 'Not recyclable'}</span>
                <h3 style={{ textTransform: 'capitalize', marginBottom: 0 }}>{result.predicted_class}</h3>
                <p className="muted">
                  Confidence {(result.confidence * 100).toFixed(1)}%
                  {result.model_loaded ? '' : ' · using mock inference'}
                </p>
              </div>
              <div className="stat">
                <span className="muted">Points this scan</span>
                <b>+{result.points_awarded}</b>
              </div>
              <div className="stat">
                <span className="muted">Total points</span>
                <b>{result.total_points}</b>
              </div>
            </div>
          )}
        </section>
      )}

      {view === 'profile' && user && (
        <section className="card">
          <h2>Your profile</h2>
          <p>
            <strong>{user.email}</strong>
            <br />
            Total points: <strong>{user.points}</strong>
          </p>
          {logs.length === 0 ? (
            <p className="muted">No scans logged yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>When</th>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Recyclable</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((row) => (
                  <tr key={row.id}>
                    <td>{new Date(row.created_at).toLocaleString()}</td>
                    <td>{row.predicted_class}</td>
                    <td>{(row.confidence * 100).toFixed(1)}%</td>
                    <td>{row.is_recyclable ? 'yes' : 'no'}</td>
                    <td>+{row.points_awarded}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {view === 'info' && (
        <section className="card">
          <h2>Campus recycling</h2>
          <p>
            RecycleSort is a coursework prototype for INF2006. It is meant to sit on AWS (EC2, load balancer, auto scaling,
            RDS or DynamoDB) and keep secrets in Parameter Store — not in the git repo.
          </p>
          <ul className="info-list">
            <li><strong>Paper</strong> — dry, uncoated office paper and cardboard. Food-soiled fibre goes to general waste.</li>
            <li><strong>Plastic</strong> — empty bottles and tubs with recycling marks. Soft film is usually not accepted on campus.</li>
            <li><strong>Metal</strong> — rinsed cans and foil. Aerosol canisters need the hazardous stream.</li>
          </ul>
          <p className="muted">This page is informational. Classification in the app is a model prediction, not a legal waste ruling.</p>
        </section>
      )}

      {view === 'admin' && (
        <section className="card">
          <h2>Admin dashboard</h2>
          <p className="muted">
            The admin key is loaded as if from AWS Parameter Store (`SSM_ADMIN_API_KEY`). The local example value is
            pre-filled.
          </p>
          <form onSubmit={(event) => void loadAdmin(event)}>
            <Field label="Admin API key">
              <input value={adminKey} onChange={(event) => setAdminKey(event.target.value)} type="password" />
            </Field>
            <div className="row">
              <button className="primary" type="submit">
                Load logs and leaderboard
              </button>
              <button
                className="ghost"
                type="button"
                onClick={() => {
                  void pingHealth()
                }}
              >
                Check /health
              </button>
              {health && <span className="pill">health: {health}</span>}
            </div>
          </form>
          <h3>Leaderboard</h3>
          {leaderboard.length === 0 ? (
            <p className="muted">No rows yet.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Points</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((row) => (
                  <tr key={row.email}>
                    <td>{row.email}</td>
                    <td>{row.points}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <h3>Scan logs</h3>
          {adminLogs.length === 0 ? (
            <p className="muted">No scans recorded.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Points</th>
                  <th>When</th>
                </tr>
              </thead>
              <tbody>
                {adminLogs.map((row) => (
                  <tr key={row.id}>
                    <td>{row.user_email ?? row.user_id}</td>
                    <td>{row.predicted_class}</td>
                    <td>{(row.confidence * 100).toFixed(1)}%</td>
                    <td>+{row.points_awarded}</td>
                    <td>{new Date(row.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      <p className="footer-note">INF2006 stub · FastAPI + React · health checks on /health for the load balancer</p>
    </div>
  )
}
