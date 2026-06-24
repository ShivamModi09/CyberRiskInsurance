import { ShieldCheck, Globe, Play, Info, ArrowRight, ArrowLeft, Network, Database, Users, Activity, WifiOff, RefreshCw, Sparkles } from 'lucide-react';

export default function CompanyInput({ company, setCompany, domain, setDomain, onNextStep, onPrevStep, onRunFullAnalysis, currentStep, isAutoPlaying, hasRun, apiFailed }) {
  const isValidDomain = domain === '' || /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(domain);

  const getStatusBadge = () => {
    if (isAutoPlaying) return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: '700', color: '#D97706', background: 'rgba(217, 119, 6, 0.1)', padding: '6px 12px', borderRadius: '99px', border: '1px solid rgba(217, 119, 6, 0.2)', letterSpacing: '0.05em' }}><RefreshCw size={14} className="pulse-glow" style={{ animation: 'spin 2s linear infinite' }} /> SYSTEM RUNNING</div>;
    if (apiFailed) return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: '700', color: '#FCA5A5', background: 'rgba(220, 38, 38, 0.1)', padding: '6px 12px', borderRadius: '99px', border: '1px solid rgba(220, 38, 38, 0.2)', letterSpacing: '0.05em' }}><WifiOff size={14} /> API DISCONNECTED</div>;
    return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', fontWeight: '700', color: '#34D399', background: 'rgba(52, 211, 153, 0.1)', padding: '6px 12px', borderRadius: '99px', border: '1px solid rgba(52, 211, 153, 0.2)', letterSpacing: '0.05em' }}><Activity size={14} /> SYSTEM CONNECTED</div>;
  };

  return (
    <div style={{ 
      background: 'linear-gradient(180deg, #020617 0%, #0F172A 100%)', 
      borderRadius: '24px', 
      padding: '40px 64px 64px 64px', 
      marginBottom: '32px',
      marginTop: '24px',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255,255,255,0.1)',
      color: '#FFFFFF',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      textAlign: 'center'
    }}>
      
      {/* Premium Studio Lighting Effects */}
      <div style={{ position: 'absolute', top: '-150px', left: '50%', transform: 'translateX(-50%)', width: '800px', height: '400px', background: 'radial-gradient(ellipse, rgba(242, 106, 33, 0.15) 0%, rgba(15, 23, 42, 0) 70%)', pointerEvents: 'none' }}></div>
      <div style={{ position: 'absolute', bottom: '0', left: '0', width: '100%', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent)' }}></div>

      <div style={{ position: 'relative', zIndex: 1, width: '100%' }}>
        
        {/* Sleek Integrated Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: '64px' }}>
          <img src="/exl-logo.png" alt="EXL Logo" style={{ height: '28px', objectFit: 'contain', filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))' }} />
          {getStatusBadge()}
        </div>

        {/* Hero Content */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '32px' }}>
          <span style={{ fontSize: '0.7rem', padding: '6px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '99px', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8', fontWeight: '600', letterSpacing: '0.1em', backdropFilter: 'blur(10px)' }}>
            <Network size={12} color="#F26A21" /> MULTI-AGENT
          </span>
          <span style={{ fontSize: '0.7rem', padding: '6px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '99px', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8', fontWeight: '600', letterSpacing: '0.1em', backdropFilter: 'blur(10px)' }}>
            <Database size={12} color="#F26A21" /> EVIDENCE-DRIVEN
          </span>
        </div>

        <div role="heading" aria-level="1" style={{ 
          fontSize: '4rem', 
          fontWeight: '800', 
          margin: '0 0 24px 0', 
          letterSpacing: '-0.04em', 
          lineHeight: '1.1',
          color: 'transparent',
          backgroundImage: 'linear-gradient(180deg, #FFFFFF 0%, #94A3B8 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text'
        }}>
          Cyber Risk Rater
        </div>
        
        <p style={{ fontSize: '1.15rem', color: '#64748B', margin: '0 auto 56px auto', maxWidth: '650px', lineHeight: '1.6', fontWeight: '400' }}>
          Deploy an autonomous swarm of AI underwriting agents to extract, corroborate, and analyze target entity risk profiles in real-time.
        </p>

        {/* Unified Pill Search Bar */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          background: 'rgba(255,255,255,0.03)', 
          border: '1px solid rgba(255,255,255,0.1)', 
          borderRadius: '99px', 
          padding: '8px', 
          maxWidth: '800px', 
          margin: '0 auto',
          backdropFilter: 'blur(20px)',
          boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)'
        }}>
          
          <div style={{ flex: 1, position: 'relative' }}>
            <input 
              type="text" 
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Target Company (e.g. Microsoft)"
              disabled={isAutoPlaying}
              style={{ width: '100%', padding: '16px 24px', fontSize: '1.05rem', fontWeight: '500', background: 'transparent', border: 'none', color: '#FFFFFF', outline: 'none' }}
            />
          </div>
          
          <div style={{ width: '1px', height: '32px', background: 'rgba(255,255,255,0.1)' }}></div>
          
          <div style={{ flex: 1, position: 'relative' }}>
            <input 
              type="text" 
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="Primary Domain (e.g. microsoft.com)"
              disabled={isAutoPlaying}
              style={{ width: '100%', padding: '16px 24px', fontSize: '1.05rem', fontWeight: '500', background: 'transparent', border: 'none', color: '#FFFFFF', outline: 'none' }}
            />
          </div>
          
          <button 
            onClick={onRunFullAnalysis}
            disabled={isAutoPlaying || !company || !domain || !isValidDomain}
            style={{ 
              background: 'linear-gradient(135deg, #F26A21 0%, #D94E07 100%)', 
              color: '#FFFFFF', 
              border: 'none', 
              borderRadius: '99px', 
              padding: '16px 32px', 
              fontSize: '0.95rem', 
              fontWeight: '800', 
              letterSpacing: '0.05em',
              cursor: (isAutoPlaying || !company || !domain || !isValidDomain) ? 'not-allowed' : 'pointer',
              opacity: (isAutoPlaying || !company || !domain || !isValidDomain) ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'transform 0.2s, box-shadow 0.2s',
              boxShadow: '0 4px 15px rgba(242, 106, 33, 0.4)'
            }}
          >
            {isAutoPlaying ? (
              <><div className="loader-small" style={{ width: '16px', height: '16px', borderColor: 'rgba(255,255,255,0.3)', borderLeftColor: '#FFF' }}></div> EXECUTING</>
            ) : (
              <><Sparkles size={16} fill="currentColor" /> RUN INTELLIGENCE</>
            )}
          </button>
        </div>
        
        {!isValidDomain && <div style={{ color: '#FCA5A5', fontSize: '0.85rem', marginTop: '16px', fontWeight: '500' }}>Invalid domain format detected.</div>}

        {/* Subtle Step Controls below */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '48px' }}>
          <button 
            onClick={onPrevStep}
            disabled={currentStep <= 0 || isAutoPlaying}
            style={{ 
              background: 'transparent', 
              color: '#64748B', 
              border: 'none', 
              fontSize: '0.85rem', 
              fontWeight: '600',
              cursor: (currentStep <= 0 || isAutoPlaying) ? 'not-allowed' : 'pointer',
              opacity: (currentStep <= 0 || isAutoPlaying) ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'color 0.2s'
            }}
          >
            <ArrowLeft size={16} /> PREVIOUS STEP
          </button>
          
          <button 
            onClick={onNextStep}
            disabled={currentStep >= 7 || isAutoPlaying || !company || !domain || !isValidDomain}
            style={{ 
              background: 'transparent', 
              color: '#94A3B8', 
              border: 'none', 
              fontSize: '0.85rem', 
              fontWeight: '600',
              cursor: (currentStep >= 7 || isAutoPlaying || !company || !domain || !isValidDomain) ? 'not-allowed' : 'pointer',
              opacity: (currentStep >= 7 || isAutoPlaying || !company || !domain || !isValidDomain) ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              transition: 'color 0.2s'
            }}
          >
            NEXT STEP <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
