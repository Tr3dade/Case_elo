import React, { useState, useEffect, useRef } from 'react';
import { Role, roles } from '../data/roles';

interface TopbarProps {
  roleData: Role;
  currentRole: string;
  onRoleChange: (role: string) => void;
}

const Topbar: React.FC<TopbarProps> = ({ roleData, currentRole, onRoleChange }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isSubmenuOpen, setIsSubmenuOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

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
        <div className="logo-dot"></div>
        ReembolsaApp
      </div>
      <div className="topbar-user" onClick={() => setIsDropdownOpen(!isDropdownOpen)} style={{ cursor: 'pointer' }}>
        <div className="avatar">{roleData.initials}</div>
        <div>
          <div className="user-name">{roleData.name}</div>
          <div className="role-badge">{roleData.label}</div>
        </div>
        {isDropdownOpen && (
          <div className="dropdown-menu" ref={dropdownRef}>
            <div className="dropdown-item disabled">Sair</div>
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
          </div>
        )}
      </div>
    </div>
  );
};

export default Topbar;