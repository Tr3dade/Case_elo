export interface CostCenter {
  id: number;
  code: string;
  projectId: string;
  manager: string;
  managerEmail: string;
}

export interface Project {
  id: string;
  name: string;
  costCenterId: number;
}

export interface ReimbursementItem {
  id: string;
  date: string;
  type: string;
  description: string;
  projectId: string;
  costCenterId: number;
  amount: number;
}

export type RequestStatus = 'Enviado' | 'Em análise' | 'Aprovado' | 'Recusado';

export interface ReimbursementRequest {
  id: string;
  createdAt: string;
  requestedBy: string;
  month: string;
  items: ReimbursementItem[];
  attachments: string[];
  status: RequestStatus;
  costCenterIds: number[];
  notifications: string[];
  total: number;
}

export const financeAdmin = {
  name: 'Financeiro',
  email: 'financeiro@empresa.com'
};

export const projects: Project[] = [
  { id: 'alpha', name: 'Projeto Alpha', costCenterId: 4521 },
  { id: 'beta', name: 'Projeto Beta', costCenterId: 3308 },
  { id: 'gamma', name: 'Projeto Gamma', costCenterId: 5102 }
];

export const costCenters: CostCenter[] = [
  { id: 4521, code: '4521', projectId: 'alpha', manager: 'Ana Lima', managerEmail: 'ana.lima@empresa.com' },
  { id: 3308, code: '3308', projectId: 'beta', manager: 'Ana Lima', managerEmail: 'ana.lima@empresa.com' },
  { id: 5102, code: '5102', projectId: 'gamma', manager: 'Carlos Souza', managerEmail: 'carlos.souza@empresa.com' }
];

export const defaultReimbursementConfig = {
  attachmentsRequired: false,
  allowedMimeTypes: ['application/pdf', 'image/jpeg', 'image/png']
};

export const sampleRequests: ReimbursementRequest[] = [
  {
    id: '2024-018',
    createdAt: '15/04/2026',
    requestedBy: 'João Martins',
    month: '2026-04',
    items: [
      {
        id: 'item-1',
        date: '2026-04-15',
        type: 'Transporte',
        description: 'Uber para reunião com cliente',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 156.0
      },
      {
        id: 'item-2',
        date: '2026-01-15', // Data antiga para testar validação de 90 dias
        type: 'Alimentação',
        description: 'Almoço de trabalho',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 45.0
      }
    ],
    attachments: ['comprovante_uber.pdf'],
    status: 'Em análise',
    costCenterIds: [4521, 3308],
    notifications: [
      'Gestor Ana Lima notificado para centro de custo 4521',
      'Financeiro notificado para revisão financeira'
    ],
    total: 201.0
  }
];
