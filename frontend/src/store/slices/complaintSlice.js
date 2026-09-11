import { createSlice } from '@reduxjs/toolkit';

const initialComplaintState = {
  id: null,
  complaint_source: null,
  customer_name: null,
  product_name: null,
  product_strength_grade: null,
  batch_lot_number: null,
  manufacturing_date: null,
  expiry_date: null,
  quantity_affected: null,
  quantity_unit: null,
  complaint_type: null,
  complaint_date: null,
  detailed_description: null,
  initial_severity: null,
  priority: null,
  risk_classification: null,
  recommended_action: null,
  ai_reasoning_notes: null,
  created_at: null,
  updated_at: null,
};

const initialState = {
  currentComplaint: { ...initialComplaintState },
  activeModule: 'API_QA', // 'API_QA' or 'FDF_QA'
  systemStatus: 'ready',
  history: [],
};

export const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    setComplaint: (state, action) => {
      state.currentComplaint = {
        ...initialComplaintState,
        ...action.payload,
      };
    },
    updateComplaintField: (state, action) => {
      const { field, value } = action.payload;
      if (field in state.currentComplaint) {
        state.currentComplaint[field] = value;
      }
    },
    resetComplaint: (state) => {
      state.currentComplaint = { ...initialComplaintState };
    },
    setActiveModule: (state, action) => {
      state.activeModule = action.payload;
    },
    setSystemStatus: (state, action) => {
      state.systemStatus = action.payload;
    },
  },
});

export const {
  setComplaint,
  updateComplaintField,
  resetComplaint,
  setActiveModule,
  setSystemStatus,
} = complaintSlice.actions;

export default complaintSlice.reducer;
