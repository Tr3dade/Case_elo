export interface Role {
  name: string;
  initials: string;
  label: string;
  tabs: string[];
}

export const roles: Record<string, Role> = {
  colaborador: {
    name: 'João Martins',
    initials: 'JM',
    label: 'Colaborador',
    tabs: ['Minhas Solicitações', 'Nova Solicitação', 'Acompanhar']
  },
  gestor: {
    name: 'Ana Lima',
    initials: 'AL',
    label: 'Gestora de Projetos',
    tabs: ['Pendentes de Aprovação', 'Aprovados', 'Rejeitados']
  },
  tecnico: {
    name: 'Carlos Souza',
    initials: 'CS',
    label: 'Técnico Administrativo',
    tabs: ['Validar Conformidade', 'Em Andamento', 'Histórico']
  },
  financeiro: {
    name: 'Maria Costa',
    initials: 'MC',
    label: 'Financeiro',
    tabs: ['Aguardando Pagamento', 'Pagamentos Realizados']
  }
};