import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';

export default function Auth({ defaultIsLogin = true }) {
  const [isLogin, setIsLogin] = useState(defaultIsLogin)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate();

  // Redirect if already logged in
  useEffect(() => {
    if (localStorage.getItem('token')) {
      navigate('/dashboard');
    }
    // Update internal state if the route changes (e.g., user clicked a link to /signup)
    setIsLogin(defaultIsLogin);
  }, [defaultIsLogin, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const endpoint = isLogin ? '/login' : '/signup'

    try {
      const response = await fetch(`https://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Authentication failed')
      }

      if (isLogin) {
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('username', data.username)
        navigate('/dashboard')
      } else {
        setIsLogin(true)
        setError('Signup successful! Please log in.')
        setPassword('')
        navigate('/login')
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>{isLogin ? 'Login to Tracker' : 'Create Account'}</h2>
        <p className="auth-subtitle">Secure HTTPS & WSS Edge Communications</p>

        {error && <div className={`auth-message ${error.includes('successful') ? 'success' : 'error'}`}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" disabled={loading} className="auth-btn">
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>
        <p className="auth-toggle">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <Link to={isLogin ? '/signup' : '/login'} onClick={() => { setError(''); setPassword(''); }}>
            {isLogin ? 'Sign up here' : 'Login here'}
          </Link>
        </p>
      </div>
    </div>
  )
}
