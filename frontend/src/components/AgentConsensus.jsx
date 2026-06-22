import React from 'react';
import { Users, CheckCircle, AlertTriangle, HelpCircle, TrendingDown, Minus, TrendingUp } from 'lucide-react';

export default function AgentConsensus({ claims, modifiers }) {
  if (!claims || !modifiers) return null;

  const verifiedClaims = claims.filter(c => c.status.toLowerCase() === 'verified').length;
  const partialClaims = claims.filter(c => c.status.toLowerCase().includes('partial')).length;
  const unsupportedClaims = claims.filter(c => c.status.toLowerCase() === 'unsupported' || c.status.toLowerCase() === 'unknown').length;

  const favorableModifiers = modifiers.filter(m => m.rating.includes('FAVOURABLE') && !m.rating.includes('UNFAVOURABLE'));
  const neutralModifiers = modifiers.filter(m => m.rating === 'AVERAGE' || m.rating === 'NEUTRAL');
  const unfavorableModifiers = modifiers.filter(m => m.rating.includes('UNFAVOURABLE'));

  return (
    <div className="glass-panel" style={{ background: '#FFFFFF', padding: '24px', borderRadius: '8px', border: '1px solid var(--border-color)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Users size={18} color="var(--accent-orange)" /> Agent Consensus Matrix
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', flex: 1, justifyContent: 'center' }}>
        
        {/* Claims Row */}
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '12px', letterSpacing: '0.05em' }}>Fact Checker Corroboration</div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <CheckCircle size={16} color="#10B981" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{verifiedClaims}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Verified</div>
            </div>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <HelpCircle size={16} color="#F59E0B" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{partialClaims}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Partial</div>
            </div>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <AlertTriangle size={16} color="#EF4444" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{unsupportedClaims}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Unsupported</div>
            </div>
          </div>
        </div>

        {/* Modifiers Row */}
        <div>
          <div style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '12px', letterSpacing: '0.05em' }}>Actuarial Modifiers</div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <TrendingDown size={16} color="#10B981" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{favorableModifiers.length}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Favorable</div>
            </div>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <Minus size={16} color="#475569" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{neutralModifiers.length}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Neutral</div>
            </div>
            <div style={{ flex: 1, background: '#F8FAFC', border: '1px solid #E5E7EB', borderRadius: '6px', padding: '12px', textAlign: 'center' }}>
              <TrendingUp size={16} color="#EF4444" style={{ marginBottom: '4px' }} />
              <div style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--text-primary)' }}>{unfavorableModifiers.length}</div>
              <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Unfavorable</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
