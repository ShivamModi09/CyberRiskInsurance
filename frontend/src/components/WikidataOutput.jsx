import React from 'react';
import { Database } from 'lucide-react';

const WikidataOutput = ({ data }) => {
  if (!data) return null;

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-icon">
          <Database size={20} />
        </div>
        <div>
          <h2 className="card-title">Wikidata Output</h2>
          <p className="card-subtitle">Raw structured evidence extracted from Wikidata API</p>
        </div>
      </div>
      <div className="card-body">
        <div className="profile-grid">
          <div className="profile-item">
            <span className="profile-label">Company/Entity Name</span>
            <span className="profile-value">{data.entity_name || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Industry</span>
            <span className="profile-value">{data.industry || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Headquarters</span>
            <span className="profile-value">{data.headquarters || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Country</span>
            <span className="profile-value">{data.country || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Official Website</span>
            <span className="profile-value">{data.official_website || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Founded Year</span>
            <span className="profile-value">{data.founded_year || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Parent Organization</span>
            <span className="profile-value">{data.parent_organization || 'Not Available'}</span>
          </div>
          <div className="profile-item">
            <span className="profile-label">Subsidiaries</span>
            <span className="profile-value">{data.subsidiaries || 'Not Available'}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WikidataOutput;
