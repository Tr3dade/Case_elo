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
  status?: 'Aprovado' | 'Rejeitado' | 'Pendente';
  rejectionReason?: string;
}

export type RequestStatus = 'Enviado' | 'Em análise' | 'Aguardando ajustes' | 'Aprovado' | 'Rejeitado' | 'Pago';

export interface ActionHistory {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  comments?: string;
  itemChanges?: { itemId: string; status: string; reason?: string }[];
}

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
  history: ActionHistory[];
  paymentDate?: string;
  archivedAttachments?: string[];
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
  { id: 4521, code: '4521', projectId: 'alpha', manager: 'Paulo Lima', managerEmail: 'paulo.lima@empresa.com' },
  { id: 3308, code: '3308', projectId: 'beta', manager: 'Paulo Lima', managerEmail: 'paulo.lima@empresa.com' },
  { id: 5102, code: '5102', projectId: 'gamma', manager: 'Fernanda Souza', managerEmail: 'fernanda.souza@empresa.com' }
];

export const defaultReimbursementConfig = {
  attachmentsRequired: false,
  allowedMimeTypes: ['application/pdf', 'image/jpeg', 'image/png']
};

export const sampleRequests: ReimbursementRequest[] = [
  {
    id: '2024-018',
    createdAt: '15/04/2026',
    requestedBy: 'João Silva',
    month: '2026-04',
    items: [
      {
        id: 'item-1',
        date: '2026-04-15',
        type: 'Transporte',
        description: 'Uber para reunião com cliente',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 156.0,
        status: 'Pendente'
      },
      {
        id: 'item-2',
        date: '2026-01-15',
        type: 'Alimentação',
        description: 'Almoço de trabalho',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 45.0,
        status: 'Pendente'
      }
    ],
    attachments: ['comprovante_uber.pdf'],
    status: 'Em análise',
    costCenterIds: [4521, 3308],
    notifications: [
      'Gestor Paulo Lima notificado para centro de custo 4521',
      'Financeiro notificado para revisão financeira'
    ],
    total: 201.0,
    history: [
      {
        id: 'hist-1',
        timestamp: '15/04/2026 10:30',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      }
    ]
  },
  {
    id: '2024-019',
    createdAt: '16/04/2026',
    requestedBy: 'João Silva',
    month: '2026-04',
    items: [
      {
        id: 'item-3',
        date: '2026-04-10',
        type: 'Material',
        description: 'Canetas para escritório',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 25.0,
        status: 'Aprovado'
      }
    ],
    attachments: ['nota_fiscal_canetas.pdf'],
    status: 'Aprovado',
    costCenterIds: [4521],
    notifications: [],
    total: 25.0,
    history: [
      {
        id: 'hist-2',
        timestamp: '16/04/2026 09:00',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-3',
        timestamp: '16/04/2026 14:00',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-4',
        timestamp: '16/04/2026 15:30',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      }
    ],
    paymentDate: '20/04/2026'
  }
];
