import { useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from 'react'
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

type View = 'home' | 'login' | 'register' | 'upload' | 'profile' | 'admin'

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string
  htmlFor: string
  children: ReactNode
}) {
  return (
    <div>
      <label htmlFor={htmlFor}>{label}</label>
      {children}
    </div>
  )
}

type Bin = 'blue' | 'special' | 'general'

const BIN_LABELS: Record<Bin, string> = {
  blue: 'Blue recycling bin',
  special: 'Special collection point',
  general: 'General waste bin',
}

// Photos live in public/materials/<id>.jpg. Until one is added, a placeholder box is shown instead.
const MATERIALS: { id: string; name: string; bin: Bin; examples: string; tip: string }[] = [
  {
    id: 'paper',
    name: 'Paper',
    bin: 'blue',
    examples: 'Notes, printouts, flyers, newspapers',
    tip: 'Keep it clean and dry. Oily or food-stained paper goes in the general waste bin.',
  },
  {
    id: 'cardboard',
    name: 'Cardboard',
    bin: 'blue',
    examples: 'Delivery boxes, cereal boxes, paper bag packaging',
    tip: 'Flatten boxes so they take up less space. Greasy pizza boxes go in general waste.',
  },
  {
    id: 'plastic',
    name: 'Plastic',
    bin: 'blue',
    examples: 'Drink bottles, food tubs, shampoo bottles',
    tip: 'Empty and give it a quick rinse. Plastic bags and wrappers are usually not accepted.',
  },
  {
    id: 'metal',
    name: 'Metal',
    bin: 'blue',
    examples: 'Drink cans, food tins, clean foil',
    tip: 'Rinse out leftover food or drink before you bin it.',
  },
  {
    id: 'glass',
    name: 'Glass',
    bin: 'blue',
    examples: 'Drink bottles, sauce and jam jars',
    tip: 'Bottles and jars only. Broken glass, mirrors and light bulbs should be wrapped up and thrown away safely.',
  },
  {
    id: 'battery',
    name: 'Batteries',
    bin: 'special',
    examples: 'AA and AAA batteries, phone and laptop batteries',
    tip: 'Never put these in any bin. They can start fires. Drop them at a battery or e-waste collection point.',
  },
  {
    id: 'clothes',
    name: 'Clothes',
    bin: 'special',
    examples: 'T-shirts, jeans, jackets',
    tip: 'Still wearable? Donate them or use a textile recycling box so someone else can use them.',
  },
  {
    id: 'shoes',
    name: 'Shoes',
    bin: 'special',
    examples: 'Sneakers, sandals, school shoes',
    tip: 'Pairs in good condition can be donated. Some shops also have shoe recycling boxes.',
  },
  {
    id: 'biological',
    name: 'Food & plant waste',
    bin: 'general',
    examples: 'Leftover food, fruit peels, leaves, flowers',
    tip: 'This cannot be recycled with the items above. Use the general waste bin, or a compost bin if there is one.',
  },
  {
    id: 'trash',
    name: 'General trash',
    bin: 'general',
    examples: 'Used face masks, tissues, snack wrappers',
    tip: 'Things that cannot be recycled or reused go in the general waste bin.',
  },
]

const STEPS: { title: string; text: string }[] = [
  { title: 'Sign in or register', text: 'Create a free account with your email, or sign in if you already have one.' },
  { title: 'Snap a photo', text: 'Take a clear photo of one item and upload it. JPEG, PNG or WebP, up to 5 MB.' },
  { title: 'Find out which bin', text: 'RecycleSort works out what the item is and tells you which bin it belongs in.' },
  {
    title: 'Earn your points',
    text: 'You get 1 point for every scan, plus 4 bonus points when the item goes in the blue recycling bin.',
  },
]

// Mirrors validate_password_policy in src/app/auth/routes.py so users see problems before submitting.
function passwordProblem(password: string, email: string): string | null {
  if (password.length < 8) return 'Password must be at least 8 characters.'
  if (new TextEncoder().encode(password).length > 72) return 'Password is too long (72 bytes at most).'
  if (!/[a-z]/.test(password)) return 'Password must contain a lowercase letter.'
  if (!/[A-Z]/.test(password)) return 'Password must contain an uppercase letter.'
  if (!/\d/.test(password)) return 'Password must contain a number.'
  const emailName = email.split('@')[0].toLowerCase()
  if (emailName && password.toLowerCase().includes(emailName)) return 'Password must not contain your email name.'
  return null
}

function MaterialPhoto({ id, name }: { id: string; name: string }) {
  const [missing, setMissing] = useState(false)
  if (missing) {
    return (
      <div className="material-photo placeholder" aria-label={`Photo of ${name} coming soon`}>
        Photo coming soon
      </div>
    )
  }
  return <img className="material-photo" src={`/materials/${id}.jpg`} alt={name} onError={() => setMissing(true)} />
}

const SCORING: { badge: string; title: string; text: string }[] = [
  { badge: '+1', title: 'Every scan', text: 'You earn 1 point for every photo you scan.' },
  {
    badge: '+4',
    title: 'Blue bin bonus',
    text: 'Get 4 extra points when the item belongs in the blue recycling bin: paper, cardboard, plastic, metal or glass.',
  },
]

