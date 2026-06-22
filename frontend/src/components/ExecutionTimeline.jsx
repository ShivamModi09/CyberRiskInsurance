import React, { useState, useEffect } from 'react';
import { Brain, Search, GitMerge, ShieldCheck, Scale, BarChart3, CheckCircle2 } from 'lucide-react';

export default function ExecutionTimeline({ isLoading, hasRun, currentStep = 0 }) {
  const steps = [
    { label: "Supervisor Agent", icon: <Brain size={24} /> },
    { label: "Collector Agents", icon: <Search size={24} /> },
    { label: "Coordinator Agent", icon: <GitMerge size={24} /> },
    { label: "Fact Checker Agent", icon: <ShieldCheck size={24} /> },
    { label: "Underwriter Agent", icon: <Scale size={24} /> },
    { label: "Final Verdict", icon: <BarChart3 size={24} /> }
  ];

  const [activeStep, setActiveStep] = useState(-1);

  useEffect(() => {
    if (hasRun) {
      setActiveStep(5); // All complete
    } else if (isLoading || currentStep > 1) {
      // currentStep: 2 = Supervisor (idx 0), 3 = Collectors (idx 1)... 7 = Verdict (idx 5)
      setActiveStep(currentStep - 2);
    } else {
      setActiveStep(-1);
    }
  }, [isLoading, hasRun, currentStep]);

  return (
    <div className="glass-panel" style={{ padding: '24px 32px' }}>
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <h2 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)', fontSize: '1.2rem', fontWeight: '700' }}>
          Underwriting Workflow Pipeline
        </h2>
        <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem' }}>
          Step-by-step progression of the underwriting process.
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative', marginTop: '32px' }}>
        {/* Track Line Container */}
        <div style={{ position: 'absolute', top: '24px', left: '60px', right: '60px', height: '2px', background: 'rgba(0,0,0,0.1)', zIndex: 0 }}>
          {/* Animated active line */}
          <div style={{ 
              height: '100%',
              background: 'var(--accent-orange)',
              width: activeStep >= 0 ? `${(Math.min(activeStep, 5) / 5) * 100}%` : '0%',
              transition: 'width 0.5s ease-in-out',
              boxShadow: '0 0 10px rgba(243, 111, 33, 0.5)'
          }}></div>
        </div>

        {steps.map((step, idx) => {
          const isCompleted = activeStep > idx || hasRun;
          const isCurrent = activeStep === idx && !hasRun;
          
          return (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', zIndex: 2, width: '120px' }}>
              <div style={{
                width: '48px', height: '48px', borderRadius: '50%',
                display: 'flex', justifyContent: 'center', alignItems: 'center',
                background: isCompleted || isCurrent ? 'rgba(243, 111, 33, 0.1)' : 'var(--bg-base)',
                border: `2px solid ${isCompleted || isCurrent ? 'var(--accent-orange)' : 'var(--border-color)'}`,
                color: isCompleted || isCurrent ? 'var(--accent-orange)' : 'var(--text-secondary)',
                transition: 'all 0.3s',
                boxShadow: isCurrent ? '0 0 15px rgba(243, 111, 33, 0.4)' : 'none',
                position: 'relative'
              }}>
                {step.icon}
                {isCompleted && (
                  <div style={{ position: 'absolute', bottom: '-4px', right: '-4px', background: 'var(--bg-surface)', borderRadius: '50%', padding: '2px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <CheckCircle2 size={14} color="var(--accent-orange)" fill="var(--bg-surface)" strokeWidth={3} />
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <div style={{ 
                  fontSize: '0.8rem', textAlign: 'center', fontWeight: '600',
                  color: isCompleted || isCurrent ? 'var(--text-primary)' : 'rgba(0,0,0,0.3)',
                  lineHeight: '1.2'
                }}>
                  {step.label}
                </div>
                <div style={{ 
                  fontSize: '0.65rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700',
                  color: isCompleted || isCurrent ? 'var(--accent-orange)' : 'var(--text-secondary)',
                  opacity: isCompleted ? 0.8 : 1
                }}>
                  {isCompleted ? 'Completed' : (isCurrent ? 'Running' : 'Waiting')}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  );
}
