import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './index.css';
import { SensorProvider } from './context/SensorContext';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <SensorProvider>
      <App />
    </SensorProvider>
  </React.StrictMode>
);
