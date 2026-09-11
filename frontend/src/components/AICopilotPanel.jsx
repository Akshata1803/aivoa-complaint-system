import React, { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setComplaint } from '../store/slices/complaintSlice';
import {
  Sparkles,
  UploadCloud,
  FileText,
  ChevronDown,
  ChevronUp,
  Send,
  Bot,
  User,
  Info,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ShieldAlert,
  ClipboardList,
} from 'lucide-react';
import './AICopilotPanel.css';

const API_BASE = 'http://127.0.0.1:8000';

const INITIAL_GREETING =
  'Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you.';

export function AICopilotPanel() {
  const dispatch = useDispatch();
  const currentComplaint = useSelector((state) => state.complaint.currentComplaint || {});

  // Component states
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'initial',
      sender: 'bot',
      text: INITIAL_GREETING,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [bottomInput, setBottomInput] = useState('');
  const [pasteInput, setPasteInput] = useState('');
  const [isPasteExpanded, setIsPasteExpanded] = useState(false);
  const [isRiskAssessmentExpanded, setIsRiskAssessmentExpanded] = useState(true);

  // Extraction Progress State
  const [isExtracting, setIsExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStatus, setProgressStatus] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);

  // Risk Classification Badge Styling Helper
  const getRiskBadgeClass = (val) => {
    if (!val) return 'class-2';
    const lower = String(val).toLowerCase();
    if (lower.includes('class i') && !lower.includes('class ii') && !lower.includes('class iii')) return 'class-1';
    if (lower.includes('class iii')) return 'class-3';
    if (lower.includes('class ii')) return 'class-2';
    return 'class-2';
  };

  // Determine if complaint has been triaged
  const hasTriage = Boolean(currentComplaint?.initial_severity);

  // Auto-scroll chat log on new messages
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isExtracting]);

  /**
   * Helper to simulate realistic progress bar increments while waiting for LLM
   */
  const runProgressAnimation = (startMessage) => {
    setIsExtracting(true);
    setProgress(15);
    setProgressStatus(startMessage || 'Analyzing complaint...');

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev < 40) {
          setProgressStatus('Extracting product & batch identification...');
          return prev + 12;
        } else if (prev < 72) {
          setProgressStatus('Running QA triage & regulatory risk assessment...');
          return prev + 8;
        } else if (prev < 90) {
          setProgressStatus('Finalizing schema validation & database sync...');
          return prev + 4;
        }
        return prev;
      });
    }, 450);

    return timer;
  };

  /**
   * 1. Handle Text Intake / Edit Submit
   */
  const handleTextSubmit = async (textToSend) => {
    const trimmed = textToSend.trim();
    if (!trimmed || isExtracting) return;

    const isEdit = Boolean(currentComplaint.id);

    // Add user message to chat log
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setChatMessages((prev) => [...prev, userMsg]);

    // Clear inputs
    setBottomInput('');
    setPasteInput('');
    setIsPasteExpanded(false);

    // Start progress bar
    const progressTimer = runProgressAnimation(
      isEdit ? 'Processing complaint correction...' : 'Analyzing complaint narrative...'
    );

    try {
      const response = await fetch(`${API_BASE}/complaints/from-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: trimmed,
          complaint_id: currentComplaint.id || null,
        }),
      });

      clearInterval(progressTimer);
      setProgress(100);
      setProgressStatus('Extraction completed!');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }

      const savedData = await response.json();

      // Dispatch to Redux to populate the left panel form
      dispatch(setComplaint(savedData));

      // Build confirmation message for chat
      let confirmationText = '';
      if (isEdit) {
        confirmationText = `Updated Complaint #${savedData.id}: Successfully merged corrections into the form. Batch: ${
          savedData.batch_lot_number || 'N/A'
        }, Quantity: ${savedData.quantity_affected ? `${savedData.quantity_affected} ${savedData.quantity_unit || ''}` : 'N/A'}. Severity: ${
          savedData.initial_severity || 'Assigned'
        }.`;
      } else {
        confirmationText = `Extracted: ${savedData.product_name || 'Pharmaceutical Product'}${
          savedData.product_strength_grade ? ` (${savedData.product_strength_grade})` : ''
        } complaint from ${savedData.customer_name || 'Customer'}. Severity: ${
          savedData.initial_severity || 'Major'
        }, Priority: ${savedData.priority || 'High'}. Form fields have been populated.`;
      }

      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: confirmationText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      clearInterval(progressTimer);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        isError: true,
        text: `Extraction failed: ${err.message}. Please verify the backend service is reachable.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setTimeout(() => {
        setIsExtracting(false);
        setProgress(0);
      }, 500);
    }
  };

  /**
   * 2. Handle Document Upload Submit (PDF or EML)
   */
  const handleFileUpload = async (file) => {
    if (!file || isExtracting) return;

    // Check file extension
    const name = file.name.toLowerCase();
    if (!name.endsWith('.pdf') && !name.endsWith('.eml') && !name.endsWith('.txt') && !name.endsWith('.docx')) {
      alert('Please upload a PDF or EML complaint document.');
      return;
    }

    // Add user action to chat log
    const userMsg = {
      id: Date.now().toString(),
      sender: 'user',
      text: `Uploaded document: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setChatMessages((prev) => [...prev, userMsg]);

    // Start progress
    const progressTimer = runProgressAnimation(`Parsing document ${file.name} with pdfplumber...`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/complaints/from-document`, {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressTimer);
      setProgress(100);
      setProgressStatus('Document extraction completed!');

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed (${response.status})`);
      }

      const savedData = await response.json();

      // Dispatch to Redux
      dispatch(setComplaint(savedData));

      const botMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: `Extracted complaint from ${file.name}: Created Complaint #${savedData.id} for ${
          savedData.product_name || 'Product'
        } (${savedData.product_strength_grade || ''}) reported by ${
          savedData.customer_name || 'Reporting Entity'
        }. Batch: ${savedData.batch_lot_number || 'N/A'}. Severity: ${
          savedData.initial_severity || 'Critical'
        }. All form fields populated.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      clearInterval(progressTimer);
      const errorMsg = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        isError: true,
        text: `Document extraction failed: ${err.message}. Please check document formatting and try again.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setChatMessages((prev) => [...prev, errorMsg]);
    } finally {
      setTimeout(() => {
        setIsExtracting(false);
        setProgress(0);
      }, 500);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  // Drag & Drop Handlers
  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="copilot-panel-card">
      {/* Header */}
      <header className="copilot-header">
        <div className="copilot-title-group">
          <div className="copilot-icon-badge">
            <Sparkles size={18} />
          </div>
          <h2 className="copilot-title">AI Complaint Intake Assistant</h2>
        </div>
        <span className="beta-badge">BETA</span>
      </header>

      {/* Main Body */}
      <div className="copilot-body">
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.eml,.docx,.txt"
          style={{ display: 'none' }}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileUpload(e.target.files[0]);
            }
          }}
        />

        {/* Upload Drop Zone */}
        <div
          className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          title="Click or drag a file to upload"
        >
          <div className="upload-icon-circle">
            <UploadCloud size={24} />
          </div>
          <p className="upload-primary-text">Drag &amp; drop complaint document here</p>
          <span className="upload-secondary-text">or click to browse</span>
        </div>

        {/* Green Info Box */}
        <div className="format-info-box">
          <div className="format-info-left">
            <Info size={14} />
            <span>Supported formats: PDF, DOCX, TXT, EML</span>
          </div>
          <span>Max file size: 10MB</span>
        </div>

        {/* OR Divider */}
        <div className="or-divider">
          <span className="or-line" />
          <span className="or-label">OR</span>
          <span className="or-line" />
        </div>

        {/* Collapsible Paste Area */}
        <div>
          <button
            type="button"
            className="paste-toggle-btn"
            style={{ width: '100%' }}
            onClick={() => setIsPasteExpanded((prev) => !prev)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={15} color="#2563eb" />
              <span>Paste Complaint Text / Email</span>
            </div>
            {isPasteExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          {isPasteExpanded && (
            <div className="paste-content-box" style={{ marginTop: '8px' }}>
              <textarea
                className="paste-textarea"
                placeholder="Paste raw complaint text, customer email body, or call transcript here..."
                value={pasteInput}
                onChange={(e) => setPasteInput(e.target.value)}
                disabled={isExtracting}
              />
              <div className="paste-actions-row">
                <button
                  type="button"
                  className="btn-extract-primary"
                  onClick={() => handleTextSubmit(pasteInput)}
                  disabled={!pasteInput.trim() || isExtracting}
                >
                  {isExtracting ? (
                    <>
                      <Loader2 size={14} className="animate-spin" />
                      <span>Extracting...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={14} />
                      <span>Extract Complaint</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* EXTRACTION PROGRESS (Visible only when request is in flight) */}
        {isExtracting && (
          <div className="progress-container">
            <div className="progress-header">
              <span>EXTRACTION PROGRESS</span>
              <span>{Math.min(progress, 100)}%</span>
            </div>
            <div className="progress-bar-bg">
              <div className="progress-bar-fill" style={{ width: `${Math.min(progress, 100)}%` }} />
            </div>
            <p className="progress-status-text">
              <Loader2 size={13} className="animate-spin" />
              <span>{progressStatus}</span>
            </p>
          </div>
        )}

        {/* AI ASSISTANT Chat Log Section */}
        <div className="chat-section">
          <label className="chat-section-label">AI ASSISTANT</label>
          <div className="chat-log">
            {chatMessages.map((msg) => {
              const isBot = msg.sender === 'bot';
              return (
                <div key={msg.id} className={`chat-message ${isBot ? 'bot' : 'user'}`}>
                  <div className={`chat-avatar ${isBot ? 'bot' : 'user'}`}>
                    {isBot ? <Bot size={14} /> : <User size={14} />}
                  </div>
                  <div className={`chat-bubble ${isBot ? 'bot' : 'user'} ${msg.isError ? 'error' : ''}`}>
                    {msg.text}
                  </div>
                </div>
              );
            })}
            <div ref={chatBottomRef} />
          </div>
        </div>
      </div>

      {/* AI Co-pilot Risk Assessment Section (Collapsible Panel docked above Chat Input) */}
      {hasTriage && (
        <section
          className="copilot-risk-card"
          aria-label="AI Co-pilot Risk Assessment"
        >
          {/* Header Bar */}
          <div
            className="copilot-risk-header"
            onClick={() => setIsRiskAssessmentExpanded((prev) => !prev)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setIsRiskAssessmentExpanded((prev) => !prev);
              }
            }}
            title={isRiskAssessmentExpanded ? 'Collapse assessment' : 'Expand assessment'}
          >
            <div className="copilot-risk-header-left">
              <div className="copilot-risk-icon-wrap">
                <ShieldAlert size={16} />
              </div>
              <h3 className="copilot-risk-title">AI Co-pilot Risk Assessment</h3>
            </div>

            <div className="copilot-risk-header-right">
              <div className="risk-classification-group">
                <span className="risk-badge-label">Risk Classification:</span>
                <span className={`risk-pill-badge ${getRiskBadgeClass(currentComplaint.risk_classification)}`}>
                  {currentComplaint.risk_classification || 'Class II'}
                </span>
              </div>
              <button
                type="button"
                className="copilot-risk-toggle-btn"
                aria-label={isRiskAssessmentExpanded ? 'Collapse assessment' : 'Expand assessment'}
                onClick={(e) => {
                  e.stopPropagation();
                  setIsRiskAssessmentExpanded((prev) => !prev);
                }}
              >
                {isRiskAssessmentExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
              </button>
            </div>
          </div>

          {/* Collapsible Content */}
          {isRiskAssessmentExpanded && (
            <div className="copilot-risk-body">
              {/* Recommended Action Block */}
              <div className="risk-field-block">
                <div className="risk-field-label-row">
                  <ClipboardList size={13} className="risk-label-icon" />
                  <span className="risk-field-label">Recommended Action (CAPA / QA Plan)</span>
                </div>
                <div className="risk-scroll-box" tabIndex={0}>
                  {currentComplaint.recommended_action ? (
                    <p className="risk-text-content">{currentComplaint.recommended_action}</p>
                  ) : (
                    <span className="risk-text-placeholder">Awaiting recommended action plan...</span>
                  )}
                </div>
              </div>

              {/* AI Reasoning Notes Block */}
              <div className="risk-field-block">
                <div className="risk-field-label-row">
                  <AlertCircle size={13} className="risk-label-icon" />
                  <span className="risk-field-label">AI Clinical &amp; Regulatory Reasoning</span>
                </div>
                <div className="risk-scroll-box" tabIndex={0}>
                  {currentComplaint.ai_reasoning_notes ? (
                    <p className="risk-text-content">{currentComplaint.ai_reasoning_notes}</p>
                  ) : (
                    <span className="risk-text-placeholder">Awaiting clinical and QA reasoning notes...</span>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Bottom Chat Input & Disclaimer */}
      <footer className="copilot-footer">
        <form
          className="chat-input-row"
          onSubmit={(e) => {
            e.preventDefault();
            handleTextSubmit(bottomInput);
          }}
        >
          <input
            type="text"
            className="chat-text-input"
            placeholder={
              currentComplaint.id
                ? `Provide follow-up corrections for complaint #${currentComplaint.id}...`
                : 'Ask me anything about this complaint...'
            }
            value={bottomInput}
            onChange={(e) => setBottomInput(e.target.value)}
            disabled={isExtracting}
          />
          <button
            type="submit"
            className="btn-send"
            disabled={!bottomInput.trim() || isExtracting}
            title="Send complaint instruction or correction"
          >
            <Send size={15} />
          </button>
        </form>
        <p className="disclaimer-text">AI responses may contain errors. Please verify information.</p>
      </footer>
    </div>
  );
}

export default AICopilotPanel;
