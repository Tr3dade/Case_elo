import React from 'react';
import ColaboradorPages from './pages/ColaboradorPages';
import GestorPages from './pages/GestorPages';
import TecnicoPages from './pages/TecnicoPages';
import FinanceiroPages from './pages/FinanceiroPages';
import { User } from '../data/users';

interface ContentProps {
  role: string;
  tab: number;
  user: User;
  onTabChange?: (tabIndex: number) => void;
}

const Content: React.FC<ContentProps> = ({ role, tab, user, onTabChange = () => {} }) => {
  const renderContent = () => {
    switch (role) {
      case 'colaborador':
        return <ColaboradorPages tab={tab} user={user} onTabChange={onTabChange} />;
      case 'gestor':
        return <GestorPages tab={tab} />;
      case 'tecnico':
        return <TecnicoPages tab={tab} />;
      case 'financeiro':
        return <FinanceiroPages tab={tab} />;
      default:
        return <div>Página não encontrada</div>;
    }
  };

  return (
    <div className="content">
      {renderContent()}
    </div>
  );
};

export default Content;