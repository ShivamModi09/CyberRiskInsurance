import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, UserCheck } from 'lucide-react';

export default function HeroDecisionCard({ company, domain, verdict, claims }) {
  if (!verdict) return null;

  const scoreNum = parseFloat(verdict.underwritingScore.replace('%', '')) || 0;
  const isZeroConfidence = scoreNum === 0;

  const rCat = verdict.riskCategory.toUpperCase();
  
  let riskColor = '#475569';
  let riskBg = 'rgba(71,85,105,0.1)';
  let MainIcon = ShieldCheck;
  
  if (rCat.includes('VERY FAVOURABLE') || rCat === 'FAVOURABLE') {
    riskColor = '#10B981'; // Green
    riskBg = 'rgba(16,185,129,0.1)';
    MainIcon = ShieldCheck;
  } else if (rCat.includes('PARTIALLY FAVOURABLE') || rCat.includes('AVERAGE')) {
    riskColor = '#F59E0B'; // Amber
    riskBg = 'rgba(245,158,11,0.1)';
    MainIcon = UserCheck;
  } else if (rCat.includes('UNFAVOURABLE')) {
    riskColor = '#EF4444'; // Red
    riskBg = 'rgba(239,68,68,0.1)';
    MainIcon = ShieldAlert;
  }

  let recommendedAction = "Proceed with Standard Review";
  if (verdict.humanEscalation) {
    recommendedAction = "Escalate to Senior Underwriter for Review";
    riskColor = '#EF4444';
    riskBg = 'rgba(239,68,68,0.1)';
    MainIcon = AlertTriangle;
  } else if (rCat.includes('VERY FAVOURABLE') || rCat === 'FAVOURABLE') {
    recommendedAction = "Proceed with Automated Binding";
  } else if (rCat.includes('UNFAVOURABLE')) {
    recommendedAction = "Decline / Refer to Specialist";
  }

  return (
    <div className="glass-panel" style={{ 
      background: '#FFFFFF', 
      border: `2px solid ${riskColor}`, 
      boxShadow: `0 8px 32px ${riskBg}`,
      padding: '32px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{ position: 'absolute', top: '-20px', right: '-20px', opacity: 0.05, transform: 'scale(3)' }}>
        <MainIcon size={120} color={riskColor} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative', zIndex: 2 }}>
        
        {/* Left Side: Verdict & Action */}
        <div style={{ flex: 2 }}>
          <div style={{ display: 'inline-block', background: riskBg, color: riskColor, padding: '6px 12px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
            Final Decision
          </div>
          <h2 style={{ margin: '0 0 8px 0', fontSize: '2.5rem', color: 'var(--text-primary)', fontWeight: '800' }}>
            {rCat}
          </h2>
          <div style={{ fontSize: '1.25rem', color: riskColor, fontWeight: '600', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <MainIcon size={24} /> {recommendedAction}
          </div>

          <div style={{ display: 'flex', gap: '32px', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
            <div>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '4px' }}>Target Entity</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: 'var(--text-primary)' }}>{company}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{domain}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '4px' }}>Workflow Status</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700', color: verdict.humanEscalation ? '#EF4444' : '#10B981' }}>
                {verdict.humanEscalation ? 'Human Escalation Required' : 'Fully Automated'}
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Confidence Score */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
          <div style={{ background: '#F8FAFC', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '24px', textAlign: 'center', minWidth: '200px' }}>
            <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '8px' }}>Evidence Confidence</div>
            <div style={{ fontSize: '3rem', fontWeight: '800', color: isZeroConfidence ? '#EF4444' : 'var(--accent-orange)', lineHeight: '1' }}>
              {verdict.underwritingScore}
            </div>
            <div style={{ marginTop: '12px', display: 'inline-block', background: isZeroConfidence || verdict.confidenceBand === 'Low' ? 'rgba(239,68,68,0.1)' : 'rgba(243, 111, 33, 0.1)', color: isZeroConfidence || verdict.confidenceBand === 'Low' ? '#EF4444' : 'var(--accent-orange)', padding: '4px 12px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: '700', textTransform: 'uppercase' }}>
              {verdict.confidenceBand} Band
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
