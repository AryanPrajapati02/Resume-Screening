import { useState, useRef, useCallback } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || '/api'

function App() {
  const [currentStep, setCurrentStep] = useState(1)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [jobTitle, setJobTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [extractedSkills, setExtractedSkills] = useState([])
  const [results, setResults] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [expandedRow, setExpandedRow] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileSelect = async (files) => {
    if (!files || files.length === 0) return
    
    setIsLoading(true)
    setError(null)
    
    try {
      const formData = new FormData()
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i])
      }
      
      const response = await fetch(`${API_BASE}/resumes/bulk`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(120000), // 2 minute timeout
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || 'Failed to upload resumes')
      }
      
      const data = await response.json()
      const fileNames = Array.from(files).map(f => f.name)
      setUploadedFiles(fileNames)
      setCurrentStep(2)
    } catch (err) {
      console.error('Upload error:', err)
      if (err.name === 'TimeoutError') {
        setError('Upload timed out. Please try again.')
      } else {
        setError(err.message || 'Failed to upload resumes')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const files = e.dataTransfer.files
    handleFileSelect(files)
  }, [])

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const handleReplaceFiles = () => {
    setUploadedFiles([])
    setCurrentStep(1)
  }

  const handleSubmitJD = async () => {
    if (!jobTitle.trim() || !jobDescription.trim()) {
      setError('Please fill in both job title and description')
      return
    }
    
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: jobTitle,
          text: jobDescription
        }),
      })
      
      if (!response.ok) {
        throw new Error('Failed to submit job description')
      }
      
      const data = await response.json()
      setExtractedSkills(data.extracted_skills || [])
      setCurrentStep(3)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleRunMatching = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`${API_BASE}/match/all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      
      if (!response.ok) {
        throw new Error('Failed to run matching')
      }
      
      const data = await response.json()
      setResults(data)
      setCurrentStep(4)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const toggleRow = (index) => {
    setExpandedRow(expandedRow === index ? null : index)
  }

  const getScoreClass = (score) => {
    if (score >= 70) return 'best'
    if (score >= 55) return 'good'
    return 'reject'
  }

  const getStatusBadge = (score) => {
    if (score >= 70) return 'best'
    if (score >= 55) return 'good'
    return 'reject'
  }

  return (
    <div className="app">
      <Navbar />
      
      <Hero onTryFree={() => document.getElementById('app-section')?.scrollIntoView({ behavior: 'smooth' })} />
      
      <Features />
      
      <section id="app-section" className="app-section">
        <div className="container">
          <div className="section-header">
            <div className="section-label">Live Demo</div>
            <h2 className="section-title">Try the Platform</h2>
            <p className="section-subtitle">Upload resumes and add job description to see results</p>
          </div>
          
          {error && (
            <div className="error-message">
              <span>{error}</span>
              <button onClick={() => setError(null)}>Dismiss</button>
            </div>
          )}
          
          <div className="app-card">
            <div className="app-section-label">Screening Platform</div>
            
            <div className="app-steps-indicator">
              {[1, 2, 3].map(step => (
                <div 
                  key={step} 
                  className={`step-indicator ${currentStep >= step ? 'active' : ''} ${currentStep === step ? 'current' : ''}`}
                >
                  {step}
                </div>
              ))}
            </div>
            
            {/* Step 1: Upload Resumes */}
            <div className={`app-step ${currentStep === 1 ? 'active' : ''}`}>
              <div className="step-header">
                <div className="step-title-group">
                  <span className="step-number">1</span>
                  <span className="step-title">Upload Resumes</span>
                </div>
                {uploadedFiles.length > 0 && (
                  <button className="step-action" onClick={handleReplaceFiles}>Replace All</button>
                )}
              </div>
              
              <div 
                className="drop-zone"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  multiple
                  accept=".pdf"
                  onChange={(e) => handleFileSelect(e.target.files)}
                  style={{ display: 'none' }}
                />
                <div className="drop-zone-icon">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                  </svg>
                </div>
                <p className="drop-zone-text">Drop PDF files here</p>
                <p className="drop-zone-hint">or click to browse</p>
              </div>
              
              {uploadedFiles.length > 0 && (
                <div className="file-list">
                  {uploadedFiles.map((file, index) => (
                    <span key={index} className="file-chip">
                      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                      {file}
                    </span>
                  ))}
                </div>
              )}
              
              {isLoading && currentStep === 1 && (
                <div className="loading-indicator">Uploading...</div>
              )}
            </div>
            
            {/* Step 2: Job Description */}
            <div className={`app-step ${currentStep >= 2 ? 'active' : ''}`}>
              <div className="step-header">
                <div className="step-title-group">
                  <span className="step-number">2</span>
                  <span className="step-title">Job Description</span>
                </div>
              </div>
              
              <div className="form-group">
                <label className="form-label">Job Title</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g., Senior Data Scientist"
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label className="form-label">Description</label>
                <textarea 
                  className="form-input form-textarea" 
                  placeholder="Paste the job description here..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                />
              </div>
              
              {extractedSkills.length > 0 && (
                <div className="skills-preview">
                  {extractedSkills.map((skill, index) => (
                    <span key={index} className="skill-tag">{skill}</span>
                  ))}
                </div>
              )}
            </div>
            
            {/* Step 3: CTA */}
            <div className={`app-cta ${currentStep >= 2 ? 'active' : ''}`}>
              <button 
                className="btn-cta" 
                onClick={currentStep === 2 ? handleSubmitJD : handleRunMatching}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>Processing...</>
                ) : currentStep === 2 ? (
                  <>
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    Submit
                  </>
                ) : (
                  <>
                    <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                    </svg>
                    Analysis
                  </>
                )}
              </button>
              <p className="cta-note">
                {currentStep === 2 
                  ? 'Submit job description to start matching'
                  : 'View detailed candidate analysis'
                }
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Results Section */}
      {results && currentStep === 4 && (
        <section className="results-section">
          <div className="container">
            <div className="section-header">
              <div className="section-label">Results</div>
              <h2 className="section-title">Ranked Candidates</h2>
              <p className="section-subtitle">Click on a candidate to see detailed analysis</p>
            </div>
            
            <div className="results-card">
              <div className="results-header">
                <div>
                  <h3 className="results-title">{results.job_title || 'Job Position'}</h3>
                  <p className="results-meta">
                    <span>{results.total_candidates || results.candidates?.length || 0}</span> candidates processed
                    {results.avg_match && (
                      <> • <span>{results.avg_match}%</span> avg match</>
                    )}
                  </p>
                </div>
                <button className="btn-export">
                  <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                  Export
                </button>
              </div>
              
              <div className="results-table">
                <div className="results-table-header">
                  <div>#</div>
                  <div>Candidate</div>
                  <div>Score</div>
                  <div>Status</div>
                  <div>Match</div>
                </div>
                
                {(results.candidates || []).map((candidate, index) => (
                  <div key={index}>
                    <div className="result-row" onClick={() => toggleRow(index)}>
                      <div className="result-rank">{index + 1}</div>
                      <div>
                        <div className="result-name">{candidate.name}</div>
                        <div className="result-role">{candidate.role} • {candidate.experience}</div>
                      </div>
                      <div className={`result-score ${getScoreClass(candidate.score)}`}>
                        {candidate.score}%
                      </div>
                      <div className="result-status">
                        <span className={`status-badge ${getStatusBadge(candidate.score)}`}>
                          {candidate.score >= 70 ? 'Best' : candidate.score >= 55 ? 'Good' : 'Reject'}
                        </span>
                      </div>
                      <div className="result-match">
                        <div className="skills-summary">
                          <span className="skills-matched">{candidate.matched_skills}</span>
                          <span className="skills-separator">/</span>
                          <span className="skills-total">{candidate.required_skills}</span>
                          <span className="skills-label"> skills</span>
                        </div>
                        <div className="skills-list">
                          {candidate.all_skills_status && candidate.all_skills_status.length > 0 ? (
                            <div className="all-skills-status">
                              {candidate.all_skills_status.slice(0, 4).map((skillStatus, i) => (
                                <span 
                                  key={i} 
                                  className={`skill-tag ${skillStatus.matched ? 'matched' : 'missing'}`}
                                >
                                  {skillStatus.skill}
                                </span>
                              ))}
                              {candidate.all_skills_status.length > 4 && (
                                <span className="skill-more">
                                  +{candidate.all_skills_status.length - 4} more
                                </span>
                              )}
                            </div>
                          ) : candidate.matched_skills_list && candidate.matched_skills_list.length > 0 && (
                            <div className="matched-skills">
                              <span className="skills-label-small">Matched:</span>
                              {candidate.matched_skills_list.slice(0, 3).map((skill, i) => (
                                <span key={i} className="skill-tag matched">{skill}</span>
                              ))}
                              {candidate.matched_skills_list.length > 3 && (
                                <span className="skill-more">+{candidate.matched_skills_list.length - 3} more</span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="match-bar">
                          <div className="match-bar-fill" style={{ width: `${candidate.skill_coverage || candidate.score}%` }}></div>
                        </div>
                      </div>
                    </div>
                    
                    <div className={`detail-panel ${expandedRow === index ? 'open' : ''}`}>
                      <div className="detail-grid">
                        <div className="detail-section green">
                          <h4><span className="detail-dot"></span> Skills Match Status</h4>
                          {(candidate.all_skills_status || []).map((skillStatus, i) => (
                            <div key={i} className="detail-item">
                              <span className={`detail-small-dot ${skillStatus.matched ? 'matched' : 'missing'}`}></span>
                              <span className={`skill-name ${skillStatus.matched ? 'matched' : 'missing'}`}>
                                {skillStatus.skill}
                              </span>
                              <span className={`skill-status ${skillStatus.matched ? '' : 'missing'}`}>
                                {skillStatus.matched ? '✓ Matched' : '✗ Missing'}
                              </span>
                            </div>
                          ))}
                        </div>
                        <div className="detail-section amber">
                          <h4><span className="detail-dot"></span> Weak Areas</h4>
                          <div className="weak-areas-compact">
                            {(candidate.weak_areas || []).slice(0, 2).map((area, i) => (
                              <span key={i} className="weak-area-tag">{area}</span>
                            ))}
                            {(candidate.weak_areas || []).length > 2 && (
                              <span className="skill-more">+{(candidate.weak_areas || []).length - 2} more</span>
                            )}
                          </div>
                        </div>
                        <div className="detail-section blue">
                          <h4><span className="detail-dot"></span> Improvement Suggestions</h4>
                          <div className="suggestions-compact">
                            {(candidate.missing_skills || []).slice(0, 3).map((skill, i) => (
                              <div key={i} className="suggestion-compact">
                                <span className="suggestion-skill">{skill}</span>
                              </div>
                            ))}
                            {(candidate.weak_areas || []).slice(0, 2).map((area, i) => (
                              <div key={`weak-${i}`} className="suggestion-compact">
                                <span className="suggestion-skill">{area}</span>
                              </div>
                            ))}
                            {((candidate.missing_skills || []).length > 3 || (candidate.weak_areas || []).length > 2) && (
                              <span className="skill-more">+{Math.max(0, (candidate.missing_skills || []).length - 3) + Math.max(0, (candidate.weak_areas || []).length - 2)} more</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {(!results.candidates || results.candidates.length === 0) && (
                  <div className="empty-results">
                    <p>No candidates found. Please upload resumes first.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      <Footer />
    </div>
  )
}

function Navbar() {
  return (
    <nav className="nav">
      <div className="nav-inner">
        <a href="#" className="logo">
          <div className="logo-mark">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
            </svg>
          </div>
          <span className="logo-text">ResumeScreen</span>
        </a>
        <div className="nav-links">
          <a href="#features" className="nav-link">Features</a>
          <a href="#how-it-works" className="nav-link">How it Works</a>
          <a href="#" className="nav-cta">Get Started</a>
        </div>
      </div>
    </nav>
  )
}

function Hero({ onTryFree }) {
  return (
    <section className="hero">
      <div className="hero-inner">
        <div className="hero-content">
          <div className="hero-badge">
            <span className="hero-badge-dot"></span>
            AI-Powered Screening
          </div>
          <h1 className="hero-title">
            Find the Perfect<br/>
            <em>Candidate</em> Instantly
          </h1>
          <p className="hero-subtitle">
            Upload resumes, paste a job description, and let our AI find the best candidates ranked by semantic matching and skills analysis.
          </p>
          <div className="hero-actions">
            <button className="btn-primary" onClick={onTryFree}>
              Try for Free
              <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
              </svg>
            </button>
            <a href="#how-it-works" className="btn-secondary">
              Learn More
            </a>
          </div>
        </div>
        <div className="hero-visual">
          <div className="hero-card">
            <div className="hero-card-header">
              <div className="hero-card-dot"></div>
              <div className="hero-card-dot"></div>
              <div className="hero-card-dot"></div>
            </div>
            <div className="hero-card-content">
              <div className="hero-card-line"></div>
              <div className="hero-card-line"></div>
              <div className="hero-card-line"></div>
              <div className="hero-card-dashed">
                <span>Upload Resume</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Features() {
  return (
    <section id="how-it-works" className="features">
      <div className="container">
        <div className="section-header">
          <div className="section-label">Workflow</div>
          <h2 className="section-title">How It Works</h2>
          <p className="section-subtitle">Three simple steps to find your perfect candidate</p>
        </div>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
              </svg>
            </div>
            <h3 className="feature-title">Upload Resumes</h3>
            <p className="feature-desc">Drag and drop multiple PDF resumes. Previous uploads are automatically replaced.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
              </svg>
            </div>
            <h3 className="feature-title">Add Job Description</h3>
            <p className="feature-desc">Paste the job requirements. Our AI extracts key skills automatically.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
              </svg>
            </div>
            <h3 className="feature-title">Get Ranked Results</h3>
            <p className="feature-desc">View ranked candidates with detailed analysis of strengths and gaps.</p>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-grid">
          <div className="footer-brand">
            <a href="#" className="logo">
              <div className="logo-mark">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
              </div>
              <span className="logo-text">ResumeScreen</span>
            </a>
            <p className="footer-desc">AI-powered resume screening that transforms hiring with intelligent candidate matching.</p>
          </div>
          <div className="footer-col">
            <h4>Product</h4>
            <ul className="footer-links">
              <li><a href="#">Features</a></li>
              <li><a href="#">How it Works</a></li>
              <li><a href="#">Pricing</a></li>
              <li><a href="#">API</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Resources</h4>
            <ul className="footer-links">
              <li><a href="#">Documentation</a></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Help Center</a></li>
              <li><a href="#">Status</a></li>
            </ul>
          </div>
          <div className="footer-col">
            <h4>Company</h4>
            <ul className="footer-links">
              <li><a href="#">About</a></li>
              <li><a href="#">Contact</a></li>
              <li><a href="#">Privacy</a></li>
              <li><a href="#">Terms</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p className="footer-copy">2026 ResumeScreen. All rights reserved.</p>
          <div className="footer-status">
            <span className="status-dot"></span>
            All systems operational
          </div>
        </div>
      </div>
    </footer>
  )
}

export default App
