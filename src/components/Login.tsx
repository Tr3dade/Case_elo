import { useState } from 'react';
import '../styles/Login.css';
import { users, User } from '../data/users';

interface LoginProps {
  onLogin: (user: User) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('bob');
  const [password, setPassword] = useState('');
  const [keepLogged, setKeepLogged] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const user = users.find(u => u.username === username && u.password === password);
    if (user) {
      onLogin(user);
    } else {
      setError('Usuário ou senha inválidos');
    }
  };

  return (
    <div className="login-page">
      <div className="login-side login-side--brand">
        <img src="/elogroup-scaled.png" alt="EloGroup" className="brand-image" />
      </div>

      <div className="login-side login-side--form">
        <div className="login-card">
          <div className="login-header">
            <h1>Entrar</h1>
            <p className="login-description">
              Digite seu usuário e senha para acessar a aplicação.
            </p>
          </div>

          <form className="login-form" onSubmit={handleSubmit}>
            {error && <div className="error-message">{error}</div>}
            <label className="login-label">
              Seu usuário
              <input
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className="login-input"
                placeholder="Digite seu usuário"
              />
            </label>

            <label className="login-label">
              Sua senha
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="login-input"
                placeholder="••••••••••"
              />
            </label>

            <div className="login-row login-row--space">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={keepLogged}
                  onChange={(event) => setKeepLogged(event.target.checked)}
                />
                Manter-me conectado
              </label>
              <button type="button" className="link-button">
                Esqueceu a senha?
              </button>
            </div>

            <button type="submit" className="login-button">
              ENTRAR
            </button>
          </form>

          <div className="login-footer">
            <button type="button" className="footer-link">
              Privacidade
            </button>
            <button type="button" className="footer-link">
              Termos
            </button>
            <button type="button" className="footer-link">
              Sobre
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
