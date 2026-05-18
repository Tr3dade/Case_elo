import React, { useState } from 'react';
import Login from './components/Login';
import AppContent from './components/AppContent';
import { User } from './data/users';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loggedUser, setLoggedUser] = useState<User | null>(null);

  const handleLogin = (user: User) => {
    setLoggedUser(user);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    setLoggedUser(null);
    setIsLoggedIn(false);
  };

  return isLoggedIn && loggedUser ? <AppContent user={loggedUser} onLogout={handleLogout} /> : <Login onLogin={handleLogin} />;
};;

export default App;