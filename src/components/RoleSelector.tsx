import React from 'react';

interface RoleSelectorProps {
  currentRole: string;
  onRoleChange: (roleKey: string) => void;
}

const RoleSelector: React.FC<RoleSelectorProps> = ({ currentRole, onRoleChange }) => {
  const roles = [
    { key: 'colaborador', label: 'Colaborador' },
    { key: 'gestor', label: 'Gestor' },
    { key: 'tecnico', label: 'Técnico Administrativo' },
    { key: 'financeiro', label: 'Financeiro' }
  ];

  return (
    <div className="role-selector">
      <span className="role-label">Visualizar como:</span>
      {roles.map(r => (
        <button
          key={r.key}
          className={`role-btn ${currentRole === r.key ? 'active' : ''}`}
          onClick={() => onRoleChange(r.key)}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
};

export default RoleSelector;