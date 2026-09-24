import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { installHistoryActivityTracker } from './lib/activityTracker';

installHistoryActivityTracker();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    {/* IMPORTANT: AuthProvider MUST wrap App here */}
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
