import { useState, useRef, useEffect } from 'react'
import { UploadCloud, Fingerprint, Search, ShieldCheck, Link, ExternalLink, Loader2, CheckCircle2, Hexagon, Network, Zap, Volume2, VolumeX } from 'lucide-react'
import './App.css'

function useIntersectionObserver(options = { threshold: 0.15 }) {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);
  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) setIsVisible(true);
    }, options);
    if (ref.current) observer.observe(ref.current);
    return () => { if (ref.current) observer.unobserve(ref.current); };
  }, [ref, options]);
  return [ref, isVisible];
}

const CustomCursor = () => {
  const cursorRef = useRef(null);
  const requestRef = useRef(null);
  const mousePos = useRef({ x: 0, y: 0 });
  const isHovering = useRef(false);

  useEffect(() => {
    const onMouseMove = (e) => {
      mousePos.current = { x: e.clientX, y: e.clientY };
      const target = e.target;
      isHovering.current = target.closest('a, button, label, .upload-area, input, [role="button"]') !== null;
      
      if (!requestRef.current) {
        requestRef.current = requestAnimationFrame(updateCursor);
      }
    };

    const updateCursor = () => {
      if (cursorRef.current) {
        // translate3d forces GPU acceleration, preventing layout thrashing
        // Subtract half the size to center the cursor exactly on the pointer
        const size = isHovering.current ? 40 : 20;
        const offset = size / 2;
        cursorRef.current.style.transform = `translate3d(${mousePos.current.x - offset}px, ${mousePos.current.y - offset}px, 0)`;
        
        if (isHovering.current) {
          cursorRef.current.classList.add('hovering');
        } else {
          cursorRef.current.classList.remove('hovering');
        }
      }
      requestRef.current = null;
    };

    window.addEventListener('mousemove', onMouseMove, { passive: true });
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, []);

  return <div className="custom-cursor" ref={cursorRef} />;
}

const KineticText = ({ text, startDelay = 2.0 }) => {
  return (
    <span>
      {text.split('').map((char, i) => (
        <span key={i} className="kinetic-char" style={{ animationDelay: `${startDelay + (i * 0.05)}s` }}>
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </span>
  )
}

const MagneticButton = ({ children, onClick, disabled, className, ...props }) => {
  const ref = useRef(null);
  const handleMouseMove = (e) => {
    if (disabled || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    ref.current.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
  };
  const handleMouseLeave = () => {
    if (ref.current) ref.current.style.transform = '';
  };
  return (
    <button 
      ref={ref} 
      className={`magnetic-btn ${className || ''}`} 
      onClick={onClick} 
      disabled={disabled}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {children}
    </button>
  );
}

const RadialProgress = ({ score }) => {
  const radius = 20;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - score * circumference;
  
  return (
    <div className="radial-progress">
      <svg viewBox="0 0 48 48">
        <defs>
          <linearGradient id="colorShiftGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#aab9c7" />
            <stop offset="50%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#6e8799" />
          </linearGradient>
        </defs>
        <circle className="radial-bg" cx="24" cy="24" r={radius} />
        <circle className="radial-value" cx="24" cy="24" r={radius} 
          style={{ strokeDasharray: circumference, strokeDashoffset }} 
        />
      </svg>
      <span className="radial-text">{(score * 100).toFixed(0)}</span>
    </div>
  )
}

function App() {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const ambientAudio = useRef(new Audio('/ambient.wav'));

  const [entryGateHidden, setEntryGateHidden] = useState(false);

  const handleEntry = (withSound) => {
    setSoundEnabled(withSound);
    if (withSound) {
      ambientAudio.current.play().catch(e => console.log("Audio play blocked", e));
    }
    setEntryGateHidden(true);
  };

  useEffect(() => {
    ambientAudio.current.loop = true;
    ambientAudio.current.volume = 0.1;
  }, []);

  useEffect(() => {
    const handleScroll = () => {
      if (!ambientAudio.current || !soundEnabled) return;
      const scrollY = window.scrollY;
      const maxScroll = document.body.scrollHeight - window.innerHeight;
      const scrollFraction = maxScroll > 0 ? (scrollY / maxScroll) : 0;
      ambientAudio.current.volume = 0.1 + (scrollFraction * 0.6);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [soundEnabled]);



  const toggleSound = () => {
    const nextState = !soundEnabled;
    setSoundEnabled(nextState);
    if (nextState) {
      ambientAudio.current.play().catch(e => console.log("Audio play blocked", e));
    } else {
      ambientAudio.current.pause();
    }
  };

  const playClick = () => {
    if (soundEnabled) {
      const click = new Audio('/click.wav');
      click.volume = 0.6;
      click.play().catch(() => {});
    }
  };

  const playSuccess = () => {
    if (soundEnabled) {
      const success = new Audio('/success.wav');
      success.volume = 0.8;
      success.play().catch(() => {});
    }
  };

  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [consent, setConsent] = useState(false)
  const [stage, setStage] = useState(0)
  const [results, setResults] = useState(null)
  const [anchorData, setAnchorData] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFile = (e) => {
    const f = e.target.files[0]
    if (!f) return
    if (!f.type.startsWith('image/')) {
      setError("Invalid format.")
      return
    }
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setStage(0)
    setResults(null)
    setAnchorData(null)
    setError(null)
    playClick()
    
    setTimeout(() => {
      document.getElementById('scene-ingestion').scrollIntoView({ behavior: 'smooth' })
    }, 300)
  }

  const handleAnalyze = async () => {
    if (!file || !consent) return
    playClick()
    setError(null)
    setStage(1) 
    
    setTimeout(() => {
      document.getElementById('scene-search').scrollIntoView({ behavior: 'smooth' })
    }, 300)

    const formData = new FormData()
    formData.append('image', file)
    try {
      const res = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Analysis failed.')
      setResults(data)
      setStage(3) 
    } catch (err) {
      setError(err.message)
      setStage(0)
      setTimeout(() => {
        document.getElementById('scene-ingestion').scrollIntoView({ behavior: 'smooth' })
      }, 300)
    }
  }

  const handleAnchor = async (match) => {
    playClick()
    setError(null)
    setStage(4) 
    
    setTimeout(() => {
      document.getElementById('scene-terminal').scrollIntoView({ behavior: 'smooth' })
    }, 300)

    try {
      const payload = {
        imageHash: results.privacy.imageHash,
        sourceUrl: match.url,
        score: match.score,
        pageTitle: match.page_title || match.source || match.url
      }
      const res = await fetch('http://localhost:8000/api/anchor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Ledger anchoring failed.')
      
      setAnchorData(data)
      setStage(5)
      playSuccess()
      
    } catch (err) {
      setError(err.message)
      setStage(3)
      setTimeout(() => {
        document.getElementById('scene-search').scrollIntoView({ behavior: 'smooth' })
      }, 300)
    }
  }

  const [heroRef, heroVisible] = useIntersectionObserver({ threshold: 0.2 });
  const [ingestRef, ingestVisible] = useIntersectionObserver({ threshold: 0.2 });
  const [searchRef, searchVisible] = useIntersectionObserver({ threshold: 0.2 });
  const [termRef, termVisible] = useIntersectionObserver({ threshold: 0.2 });

  return (
    <>
      <CustomCursor />
      <div className={`entry-gate ${entryGateHidden ? 'hidden' : ''}`}>
        <div className="entry-logo-container">
          <div className="entry-logo">LUMINA</div>
          <div className="entry-subtitle">FACE ID + BLOCKCHAIN VERIFICATION</div>
        </div>
        <div className="entry-options">
          <MagneticButton className="btn-primary" onClick={() => handleEntry(true)}>
            ENTER WITH SOUND
          </MagneticButton>
          <MagneticButton className="btn-primary" onClick={() => handleEntry(false)}>
            ENTER WITHOUT SOUND
          </MagneticButton>
        </div>
      </div>

      <div className="app-container">
        {/* Global Navigation */}
        <nav className="global-nav">
          <div className="nav-left-container">
            <div className="nav-left">
              <Hexagon size={16} className="brand-icon color-shift" />
              <span className="brand-text">LUMINA</span>
            </div>
            <div className="nav-subtitle">FACE ID + BLOCKCHAIN VERIFICATION</div>
          </div>
          <div className="nav-center">
            <a href="#scene-ingestion" onClick={playClick}>PIPELINE</a>
            <a href="#scene-search" onClick={playClick}>PROVENANCE</a>
            <a href="#scene-terminal" onClick={playClick}>LEDGER</a>
          </div>
          <div className="nav-right">
            <button className="sound-toggle" onClick={toggleSound}>
              {soundEnabled ? <Volume2 size={16} className="color-shift" /> : <VolumeX size={16} />}
              <span className={soundEnabled ? 'color-shift' : ''}>SOUND {soundEnabled ? 'ON' : 'OFF'}</span>
            </button>
          </div>
        </nav>

        <main className="scroller">
          {/* HERO SCENE */}
          <section className={`scene hero-scene ${heroVisible ? 'is-visible' : ''}`} ref={heroRef}>
            <div className="hero-content">
              <h1 className="hero-title">
                <KineticText text="Zero-Knowledge" startDelay={2.0} /><br/>
                <KineticText text="Visual Truth." startDelay={2.8} />
              </h1>
              <p className="hero-subtitle">
                Securely map digital assets to their web origins. Generate immutable cryptographic footprints and anchor them directly to decentralized ledgers.
              </p>
              <MagneticButton onClick={() => { playClick(); document.getElementById('scene-ingestion').scrollIntoView({ behavior: 'smooth' })}}>
                COMMENCE PROTOCOL
              </MagneticButton>
            </div>
            <div className="scroll-indicator">
              <div className="mouse"></div>
            </div>
          </section>

          {/* SCENE 1: INGESTION */}
          <section id="scene-ingestion" className={`scene ingestion-scene ${ingestVisible ? 'is-visible' : ''}`} ref={ingestRef}>
            <div className="scene-container">
              <div className="scene-header">
                <span className="scene-num">01</span>
                <h2>Asset Ingestion</h2>
              </div>
              
              <div className="ingestion-panel">
                <div 
                  className={`upload-area ${file ? 'active' : ''}`}
                  onClick={() => { playClick(); !file && fileInputRef.current?.click() }}
                >
                  {!file && <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFile}
                    accept="image/jpeg, image/png, image/webp" 
                  />}
                  
                  {preview ? (
                    <div className="preview-container">
                      <img src={preview} alt="Asset preview" className="preview-image" />
                      <div className="preview-overlay">
                        <div>
                          <div className="preview-name">{file.name}</div>
                          <div className="mono preview-size">{(file.size / 1024).toFixed(2)} KB</div>
                        </div>
                        <button 
                          className="btn-clear" 
                          onClick={(e) => {
                            e.stopPropagation();
                            playClick();
                            setFile(null);
                            setPreview(null);
                            setResults(null);
                            setAnchorData(null);
                            setStage(0);
                          }}
                        >
                          CLEAR
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="upload-prompt">
                      <Network size={48} className="upload-icon color-shift" />
                      <div className="upload-title">Initialize Sequence</div>
                      <div className="text-muted">Drag & drop or click to upload target asset</div>
                    </div>
                  )}
                </div>

                {error && (
                  <div className="error-box">
                    <strong>Exception:</strong> {error}
                  </div>
                )}

                {file && !results && stage === 0 && (
                  <div className="consent-box animate-fade-up">
                    <input 
                      type="checkbox" 
                      id="consent-check"
                      checked={consent} 
                      onChange={(e) => { playClick(); setConsent(e.target.checked)}} 
                    />
                    <label htmlFor="consent-check">
                      I authorize the cryptographic hashing of this asset. This protocol strictly verifies provenance and does not execute facial recognition on private individuals.
                    </label>
                  </div>
                )}

                {file && !results && stage === 0 && (
                  <button 
                    className="btn-primary" 
                    style={{width: '100%', marginTop: '2rem'}} 
                    disabled={!consent}
                    onClick={handleAnalyze}
                  >
                    <Fingerprint size={20} /> COMMENCE ANALYSIS
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* SCENE 2: PROVENANCE SEARCH */}
          <section id="scene-search" className={`scene search-scene ${searchVisible ? 'is-visible' : ''}`} ref={searchRef}>
            <div className="scene-container">
              <div className="scene-header">
                <span className="scene-num">02</span>
                <h2>Network Provenance</h2>
              </div>

              {stage === 1 && (
                <div className="results-panel">
                  <div className="skeleton skeleton-card" style={{height: '80px'}}></div>
                  <h3 className="section-subtitle">Scanning Web Index</h3>
                  <div className="skeleton skeleton-card"></div>
                  <div className="skeleton skeleton-card"></div>
                </div>
              )}

              {stage === 0 && !results && (
                <div className="waiting-state">
                  <Search size={48} className="text-muted dim" />
                  <p>Awaiting asset ingestion to commence public web index scan.</p>
                </div>
              )}

              {results && (
                <div className="results-panel animate-fade-up">
                  <div className="hash-box">
                    <div className="hash-label color-shift">Generated Signature (SHA-256)</div>
                    <div className="mono hash-value">{results.privacy.imageHash}</div>
                  </div>

                  <h3 className="section-subtitle">Discovered Origins</h3>
                  
                  {results.search.matches.length > 0 ? (
                    <div className="match-grid">
                      {results.search.matches.map((m, idx) => (
                        <div key={idx} className="match-card">
                          <div className="match-info">
                            {m.thumbnail ? (
                              <img src={m.thumbnail} alt="thumbnail" className="match-thumb" />
                            ) : (
                              <div className="match-thumb-placeholder">
                                <Search size={20} className="text-muted" />
                              </div>
                            )}
                            <div className="match-details">
                              <div className="match-title">{m.page_title || m.source}</div>
                              <div className="match-score">visual_match</div>
                              <a href={m.url} target="_blank" rel="noreferrer" className="match-url">{m.url}</a>
                            </div>
                          </div>
                          
                          <div style={{display: 'flex', alignItems: 'center', gap: '2rem'}}>
                            <RadialProgress score={m.score} />
                            
                            <button 
                              className="btn-primary btn-anchor" 
                              onClick={() => handleAnchor(m)}
                              disabled={stage >= 4}
                            >
                              <ShieldCheck size={16} />
                              ANCHOR TO LEDGER
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-results-box">
                      <Search size={32} className="text-muted" />
                      <div>No verifiable sources found.</div>
                      <p className="text-muted">Asset provenance could not be established.</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          </section>

          {/* SCENE 3: LEDGER TERMINAL */}
          <section id="scene-terminal" className={`scene terminal-scene ${termVisible ? 'is-visible' : ''}`} ref={termRef}>
            <div className="scene-container">
              <div className="scene-header">
                <span className="scene-num">03</span>
                <h2>Decentralized Ledger</h2>
              </div>

              {stage === 4 && (
                <div className="terminal-panel">
                  <div className="terminal-header">
                    <Loader2 className="animate-spin text-muted" size={20} /> 
                    <span>Authorizing cryptographic signature on Polygon Amoy...</span>
                  </div>
                  <div className="terminal-content">
                    <div className="skeleton skeleton-text"></div>
                    <div className="skeleton skeleton-text short"></div>
                    <div className="skeleton skeleton-text"></div>
                  </div>
                </div>
              )}

              {stage < 4 && !anchorData && (
                <div className="waiting-state">
                  <ShieldCheck size={48} className="text-muted dim" />
                  <p>Awaiting anchor authorization to commit provenance to Polygon.</p>
                </div>
              )}

              {anchorData && anchorData.chain.status !== 'demo' && (
                <div className="terminal-panel reveal-stamp">
                  <div className="terminal-header">
                    <CheckCircle2 className="color-shift" size={24} /> 
                    <span className="color-shift" style={{fontWeight: 600, letterSpacing: '0.1em'}}>LEDGER SYNCHRONIZATION COMPLETE</span>
                  </div>
                  
                  <div className="terminal-content">
                    <div className="term-line">
                      <span className="term-label">IPFS_CID</span>
                      <span className="term-value">{anchorData.verify?.stored_cid}</span>
                    </div>
                    <div className="term-line">
                      <span className="term-label">TX_HASH</span>
                      <a href={anchorData.chain.explorerUrl} target="_blank" rel="noreferrer" className="term-value term-success color-shift">
                        {anchorData.chain.txHash} <ExternalLink size={12} className="inline-icon"/>
                      </a>
                    </div>
                    <div className="term-line">
                      <span className="term-label">CONTRACT</span>
                      <span className="term-value">{anchorData.chain.contractAddress}</span>
                    </div>
                    <div className="term-line">
                      <span className="term-label">STATUS</span>
                      <span className="term-value status-verified color-shift">VERIFIED_ON_CHAIN</span>
                    </div>
                  </div>
                </div>
              )}

              {anchorData && anchorData.chain.status === 'demo' && (
                <div className="terminal-panel reveal-stamp">
                  <div className="terminal-header">
                    <CheckCircle2 className="color-shift" size={24} /> 
                    <span className="color-shift" style={{fontWeight: 600, letterSpacing: '0.1em'}}>RECORD READY · DEMO MODE</span>
                  </div>
                  
                  <div className="terminal-content">
                    <div className="term-line">
                      <span className="term-label">SOURCE</span>
                      <span className="term-value">{anchorData.source.url}</span>
                    </div>
                    <div className="term-line">
                      <span className="term-label">EVIDENCE SCORE</span>
                      <span className="term-value">{Math.round(anchorData.source.score * 100)}%</span>
                    </div>
                    <div className="term-line" style={{marginTop: '10px'}}>
                      <span className="term-value color-shift">Add Polygon Amoy credentials in .env to write the record on-chain.</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </>
  )
}

export default App
