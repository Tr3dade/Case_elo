import React, { useState } from 'react';
import '../styles/App.css';
import '../styles/Components.css';
import { roles } from '../data/roles';
import Topbar from './Topbar';
import RoleSelector from './RoleSelector';
import NavTabs from './NavTabs';
import Content from './Content';

const AppContent: React.FC = () => {
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

export default AppContent;
