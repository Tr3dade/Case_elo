export interface Role {
  label: string;
  tabs: string[];
}

export const roles: Record<string, Role> = {
  colaborador: {
    label: 'Colaborador',
    tabs: ['Minhas Solicitações', 'Nova Solicitação', 'Acompanhar']
  },
  gestor: {
    label: 'Gestora de Projetos',
    tabs: ['Pendentes de Aprovação', 'Aprovados', 'Rejeitados']
  },
  tecnico: {
    label: 'Técnico Administrativo',
    tabs: ['Validar Conformidade', 'Em Andamento', 'Histórico']
  },
  financeiro: {
    label: 'Financeiro',
    tabs: ['Aguardando Pagamento', 'Pagamentos Realizados']
  },
  admin: {
    label: 'Administrador',
    tabs: ['Gerenciar Usuários', 'Relatórios', 'Configurações']
  }
};