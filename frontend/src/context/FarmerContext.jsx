import { createContext, useContext, useState, useCallback } from 'react';

const FarmerContext = createContext(null);

export function FarmerProvider({ children }) {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(false);
  return (
    <FarmerContext.Provider value={{ dashboard, setDashboard, loading, setLoading }}>
      {children}
    </FarmerContext.Provider>
  );
}

export function useFarmer() {
  return useContext(FarmerContext) || { dashboard: null, setDashboard: () => {}, loading: false, setLoading: () => {} };
}
