import { Link } from 'react-router-dom';
import { Shield, Activity, Zap, Lock } from 'lucide-react';

export default function Home() {
  return (
    <div className="home-container">
      {/* Animated background glow elements for creative aesthetic */}
      <div className="glow-blob blob-1"></div>
      <div className="glow-blob blob-2"></div>
      <div className="glow-blob blob-3"></div>

      <nav className="home-nav">
        <div className="nav-brand">
          <Activity className="brand-icon" />
          <span>Tracker</span>
        </div>
        <div className="nav-links">
          <Link to="/login" className="nav-link">Log In</Link>
          <Link to="/signup" className="nav-btn-primary">Get Started</Link>
        </div>
      </nav>

      <main className="hero-section">
        <div className="hero-content">
          <div className="badge glass-effect">
            <Lock size={14} className="badge-icon" />
            <span>Bank-Grade Security</span>
          </div>
          <h1 className="hero-title">
            Secure & Real-Time <br />
            <span className="hero-gradient">Stock Tracking.</span>
          </h1>
          <p className="hero-subtitle">
            Experience ultra-low latency, WSS-edge communicated market data with uncompromising safety. Stay ahead of the curve.
          </p>
          <div className="hero-actions">
            <Link to="/signup" className="btn-glow">
              Start Tracking Now
              <Zap size={18} className="btn-icon" />
            </Link>
            <Link to="/login" className="btn-outline glass-effect">
              Access Dashboard
            </Link>
          </div>
          
          <div className="features-grid">
            <div className="feature-card glass-effect">
              <div className="feature-icon-wrapper purple-glow">
                <Shield size={24} />
              </div>
              <div>
                <h3>Military Encryption</h3>
                <p>End-to-end WSS secure socket pipeline.</p>
              </div>
            </div>
            <div className="feature-card glass-effect">
              <div className="feature-icon-wrapper green-glow">
                <Activity size={24} />
              </div>
              <div>
                <h3>Live Updates</h3>
                <p>Sub-millisecond data delivery straight to your UI.</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className="hero-visual">
          <div className="glass-panel mockup-panel">
            <div className="mockup-header">
              <div className="mac-dots">
                <span></span><span></span><span></span>
              </div>
              <div className="mockup-tabs">Live Feed</div>
            </div>
            <div className="mockup-body">
              <div className="mock-stock up">
                <div className="mock-stock-info">
                  <span className="mock-symbol">AAPL</span>
                  <span className="mock-name">Apple Inc.</span>
                </div>
                <div className="mock-price-info">
                  <span className="mock-price">$189.42</span>
                  <span className="mock-change">+1.24%</span>
                </div>
              </div>
              <div className="mock-stock down">
                <div className="mock-stock-info">
                  <span className="mock-symbol">TSLA</span>
                  <span className="mock-name">Tesla</span>
                </div>
                <div className="mock-price-info">
                  <span className="mock-price">$214.11</span>
                  <span className="mock-change">-0.85%</span>
                </div>
              </div>
              <div className="mock-stock up">
                <div className="mock-stock-info">
                  <span className="mock-symbol">NVDA</span>
                  <span className="mock-name">NVIDIA</span>
                </div>
                <div className="mock-price-info">
                  <span className="mock-price">$485.09</span>
                  <span className="mock-change">+2.15%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
