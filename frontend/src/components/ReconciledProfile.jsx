import React from 'react';
import { Database, ShieldCheck } from 'lucide-react';

export default function ReconciledProfile({ data, claims, verdict }) {
  if (!data) return null;

  const scoreNum = verdict ? (parseFloat(verdict.underwritingScore.replace('%', '')) || 0) : 100;
  const isZeroConfidence = scoreNum === 0;

  const getClaimData = (claimName) => {
    if (!claims || !claimName) return { status: isZeroConfidence ? "Provisional" : "Unknown", sourceCount: 0 };
    const claim = claims.find(c => c.claim === claimName);
    if (claim) return claim;
    return { status: isZeroConfidence ? "Provisional" : "Unknown", sourceCount: 0 };
  };

  const getBadge = (status) => {
    if (!status) return null;
    const s = status.toLowerCase();
    if (s === "verified") return <span style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10B981', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>Verified</span>;
    if (s.includes("partial")) return <span style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>Partial</span>;
    if (s.includes("unsupported")) return <span style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>Unsupported</span>;
    if (s === "provisional") return <span style={{ background: 'rgba(71, 85, 105, 0.1)', color: '#475569', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>Provisional</span>;
    return <span style={{ background: 'rgba(71, 85, 105, 0.1)', color: '#475569', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>{status}</span>;
  };

  const getConfidenceLevel = (status) => {
    if (!status) return { text: "None", color: "#475569" };
    const s = status.toLowerCase();
    if (s === "verified") return { text: "High", color: "#10B981" };
    if (s.includes("partial")) return { text: "Medium", color: "#F59E0B" };
    if (s.includes("unsupported")) return { text: "Low", color: "#EF4444" };
    return { text: "None", color: "#475569" };
  };

  let formattedRevenue = data.revenue;
  if (typeof formattedRevenue === 'string' && formattedRevenue.startsWith('$')) {
    formattedRevenue = formattedRevenue.replace(/\s/g, '');
  }

  const profileItems = [
    { label: "Revenue", value: formattedRevenue, claimName: "revenue", collectors: "SEC Collector, Wikidata" },
    { label: "Subsidiaries Count", value: data.subsidiariesCount, claimName: "subsidiaries_count", collectors: "SEC Collector, Wikidata" },
    { label: "Acquisitions Count", value: data.acquisitionsCount, claimName: "acquisitions_count", collectors: "Wikidata, Wikipedia" },
    { label: "Customer Type", value: data.customerType, claimName: "customer_type", collectors: "DB Collector, Wikipedia" },
    { label: "E-Commerce Presence", value: (data.ecommercePlatform || data.has_ecommerce || data.ecommerce) ? "True" : "False", claimName: "has_ecommerce", collectors: "Domain Scraper" },
    { label: "Countries of Operations", value: data.countriesOfOps, claimName: null, collectors: "DB Collector, Wikidata" },
    { label: "Privacy Policy", value: data.privacyPolicy ? "Published" : "Unknown", claimName: "privacy_policy_published", collectors: "Domain Scraper" },
  ];

  return (
    <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px', background: '#FFFFFF', borderColor: '#E5E7EB', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
      <div style={{ borderBottom: '1px solid #E5E7EB', paddingBottom: '16px' }}>
         <h2 style={{ margin: 0, color: '#0F172A', display: 'flex', alignItems: 'center', gap: '8px' }}>
           <Database size={24} color="#F36F21" /> Reconciled Profile & Fact Checker
         </h2>
         <p style={{ fontSize: '0.9rem', margin: '8px 0 0 0', color: '#475569' }}>
           Merged entity profile continuously corroborated against raw scraped collector evidence.
         </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
         {/* Table Header / Legend */}
         <div style={{ display: 'flex', alignItems: 'center', padding: '0 16px 8px 16px', borderBottom: '1px solid #E5E7EB', marginBottom: '8px' }}>
           <div style={{ flex: '0 0 35%', fontSize: '0.75rem', fontWeight: '800', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Raw Extraction</div>
           <div style={{ flex: '0 0 10%', display: 'flex', justifyContent: 'center' }}>
             <ShieldCheck size={16} color="#CBD5E1" />
           </div>
           <div style={{ flex: '1', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', fontWeight: '800', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
             <span>Verification Engine</span>
             <span>Confidence</span>
           </div>
         </div>

         {/* Sleek Comparison Strips */}
         {profileItems.map((item, idx) => {
           const claimData = getClaimData(item.claimName);
           const conf = getConfidenceLevel(claimData.status);
           const hasClaim = !!item.claimName;
           
           return (
             <div key={idx} style={{ 
               display: 'flex', 
               alignItems: 'stretch', 
               background: '#FFFFFF', 
               border: '1px solid #E5E7EB', 
               borderRadius: '8px', 
               overflow: 'hidden',
               boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
               transition: 'all 0.2s ease-in-out',
               cursor: 'default'
             }}
             onMouseEnter={(e) => {
               e.currentTarget.style.transform = 'translateY(-1px)';
               e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
               e.currentTarget.style.borderColor = '#CBD5E1';
             }}
             onMouseLeave={(e) => {
               e.currentTarget.style.transform = 'translateY(0)';
               e.currentTarget.style.boxShadow = '0 1px 2px rgba(0,0,0,0.02)';
               e.currentTarget.style.borderColor = '#E5E7EB';
             }}
             >
               
               {/* Left Zone: Raw Extraction */}
               <div style={{ flex: '0 0 35%', background: '#F8FAFC', padding: '12px 16px', borderRight: '1px dashed #E5E7EB', display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '4px' }}>
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                   <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#334155' }}>{item.label}</span>
                   <span style={{ fontSize: '0.65rem', color: '#94A3B8', fontFamily: 'monospace', background: '#F1F5F9', padding: '2px 6px', borderRadius: '4px' }}>{item.claimName || 'N/A'}</span>
                 </div>
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: '4px' }}>
                   <div style={{ fontSize: '1rem', fontWeight: '800', color: '#0F172A' }}>
                     {item.value === "True" || item.value === "Published" ? (
                        <span style={{ color: '#059669' }}>{item.value}</span>
                     ) : item.value === "False" || item.value === "Unknown" || item.value === "Not Available" ? (
                        <span style={{ color: '#94A3B8', fontWeight: '600' }}>{item.value}</span>
                     ) : (
                        <span>{item.value}</span>
                     )}
                   </div>
                   <div style={{ fontSize: '0.65rem', color: '#F26A21', display: 'flex', alignItems: 'center', gap: '3px', fontWeight: '600' }}>
                     <Database size={10} /> {item.collectors.split(',')[0]} {item.collectors.includes(',') && '+'}
                   </div>
                 </div>
               </div>

               {/* Middle Zone: Engine Connector */}
               <div style={{ flex: '0 0 10%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'linear-gradient(to right, #F8FAFC, #FFFFFF)' }}>
                 <div style={{ display: 'flex', alignItems: 'center', color: '#CBD5E1', gap: '4px' }}>
                   <div style={{ width: '12px', height: '1px', background: '#E5E7EB' }}></div>
                   <ShieldCheck size={14} color={hasClaim ? (conf.color === '#EF4444' ? '#FCA5A5' : conf.color) : '#E5E7EB'} />
                   <div style={{ width: '12px', height: '1px', background: '#E5E7EB' }}></div>
                 </div>
               </div>

               {/* Right Zone: Fact Checked Result */}
               <div style={{ flex: '1', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#FFFFFF' }}>
                 <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                   <div style={{ width: '110px' }}>
                     {hasClaim ? getBadge(claimData.status) : <span style={{ background: '#F1F5F9', color: '#94A3B8', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: '700', textTransform: 'uppercase' }}>Unverified</span>}
                   </div>
                   <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                     <span style={{ fontSize: '0.75rem', fontWeight: '600', color: '#475569' }}>
                       {hasClaim ? `${claimData.sourceCount} Sources Corroborated` : 'No sources analyzed'}
                     </span>
                     {hasClaim && (
                       <span style={{ fontSize: '0.65rem', color: '#94A3B8' }}>Cross-referencing active</span>
                     )}
                   </div>
                 </div>
                 
                 <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                   <span style={{ fontWeight: '800', color: hasClaim ? conf.color : '#CBD5E1', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                     {hasClaim ? conf.text : 'N/A'}
                   </span>
                 </div>
               </div>

             </div>
           );
         })}
      </div>
    </div>
  );
}
