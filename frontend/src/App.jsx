import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle } from 'lucide-react';
import Header from './components/Header';
import CompanyInput from './components/CompanyInput';
import VerdictCard from './components/VerdictCard';
import ReconciledProfile from './components/ReconciledProfile';
import AgentWorkflow from './components/AgentWorkflow';
import ModifierTable from './components/ModifierTable';
import ExecutionTimeline from './components/ExecutionTimeline';
import AgentResultCards from './components/AgentResultCards';
import LiveAgentTelemetry from './components/LiveAgentTelemetry';
import './components.css';

import { 
  reconciledProfile as mockReconciled, 
  factCheckerClaims as mockClaims, 
  modifiers as mockModifiers, 
  finalVerdict as mockVerdict 
} from './data/mockData';

function App() {
  const [company, setCompany] = useState('Microsoft');
  const [domain, setDomain] = useState('microsoft.com');
  const [isAutoPlaying, setIsAutoPlaying] = useState(false);
  const [hasRun, setHasRun] = useState(false);
  const [apiFailed, setApiFailed] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [toasts, setToasts] = useState([]);
  const hasShownToast = React.useRef(false);

  // Automated execution flow state
  const [currentStep, setCurrentStep] = useState(0);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  const fetchAnalysis = async () => {
    if (analysisData && !isAutoPlaying) return; // Don't refetch if already fetched unless forced
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, domain })
      });
      if (!response.ok) throw new Error(`API Error: ${response.status}`);
      const data = await response.json();
      setAnalysisData(data);
      setApiFailed(false);
    } catch (error) {
      console.error("Backend fetch failed. Falling back to mock data.", error);
      setApiFailed(true);
      setAnalysisData(null);
    }
  };

  // Automated Presentation Mode
  useEffect(() => {
    let interval;
    if (isAutoPlaying && currentStep > 0 && currentStep < 7) {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= 6) {
            if (!hasShownToast.current) {
              addToast("Analysis completed successfully", "success");
              hasShownToast.current = true;
            }
            setHasRun(true);
            setIsAutoPlaying(false);
            return 7;
          }
          return prev + 1;
        });
      }, 2000); // 2 second delay between stages
    }
    return () => clearInterval(interval);
  }, [isAutoPlaying, currentStep]);

  const handleRunFullAnalysis = async () => {
    setAnalysisData(null); // Force clear so new data loads
    setHasRun(false);
    hasShownToast.current = false;
    setCurrentStep(1);
    setIsAutoPlaying(true);
    await fetchAnalysis();
  };

  const handleNextStep = async () => {
    if (currentStep === 0) {
      setHasRun(false);
      await fetchAnalysis();
    }
    setCurrentStep(prev => {
      const next = prev < 7 ? prev + 1 : 7;
      if (next === 7) setHasRun(true);
      return next;
    });
  };

  const handlePrevStep = () => {
    setCurrentStep(prev => {
      const next = prev > 1 ? prev - 1 : 1;
      setHasRun(false); // Can't be fully run if stepping back
      return next;
    });
  };

  // If user changes inputs, reset step state so they can start fresh
  const handleCompanyChange = (val) => {
    setCompany(val);
    if (currentStep > 0) {
      setCurrentStep(0);
      setHasRun(false);
      setAnalysisData(null);
    }
  };

  const handleDomainChange = (val) => {
    setDomain(val);
    if (currentStep > 0) {
      setCurrentStep(0);
      setHasRun(false);
      setAnalysisData(null);
    }
  };

  const activeReconciled = analysisData ? analysisData.reconciled_profile : mockReconciled;
  const activeClaims = analysisData ? analysisData.fact_checker_claims : mockClaims;
  const activeModifiers = analysisData ? analysisData.modifiers : mockModifiers;
  const activeVerdict = analysisData ? analysisData.final_verdict : mockVerdict;

  // Progressive disclosure
  const showWorkflow = currentStep > 0 || hasRun;
  const showReconciled = hasRun || currentStep >= 4;
  const showModifiers = hasRun || currentStep >= 6;
  const showVerdict = hasRun || currentStep >= 7;

  return (
    <div className="dashboard-container">
      
      <div style={{ maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        <CompanyInput 
          company={company} 
          setCompany={handleCompanyChange} 
          domain={domain} 
          setDomain={handleDomainChange} 
          onNextStep={handleNextStep}
          onPrevStep={handlePrevStep}
          onRunFullAnalysis={handleRunFullAnalysis}
          currentStep={currentStep}
          isAutoPlaying={isAutoPlaying}
          hasRun={hasRun}
          apiFailed={apiFailed}
        />
      </div>

      {showWorkflow && (
        <div className="fade-in-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '32px', marginBottom: '32px' }}>
          <LiveAgentTelemetry 
            currentStep={currentStep} 
            isAutoPlaying={isAutoPlaying} 
            hasRun={hasRun} 
          />
        </div>
      )}

      {showVerdict && (
        <div className="fade-in-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '32px', marginBottom: '32px' }}>
          <AgentResultCards 
            reconciledProfile={activeReconciled}
            claims={activeClaims}
            modifiers={activeModifiers}
            verdict={activeVerdict}
          />
        </div>
      )}

      {showWorkflow && (
        <AgentWorkflow isLoading={isAutoPlaying} hasRun={hasRun} currentStep={currentStep} />
      )}

      <ExecutionTimeline isLoading={isAutoPlaying} hasRun={hasRun} currentStep={currentStep} />
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        {showReconciled && (
          <ReconciledProfile data={activeReconciled} claims={activeClaims} verdict={activeVerdict} />
        )}
        
        {showModifiers && <ModifierTable data={activeModifiers} />}
        
        {showVerdict && (
          <div className="fade-in-slide-up">
            <VerdictCard data={activeVerdict} modifiers={activeModifiers} claims={activeClaims} />
          </div>
        )}
      </div>

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.type === 'success' ? <ShieldCheck size={18} /> : <AlertTriangle size={18} />}
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
