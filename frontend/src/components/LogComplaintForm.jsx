import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { resetComplaint } from '../store/slices/complaintSlice';
import {
  ShieldAlert,
  CheckCircle2,
  Clock,
  RotateCcw,
  Save,
  AlertTriangle,
  Info,
} from 'lucide-react';
import './LogComplaintForm.css';

const PLACEHOLDER_TEXT = 'Awaiting AI extraction...';

/**
 * Reusable Read-Only Display Field.
 * Displays extracted value bound to Redux, or the muted placeholder.
 */
function ReadOnlyField({ label, value, isTextarea = false, className = '' }) {
  const hasValue = value !== null && value !== undefined && String(value).trim() !== '';

  return (
    <div className={`field-group ${className}`}>
      <label className="field-label">{label}</label>
      <div className={`readonly-box ${isTextarea ? 'textarea' : ''}`}>
        {hasValue ? (
          <span className="readonly-value">{String(value)}</span>
        ) : (
          <span className="readonly-placeholder">{PLACEHOLDER_TEXT}</span>
        )}
      </div>
    </div>
  );
}

/**
 * Styled Read-Only Badge Field for Triage values (Severity, Priority).
 */
function TriageBadgeField({ label, value }) {
  const hasValue = value !== null && value !== undefined && String(value).trim() !== '';

  const getBadgeClass = (val) => {
    if (!val) return '';
    const lower = String(val).toLowerCase();
    if (lower.includes('critical')) return 'critical';
    if (lower.includes('major')) return 'major';
    if (lower.includes('minor')) return 'minor';
    if (lower.includes('urgent')) return 'urgent';
    if (lower.includes('high')) return 'high';
    if (lower.includes('medium')) return 'medium';
    if (lower.includes('low')) return 'low';
    return 'major';
  };

  return (
    <div className="field-group">
      <label className="field-label">{label}</label>
      <div className="readonly-box">
        {hasValue ? (
          <span className={`triage-badge ${getBadgeClass(value)}`}>
            {String(value)}
          </span>
        ) : (
          <span className="readonly-placeholder">{PLACEHOLDER_TEXT}</span>
        )}
      </div>
    </div>
  );
}

export function LogComplaintForm() {
  const dispatch = useDispatch();
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint || {});

  // Compute status badge
  const isTriaged = Boolean(currentComplaint.initial_severity);

  // Formatted Quantity Affected with Unit
  const formattedQuantity = (() => {
    if (currentComplaint.quantity_affected !== null && currentComplaint.quantity_affected !== undefined) {
      const qty = currentComplaint.quantity_affected;
      const unit = currentComplaint.quantity_unit || '';
      return `${qty} ${unit}`.trim();
    }
    return null;
  })();

  const handleReset = () => {
    dispatch(resetComplaint());
  };

  return (
    <div className="log-complaint-card">
      {/* Header */}
      <header className="form-header">
        <div className="form-title-group">
          <h2 className="form-title">Log Customer Complaint</h2>
          <p className="form-subtitle">API &amp; FDF Quality Assurance Module</p>
        </div>

        {isTriaged ? (
          <div className="status-badge triaged">
            <span className="status-dot triaged" />
            <CheckCircle2 size={13} />
            <span>Triaged ({currentComplaint.initial_severity})</span>
          </div>
        ) : (
          <div className="status-badge pending">
            <span className="status-dot pending" />
            <Clock size={13} />
            <span>Pending Triage</span>
          </div>
        )}
      </header>

      {/* Form Body with 4 Numbered Sections */}
      <div className="form-body">
        {/* Section 1: Origin & Customer Details */}
        <section className="form-section">
          <h3 className="section-heading">
            1. ORIGIN &amp; CUSTOMER DETAILS
          </h3>
          <div className="grid-2-col">
            <ReadOnlyField
              label="Complaint Source"
              value={currentComplaint.complaint_source}
            />
            <ReadOnlyField
              label="Customer Name"
              value={currentComplaint.customer_name}
            />
          </div>
        </section>

        {/* Section 2: Product & Batch Identification */}
        <section className="form-section">
          <h3 className="section-heading">
            2. PRODUCT &amp; BATCH IDENTIFICATION
          </h3>
          <div className="grid-2-col">
            <ReadOnlyField
              label="Product Name"
              value={currentComplaint.product_name}
            />
            <ReadOnlyField
              label="Product Strength / Grade"
              value={currentComplaint.product_strength_grade}
            />
            <ReadOnlyField
              label="Batch / Lot Number"
              value={currentComplaint.batch_lot_number}
            />
            <ReadOnlyField
              label="Quantity Affected"
              value={formattedQuantity}
            />
            <ReadOnlyField
              label="Manufacturing Date"
              value={currentComplaint.manufacturing_date}
            />
            <ReadOnlyField
              label="Expiry Date"
              value={currentComplaint.expiry_date}
            />
          </div>
        </section>

        {/* Section 3: Complaint Details */}
        <section className="form-section">
          <h3 className="section-heading">
            3. COMPLAINT DETAILS
          </h3>
          <div className="grid-2-col">
            <ReadOnlyField
              label="Complaint Type"
              value={currentComplaint.complaint_type}
            />
            <ReadOnlyField
              label="Complaint Date"
              value={currentComplaint.complaint_date}
            />
            <div className="col-span-full">
              <ReadOnlyField
                label="Detailed Complaint Description"
                value={currentComplaint.detailed_description}
                isTextarea={true}
              />
            </div>
          </div>
        </section>

        {/* Section 4: Initial Assessment & Priority */}
        <section className="form-section">
          <h3 className="section-heading">
            4. INITIAL ASSESSMENT &amp; PRIORITY
          </h3>
          <div className="grid-2-col">
            <TriageBadgeField
              label="Initial Severity"
              value={currentComplaint.initial_severity}
            />
            <TriageBadgeField
              label="Priority"
              value={currentComplaint.priority}
            />
          </div>
        </section>
      </div>

      {/* Footer Action Buttons */}
      <footer className="form-footer">
        <button
          type="button"
          className="btn-reset"
          onClick={handleReset}
          title="Clear current complaint form back to initial state"
        >
          <RotateCcw size={14} />
          <span>Reset Form</span>
        </button>

        <button
          type="button"
          className="btn-disabled"
          disabled
          title="Save Complaint (Enabled once intake is complete)"
        >
          <Save size={14} />
          <span>Save Complaint</span>
        </button>
      </footer>
    </div>
  );
}

export default LogComplaintForm;