function MaterialGrid({ details }: { details: boolean }) {
  return (
    <section className={details ? 'material-grid' : 'material-grid compact'}>
      {MATERIALS.map((item) => (
        <article key={item.id} className="card material">
          <MaterialPhoto id={item.id} name={item.name} />
          <h3>{item.name}</h3>
          <span className={`bin-tag ${item.bin}`}>{BIN_LABELS[item.bin]}</span>
          {details && (
            <>
              <p className="muted">{item.examples}</p>
              <p>{item.tip}</p>
            </>
          )}
        </article>
      ))}
    </section>
  )
}

function SignOutDialog({ open, onConfirm, onCancel }: { open: boolean; onConfirm: () => void; onCancel: () => void }) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby="sign-out-title"
      onCancel={(event) => {
        // Escape key: let React state close the dialog.
        event.preventDefault()
        onCancel()
      }}
      onClick={(event) => {
        // Clicking the dimmed backdrop (outside .modal-body) counts as cancel.
        if (event.target === event.currentTarget) onCancel()
      }}
    >
      <div className="modal-body">
        <h2 id="sign-out-title">Sign out?</h2>
        <p className="muted">You will need to sign in again to scan items and earn points.</p>
        <div className="modal-actions">
          <button className="ghost" onClick={onCancel}>
            Cancel
          </button>
          <button className="danger" autoFocus onClick={onConfirm}>
            Yes, sign out
          </button>
        </div>
      </div>
    </dialog>
  )
}

