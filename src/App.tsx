import React, { useState } from 'react';
import Login from './components/Login';
import AppContent from './components/AppContent';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  return isLoggedIn ? <AppContent /> : <Login onLogin={handleLogin} />;
};

export default App;