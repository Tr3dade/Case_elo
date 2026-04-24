import React from 'react';
import { Role } from '../data/roles';

interface TopbarProps {
  roleData: Role;
}

const Topbar: React.FC<TopbarProps> = ({ roleData }) => {
  return (
    <div className="topbar">
      <div className="topbar-logo">
        <div className="logo-dot"></div>
        ReembolsaApp
      </div>
      <div className="topbar-user">
        <div className="avatar">{roleData.initials}</div>
        <div>
          <div className="user-name">{roleData.name}</div>
          <div className="role-badge">{roleData.label}</div>
        </div>
      </div>
    </div>
  );
};

export default Topbar;