export default function App() {
  const [view, setView] = useState<View>(isAuthed() ? 'upload' : 'home')
  const [user, setUser] = useState<User | null>(loadUser())
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [result, setResult] = useState<ScanResult | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [resultPreview, setResultPreview] = useState<string | null>(null)
  const [confirmSignOut, setConfirmSignOut] = useState(false)
  const [busy, setBusy] = useState(false)
  const [logs, setLogs] = useState<ScanLog[]>([])
  const [adminKey, setAdminKey] = useState('dev-admin-api-key-not-for-production')
  const [leaderboard, setLeaderboard] = useState<{ email: string; points: number }[]>([])
  const [adminLogs, setAdminLogs] = useState<ScanLog[]>([])
  const [health, setHealth] = useState<string>('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regTouched, setRegTouched] = useState(false)

  const regProblem = passwordProblem(regPassword, regEmail)

  useEffect(() => {
    if (!isAuthed()) return
    api
      .profile()
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
      { id: 'profile', label: 'Profile', needsAuth: true },
      { id: 'admin', label: 'Admin' },
    ]
    return items.filter((item) => !item.needsAuth || user)
  }, [user])

  function go(next: View) {
    setError('')
    setNotice('')
    setConfirmSignOut(false)
    setView(next)
  }

  async function onAuth(event: FormEvent<HTMLFormElement>, mode: 'login' | 'register') {
    event.preventDefault()
    setError('')
    const form = new FormData(event.currentTarget)
    const email = String(form.get('email') || '')
    const password = String(form.get('password') || '')
    if (mode === 'register' && passwordProblem(password, email)) {
      setRegTouched(true)
      return
    }
    setBusy(true)
    try {
      const payload = mode === 'login' ? await api.login(email, password) : await api.register(email, password)
      saveSession(payload.access_token, payload.user)
      setUser(payload.user)
      setRegPassword('')
      setRegTouched(false)
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
      // Move the photo to the profile's latest-scan card and empty the scan form for the next item.
      if (resultPreview) URL.revokeObjectURL(resultPreview)
      setResultPreview(preview)
      setPreview(null)
      setUser((current) => (current ? { ...current, points: scan.total_points } : current))
      const token = localStorage.getItem('recyclesort.token')
      if (token && user) saveSession(token, { ...user, points: scan.total_points })
      setView('profile')
      void loadProfile()
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
        <div className="brand" onClick={() => go(user ? 'upload' : 'home')}>
          <img className="brand-mark" src="/favicon.svg" alt="" />
          <h1>RecycleSort</h1>
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
            <button className="danger" onClick={() => setConfirmSignOut(true)}>
              Sign out
            </button>
          )}
        </nav>
      </header>

      <SignOutDialog
        open={confirmSignOut}
        onCancel={() => setConfirmSignOut(false)}
        onConfirm={() => {
          clearSession()
          setUser(null)
          setResult(null)
          setResultPreview(null)
          setPreview(null)
          go('home')
        }}
      />

      {error && <div className="banner error">{error}</div>}
      {notice && <div className="banner ok">{notice}</div>}

      {view === 'login' && (
        <section className="card">
          <h2>Sign in</h2>
          <form onSubmit={(event) => void onAuth(event, 'login')}>
            <Field label="Email" htmlFor="login-email">
              <input id="login-email" name="email" type="email" required autoComplete="email" />
            </Field>
            <Field label="Password" htmlFor="login-password">
              <input id="login-password" name="password" type="password" required minLength={8} autoComplete="current-password" />
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
          <p className="muted">You start at 0 points and earn more with every scan.</p>
          <form onSubmit={(event) => void onAuth(event, 'register')}>
            <Field label="Email" htmlFor="register-email">
              <input
                id="register-email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={regEmail}
                onChange={(event) => setRegEmail(event.target.value)}
              />
            </Field>
            <Field label="Password" htmlFor="register-password">
              <input
                id="register-password"
                name="password"
                type="password"
                required
                autoComplete="new-password"
                aria-invalid={regTouched && regProblem ? true : undefined}
                aria-describedby="register-password-hint"
                className={regTouched && regProblem ? 'invalid' : undefined}
                value={regPassword}
                onChange={(event) => setRegPassword(event.target.value)}
                onBlur={() => setRegTouched(true)}
              />
              {regTouched && regProblem ? (
                <p id="register-password-hint" className="field-error" role="alert">
                  {regProblem}
                </p>
              ) : (
                <p id="register-password-hint" className="field-hint">
                  At least 8 characters, with an uppercase letter, a lowercase letter and a number.
                </p>
              )}
            </Field>
            <button className="primary" disabled={busy} type="submit">
              {busy ? 'Creating…' : 'Register'}
            </button>
          </form>
        </section>
      )}

      {view === 'upload' && user && (
        <>
          <section className="grid two">
            <form className="card" onSubmit={(event) => void onUpload(event)}>
              <h2>Scan an item</h2>
              <p className="muted">JPEG, PNG, or WebP, up to 5 MB.</p>
              <div className="drop">
                <label htmlFor="scan-file">Image file</label>
                <input
                  id="scan-file"
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
              <div className="row scan-actions">
                <button className="primary" disabled={busy} type="submit">
                  {busy ? 'Classifying…' : 'Classify image'}
                </button>
                <span className="muted">Signed in as {user.email} · {user.points} pts</span>
              </div>
            </form>
            <aside className="card">
              <h2>How scoring works</h2>
              <ol className="steps">
                {SCORING.map((rule) => (
                  <li key={rule.title}>
                    <span className="step-number">{rule.badge}</span>
                    <div>
                      <h3>{rule.title}</h3>
                      <p className="muted">{rule.text}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </aside>
          </section>

          <h2 className="section-title">What can I scan?</h2>
          <MaterialGrid details={false} />
        </>
      )}

      {view === 'profile' && user && (
        <div className="stack">
          <section className="card">
            <h2>Your profile</h2>
            <p>
              <strong>{user.email}</strong>
              <br />
              Total points: <strong>{user.points}</strong>
            </p>
          </section>

          {result && (
            <section className="card">
              <h2>Latest scan</h2>
              <div className="result-hero">
                {resultPreview && <img className="preview" src={resultPreview} alt="Scanned waste item" />}
                <div>
                  <span className="pill">{result.is_recyclable ? 'Recyclable' : 'Not recyclable'}</span>
                  <h3 style={{ textTransform: 'capitalize', marginBottom: 0 }}>{result.predicted_class}</h3>
                  <p className="muted">
                    Confidence {(result.confidence * 100).toFixed(1)}%
                    {result.model_loaded ? '' : ' · model unavailable'}
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
              <p><strong>Take note!!:</strong> {result.bin_message}</p>
              <p className="muted"><strong>Fun fact!!:</strong> {result.fun_fact}</p>
            </section>
          )}

          <section className="card">
            <h2>Scan history</h2>
            {logs.length === 0 ? (
              <p className="muted">No scans yet. Head to the Scan page to earn your first points.</p>
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
        </div>
      )}

      {view === 'home' && (
        <>
          <section className="hero">
            <h1>RecycleSort</h1>
            <p>Photograph waste. Learn the bin. Earn points.</p>
            {!user && (
              <div className="hero-actions">
                <button className="primary" onClick={() => go('login')}>
                  Sign in
                </button>
                <button className="ghost" onClick={() => go('register')}>
                  Register
                </button>
              </div>
            )}
          </section>

          <h2 className="section-title">What can I scan?</h2>
          <MaterialGrid details />

          <h2 className="section-title">How do I earn recycling points?</h2>
          <section className="card">
            <ol className="steps">
              {STEPS.map((step, index) => (
                <li key={step.title}>
                  <span className="step-number">{index + 1}</span>
                  <div>
                    <h3>
                      Step {index + 1}: {step.title}
                    </h3>
                    <p className="muted">{step.text}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </>
      )}

      {view === 'admin' && (
        <section className="card">
          <h2>Admin dashboard</h2>
          <p className="muted">
            The admin key is loaded as if from AWS Parameter Store (`SSM_ADMIN_API_KEY`). The local example value is
            pre-filled.
          </p>
          <form onSubmit={(event) => void loadAdmin(event)}>
            <Field label="Admin API key" htmlFor="admin-key">
              <input
                id="admin-key"
                name="adminKey"
                value={adminKey}
                onChange={(event) => setAdminKey(event.target.value)}
                type="password"
                autoComplete="off"
              />
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
    </div>
  )
}
