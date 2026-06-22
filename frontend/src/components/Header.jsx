import { Activity, WifiOff, RefreshCw } from 'lucide-react';

export default function Header({ isLoading, apiFailed }) {
  const getStatusBadge = () => {
    if (isLoading) return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: '800', color: '#D97706', background: '#FEF3C7', padding: '8px 16px', borderRadius: '99px' }}><RefreshCw size={16} className="pulse-glow" style={{ animation: 'spin 2s linear infinite' }} /> SYSTEM RUNNING</div>;
    if (apiFailed) return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: '800', color: '#DC2626', background: '#FEF2F2', padding: '8px 16px', borderRadius: '99px' }}><WifiOff size={16} /> API DISCONNECTED</div>;
    return <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', fontWeight: '800', color: '#059669', background: '#ECFDF5', padding: '8px 16px', borderRadius: '99px' }}><Activity size={16} /> SYSTEM CONNECTED</div>;
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '20px 40px', 
      background: '#FFFFFF', 
      borderBottom: '1px solid #E2E8F0',
      width: '100%',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
    }}>
      
      <div>
        <img src="/exl-logo.png" alt="EXL Logo" style={{ height: '32px', objectFit: 'contain' }} />
      </div>
      
      <div>
        {getStatusBadge()}
      </div>
      
    </div>
  );
}
