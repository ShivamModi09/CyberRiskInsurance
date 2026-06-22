import React, { useState } from 'react';
import { Calculator, Info } from 'lucide-react';

const modifierMetadata = {
  "Mergers and Acquisitions": { scale: "0-10+ Points", logic: "Lower score = More favourable (less integration risk)" },
  "Amount of sensitive information": { scale: "Customer Type & E-com", logic: "B2C + Ecommerce increases data breach severity" },
  "Domain Encryption": { scale: "Encrypted Ratio", logic: "100% encrypted domains = Favourable" },
  "Geographic Spread": { scale: "Country Count", logic: "Wider spread increases regulatory complexity" },
  "Internet footprint": { scale: "Domains × Size Multiplier", logic: "Larger footprint increases attack surface" },
  "Nature of services": { scale: "Low / Medium / High Risk", logic: "Higher risk industries increase cyber exposure" },
  "Organizational Complexity": { scale: "Subsidiary Count", logic: "More subsidiaries = broader threat landscape" },
  "Privacy Regulation": { scale: "Compliance Mentions", logic: "Published policy + Compliance = Favourable" },
  "Seasonality of sales": { scale: "Coefficient of Variation", logic: "High variance means peak outages are devastating" },
  "Volatility/Recovery in Sales": { scale: "Averaged Risk Index", logic: "Higher recovery complexity = Unfavourable" },
  "Applicability of Privacy Regulation": { scale: "SIC Code Mapping", logic: "Strict industries (Health/Finance) increase liability" },
  "B2C End Products": { scale: "Business Model", logic: "Direct consumer interaction increases privacy risk" },
  "Years in business": { scale: "Age in Years", logic: "Older enterprise = more established and favourable" }
};

