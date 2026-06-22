import React from 'react';
import { Target, TrendingUp, TrendingDown, Info } from 'lucide-react';

export default function KeyFindings({ reconciledProfile, modifiers, verdict }) {
  if (!modifiers || !reconciledProfile) return null;

  const getHighlights = () => {
    const highlights = [];
    
    // Privacy Policy
    if (reconciledProfile.privacyPolicy) {
      highlights.push({ icon: <TrendingDown color="#10B981" size={16} />, text: "Published privacy policy and compliance signals detected", type: "positive" });
    } else {
      highlights.push({ icon: <TrendingUp color="#EF4444" size={16} />, text: "No explicit privacy policy or compliance framework found", type: "negative" });
    }

    // Subsidiaries
    if (reconciledProfile.subsidiariesCount > 0) {
      highlights.push({ icon: <Info color="#F59E0B" size={16} />, text: `Verified ${reconciledProfile.subsidiariesCount} subsidiaries, increasing organizational complexity`, type: "neutral" });
    }

    // E-commerce
    if (reconciledProfile.ecommercePlatform || reconciledProfile.has_ecommerce) {
      highlights.push({ icon: <TrendingUp color="#F59E0B" size={16} />, text: "E-commerce presence increases data breach severity and privacy risk", type: "neutral" });
    } else {
      highlights.push({ icon: <TrendingDown color="#10B981" size={16} />, text: "No direct e-commerce exposure reduces B2C data liability", type: "positive" });
    }

    // Find the strongest positive and negative modifier that isn't already covered
    const bestMod = modifiers.find(m => m.rating.includes('VERY FAVOURABLE'));
    if (bestMod) {
      highlights.push({ icon: <TrendingDown color="#10B981" size={16} />, text: bestMod.rationale, type: "positive" });
    }

    const worstMod = modifiers.find(m => m.rating.includes('UNFAVOURABLE'));
    if (worstMod) {
      highlights.push({ icon: <TrendingUp color="#EF4444" size={16} />, text: worstMod.rationale, type: "negative" });
    }

    // Evidence coverage
    if (verdict?.confidenceBand === 'High' || verdict?.confidenceBand === 'Medium') {
      highlights.push({ icon: <Target color="#10B981" size={16} />, text: "Strong evidence coverage across multiple independent sources", type: "positive" });
    }

    return highlights.slice(0, 5); // Max 5 findings
  };

  const findings = getHighlights();

  return (
    <div className="glass-panel" style={{ background: '#FFFFFF', padding: '24px', borderRadius: '8px', border: '1px solid var(--border-color)', height: '100%' }}>
      <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Target size={18} color="var(--accent-orange)" /> Executive Key Findings
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {findings.map((f, idx) => (
          <div key={idx} style={{ 
            display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px', 
            background: f.type === 'positive' ? 'rgba(16,185,129,0.05)' : (f.type === 'negative' ? 'rgba(239,68,68,0.05)' : '#F8FAFC'),
            borderLeft: `3px solid ${f.type === 'positive' ? '#10B981' : (f.type === 'negative' ? '#EF4444' : '#F59E0B')}`,
            borderRadius: '4px'
          }}>
            <div style={{ marginTop: '2px' }}>{f.icon}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>{f.text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
