import React, { useState } from 'react';
import '../styles/App.css';
import '../styles/Components.css';
import { roles } from '../data/roles';
import Topbar from './Topbar';
import RoleSelector from './RoleSelector';
import NavTabs from './NavTabs';
import Content from './Content';
import { User } from '../data/users';

interface AppContentProps {
  user: User;
}

const AppContent: React.FC<AppContentProps> = ({ user }) => {
  const [currentRole, setCurrentRole] = useState<string>(user.role);
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
      <Topbar roleData={currentRoleData} currentRole={currentRole} onRoleChange={handleRoleChange} userName={user.name} />
      <RoleSelector currentRole={currentRole} onRoleChange={handleRoleChange} />
      <NavTabs tabs={currentRoleData.tabs} currentTab={currentTab} onTabChange={handleTabChange} />
      <Content role={currentRole} tab={currentTab} />
    </div>
  );
};

export default AppContent;