export default function ModifierTable({ data }) {
  const [selectedModifier, setSelectedModifier] = useState(null);
  const [showInternalLogic, setShowInternalLogic] = useState(false);

  if (!data) return null;
  
  const getRatingBadge = (rating) => {
    const r = rating.toUpperCase();
    let badgeClass = "neutral";
    
    if (r === 'VERY FAVOURABLE' || r.includes('VERY FAVOURABLE')) {
      badgeClass = "emerald";
    } else if (r === 'PARTIALLY FAVOURABLE' || (r.includes('PARTIALLY FAVOURABLE') && !r.includes('UNFAVOURABLE'))) {
      badgeClass = "orange";
    } else if (r === 'FAVOURABLE' || (r.includes('FAVOURABLE') && !r.includes('PARTIALLY') && !r.includes('UNFAVOURABLE'))) {
      badgeClass = "teal";
    } else if (r === 'AVERAGE' || r.includes('AVERAGE') || r === 'NEUTRAL') {
      badgeClass = "slate";
    } else if (r === 'PARTIALLY UNFAVOURABLE' || r.includes('PARTIALLY UNFAVOURABLE')) {
      badgeClass = "warning";
    } else if (r === 'UNFAVOURABLE' || r.includes('UNFAVOURABLE')) {
      badgeClass = "danger";
    }

    return <span className={`badge ${badgeClass}`}>{rating.toUpperCase()}</span>;
  };

  return (
    <>
      <div className="glass-panel" style={{ padding: 0, display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '24px 24px 16px 24px', position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 11, borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Calculator size={20} color="var(--accent-orange)" /> Underwriter Modifiers
          </h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(0,0,0,0.05)', padding: '6px 12px', borderRadius: '20px' }}>
              <Info size={14} color="var(--accent-orange)" /> Actuarial logic derived from CNA underwriting matrix
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}>
              <span style={{ fontSize: '0.85rem', color: showInternalLogic ? 'var(--text-primary)' : 'var(--text-secondary)' }}>Show Internal Logic Details</span>
              <div style={{ 
                width: '40px', height: '22px', 
                background: showInternalLogic ? 'var(--accent-orange)' : 'var(--border-color)', 
                borderRadius: '12px', position: 'relative', transition: '0.3s' 
              }}>
                <div style={{ 
                  width: '18px', height: '18px', 
                  background: '#fff', borderRadius: '50%', 
                  position: 'absolute', top: '2px', 
                  left: showInternalLogic ? '20px' : '2px', 
                  transition: '0.3s' 
                }}></div>
              </div>
              <input 
                type="checkbox" 
                style={{ display: 'none' }} 
                checked={showInternalLogic} 
                onChange={(e) => setShowInternalLogic(e.target.checked)} 
              />
            </label>
          </div>
        </div>
        <div style={{ width: '100%', overflowX: 'auto', background: '#FFFFFF', borderRadius: '0 0 8px 8px' }}>
          <table style={{ width: '100%', minWidth: '1200px', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ background: '#F8FAFC', borderBottom: '2px solid #E2E8F0' }}>
              <tr>
                <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '40px' }}>#</th>
                <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '250px' }}>Modifier Name</th>
                {showInternalLogic && <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '120px' }}>Raw Score</th>}
                {showInternalLogic && <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '180px' }}>Scale</th>}
                {showInternalLogic && <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '250px' }}>Scoring Logic</th>}
                <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em', width: '200px' }}>Category Rating</th>
                <th style={{ padding: '16px 24px', fontSize: '0.7rem', textTransform: 'uppercase', color: '#64748B', fontWeight: '800', letterSpacing: '0.05em' }}>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {data.map((mod, index) => {
                const meta = modifierMetadata[mod.name] || { scale: "Variable", logic: "Derived dynamically based on inputs" };
                
                // Premium Badge Generator
                const r = mod.rating.toUpperCase();
                let colors = { bg: '#F8FAFC', text: '#64748B', border: '#E2E8F0' }; // Default Slate
                if (r === 'VERY FAVOURABLE' || r.includes('VERY FAVOURABLE')) {
                  colors = { bg: '#ECFDF5', text: '#059669', border: '#A7F3D0' };
                } else if (r === 'PARTIALLY FAVOURABLE' || (r.includes('PARTIALLY FAVOURABLE') && !r.includes('UNFAVOURABLE'))) {
                  colors = { bg: '#FEF3C7', text: '#D97706', border: '#FDE68A' };
                } else if (r === 'FAVOURABLE' || (r.includes('FAVOURABLE') && !r.includes('PARTIALLY') && !r.includes('UNFAVOURABLE'))) {
                  colors = { bg: '#F0FDF4', text: '#16A34A', border: '#BBF7D0' };
                } else if (r === 'PARTIALLY UNFAVOURABLE' || r.includes('PARTIALLY UNFAVOURABLE')) {
                  colors = { bg: '#FFF7ED', text: '#C2410C', border: '#FFEDD5' };
                } else if (r === 'UNFAVOURABLE' || r.includes('UNFAVOURABLE')) {
                  colors = { bg: '#FEF2F2', text: '#DC2626', border: '#FECACA' };
                }

                return (
                <tr key={mod.id} style={{ 
                  borderBottom: index === data.length - 1 ? 'none' : '1px solid #F1F5F9',
                  transition: 'background 0.2s ease',
                  background: '#FFFFFF'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#F8FAFC'}
                onMouseLeave={(e) => e.currentTarget.style.background = '#FFFFFF'}
                >
                  <td style={{ padding: '20px 24px', fontSize: '0.8rem', color: '#94A3B8', fontWeight: '800', fontFamily: 'monospace' }}>
                    {String(mod.id).padStart(2, '0')}
                  </td>
                  <td style={{ padding: '20px 24px', fontWeight: '800', color: '#0F172A', fontSize: '0.9rem', whiteSpace: 'nowrap' }}>
                    {mod.name}
                  </td>
                  
                  {showInternalLogic && (
                    <td style={{ padding: '20px 24px' }}>
                      <span style={{ 
                        fontFamily: 'monospace', color: '#F26A21', fontWeight: '800', 
                        background: 'rgba(242, 106, 33, 0.1)', border: '1px solid rgba(242, 106, 33, 0.2)',
                        padding: '4px 10px', borderRadius: '6px', fontSize: '0.85rem'
                      }}>
                        {mod.score}
                      </span>
                    </td>
                  )}
                  {showInternalLogic && (
                    <td style={{ padding: '20px 24px', fontSize: '0.8rem', color: '#64748B', fontWeight: '600' }}>
                      {meta.scale}
                    </td>
                  )}
                  {showInternalLogic && (
                    <td style={{ padding: '20px 24px', fontSize: '0.8rem', color: '#475569', lineHeight: '1.5' }}>
                      {meta.logic}
                    </td>
                  )}
                  
                  <td style={{ padding: '20px 24px' }}>
                    <span style={{ 
                      background: colors.bg, 
                      color: colors.text, 
                      border: `1px solid ${colors.border}`, 
                      padding: '6px 12px', 
                      borderRadius: '6px', 
                      fontSize: '0.7rem', 
                      fontWeight: '800', 
                      letterSpacing: '0.05em', 
                      display: 'inline-flex', 
                      alignItems: 'center', 
                      gap: '6px',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
                    }}>
                      <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: colors.text }}></div>
                      {r}
                    </span>
                  </td>
                  
                  <td style={{ padding: '20px 24px', fontSize: '0.85rem', color: '#475569', lineHeight: '1.6' }}>
                    {mod.rationale}
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
