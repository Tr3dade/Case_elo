import React, { useState, useEffect, useRef } from 'react';
import { Role, roles } from '../data/roles';

interface TopbarProps {
  roleData: Role;
  currentRole: string;
  onRoleChange: (role: string) => void;
  userName: string;
  onLogout: () => void;
}

const Topbar: React.FC<TopbarProps> = ({ roleData, currentRole, onRoleChange, userName, onLogout }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSubmenuOpen, setIsSubmenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const getInitials = (name: string) => {
    return name.split(' ').map(word => word.charAt(0)).join('').toUpperCase();
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
        setIsSubmenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="topbar">
      <div className="topbar-logo">
        <img src="/elo_logo.png" alt="ELO Group" style={{ height: '32px', marginRight: '12px' }} />
        GERENCIAMENTO DE REEMBOLSOS
      </div>
      <div className="topbar-user" onClick={() => setIsDropdownOpen(!isDropdownOpen)} style={{ cursor: 'pointer' }}>
        <div className="avatar">{getInitials(userName)}</div>
        <div>
          <div className="user-name">{userName}</div>
          <div className="role-badge">{roleData.label}</div>
        </div>
        {isDropdownOpen && (
          <div className="dropdown-menu" ref={dropdownRef}>
            <div className="dropdown-item">Opções</div>
            <div className="dropdown-item" onClick={(e) => { e.stopPropagation(); setIsSubmenuOpen(!isSubmenuOpen); }}>Gerenciar cargo</div>
            {isSubmenuOpen && (
              <div className="submenu">
                {Object.keys(roles).map(roleKey => (
                  <div key={roleKey} className={`submenu-item ${roleKey === currentRole ? 'active' : ''}`} onClick={() => { onRoleChange(roleKey); setIsDropdownOpen(false); setIsSubmenuOpen(false); }}>
                    {roles[roleKey].label}
                  </div>
                ))}
              </div>
            )}
            <div className="dropdown-item" onClick={() => { setIsDropdownOpen(false); onLogout(); }} style={{ cursor: 'pointer', color: '#FF6B6B', fontWeight: '500' }}>Sair</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Topbar;