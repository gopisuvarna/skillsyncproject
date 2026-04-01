'use client';

// Context to store the results of the resume upload and processing, including extracted skills and recommended roles.
import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

// Types for the recommended roles that are generated based on the uploaded resume.
export interface RecommendedRole {
  role: string;
  description: string;
  skills: string;
  score: number;
}
// Types for the overall upload result, including all extracted skills and the recommended roles.
export interface UploadResult {
  all_skills: string[];
  rule_based_skills: string[];
  llm_skills: string[];
  recommended_roles: RecommendedRole[];
}

// Context value type, including the current upload result and functions to set or clear it.

interface UploadResultContextValue {

  // The current result of the resume upload and processing, or null if no upload has been done yet.

  uploadResult: UploadResult | null;

  // Function to update the upload result in the context. Accepts a new UploadResult or null to clear it.

  setUploadResult: (result: UploadResult | null) => void;

  // Function to clear the current upload result, setting it back to null.

  clearUploadResult: () => void;
}

//creating global data container that any component can read from and write to.
const UploadResultContext = createContext<UploadResultContextValue | null>(null);

// Provider component that wraps the application and provides the upload result context to its children.
export function UploadResultProvider({ children }: { children: ReactNode }) {
// actual storage for the upload result, initialized to null (no result). The state will be updated when a resume is uploaded and processed.
  const [uploadResult, setUploadResultState] = useState<UploadResult | null>(null);
// Function to update the upload result in the state, wrapped in useCallback for performance optimization.
  const setUploadResult = useCallback((result: UploadResult | null) => {
    setUploadResultState(result);
  }, []);
// Function to clear the upload result, setting it back to null, also wrapped in useCallback.
  const clearUploadResult = useCallback(() => setUploadResultState(null), []);

  // The provider component makes the upload result and the functions to update it available to all child components that consume this context.
  return (
    <UploadResultContext.Provider
      value={{ uploadResult, setUploadResult, clearUploadResult }}
    >
      {children}
    </UploadResultContext.Provider>
  );
}

// Custom hook to access the upload result context. It ensures that the hook is used within a provider and returns the context value.
export function useUploadResult() {
  // Access the context value using useContext. If the context is not available (i.e., the hook is used outside of a provider), it throws an error to alert the developer.
  const ctx = useContext(UploadResultContext);
  if (!ctx) throw new Error('useUploadResult must be used within UploadResultProvider');
  // If the context is available, it returns the context value, which includes the current upload result and the functions to update or clear it.
  return ctx;
}