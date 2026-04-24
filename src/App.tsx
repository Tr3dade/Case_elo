import React, { useState } from 'react';
import './styles/App.css';
import './styles/Components.css';
import { roles } from './data/roles';
import Topbar from './components/Topbar';
import RoleSelector from './components/RoleSelector';
import NavTabs from './components/NavTabs';
import Content from './components/Content';

const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<string>('colaborador');
  const [currentTab, setCurrentTab] = useState<number>(0);

  const handleRoleChange = (role: string) => {
    setCurrentRole(role);
    setCurrentTab(0);
  };

  const handleTabChange = (tabIndex: number) => {
    setCurrentTab(tabIndex);
  };

  const currentRoleData = roles[currentRole];

  return (
    <div className="app">
      <Topbar roleData={currentRoleData} currentRole={currentRole} onRoleChange={handleRoleChange} />
      <RoleSelector currentRole={currentRole} onRoleChange={handleRoleChange} />
      <NavTabs tabs={currentRoleData.tabs} currentTab={currentTab} onTabChange={handleTabChange} />
      <Content role={currentRole} tab={currentTab} />
    </div>
  );
};

export default App;