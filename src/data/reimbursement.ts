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
  status?: 'Aprovado' | 'Rejeitado' | 'Pendente' | 'Pago' | 'Em análise' | 'Aguardando ajustes';
  rejectionReason?: string;
}

export type RequestStatus = 'Enviado' | 'Em análise' | 'Aguardando ajustes' | 'Aprovado' | 'Rejeitado' | 'Pago' | 'Rascunho';

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
  },
  {
    id: '2024-020',
    createdAt: '10/03/2026',
    requestedBy: 'João Silva',
    month: '2026-03',
    items: [
      {
        id: 'item-4',
        date: '2026-03-08',
        type: 'Transporte',
        description: 'Taxi para visita técnica',
        projectId: 'gamma',
        costCenterId: 5102,
        amount: 89.50,
        status: 'Pago'
      }
    ],
    attachments: ['recibo_taxi.pdf'],
    status: 'Pago',
    costCenterIds: [5102],
    notifications: [],
    total: 89.50,
    history: [
      {
        id: 'hist-5',
        timestamp: '10/03/2026 11:00',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-6',
        timestamp: '12/03/2026 09:15',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-7',
        timestamp: '13/03/2026 14:20',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      },
      {
        id: 'hist-8',
        timestamp: '15/03/2026 10:00',
        actor: 'Roberto Almeida',
        action: 'Pagamento processado'
      }
    ],
    paymentDate: '15/03/2026'
  },
  {
    id: '2024-021',
    createdAt: '05/02/2026',
    requestedBy: 'João Silva',
    month: '2026-02',
    items: [
      {
        id: 'item-5',
        date: '2026-02-03',
        type: 'Refeição',
        description: 'Jantar com cliente potencial',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 120.00,
        status: 'Rejeitado'
      }
    ],
    attachments: ['nota_restaurante.pdf'],
    status: 'Rejeitado',
    costCenterIds: [4521],
    notifications: [],
    total: 120.00,
    history: [
      {
        id: 'hist-9',
        timestamp: '05/02/2026 18:30',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-10',
        timestamp: '07/02/2026 10:45',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-11',
        timestamp: '08/02/2026 16:00',
        actor: 'Paulo Lima',
        action: 'Rejeitado pelo gestor',
        comments: 'Valor acima do limite permitido para refeições'
      }
    ]
  },
  {
    id: '2024-022',
    createdAt: '20/01/2026',
    requestedBy: 'João Silva',
    month: '2026-01',
    items: [
      {
        id: 'item-6',
        date: '2026-01-18',
        type: 'Gráfica',
        description: 'Impressão de folders promocionais',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 450.00,
        status: 'Aguardando ajustes'
      }
    ],
    attachments: ['orcamento_grafica.pdf'],
    status: 'Aguardando ajustes',
    costCenterIds: [3308],
    notifications: [],
    total: 450.00,
    history: [
      {
        id: 'hist-12',
        timestamp: '20/01/2026 14:00',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-13',
        timestamp: '22/01/2026 11:20',
        actor: 'Fernanda Souza',
        action: 'Solicitado ajustes ao colaborador',
        comments: 'Falta comprovante fiscal da gráfica'
      }
    ]
  },
  {
    id: '2024-023',
    createdAt: '12/12/2025',
    requestedBy: 'João Silva',
    month: '2025-12',
    items: [
      {
        id: 'item-7',
        date: '2025-12-10',
        type: 'Transporte',
        description: 'Passagem aérea para conferência',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 850.00,
        status: 'Aprovado'
      }
    ],
    attachments: ['bilhete_aviao.pdf'],
    status: 'Aprovado',
    costCenterIds: [4521],
    notifications: [],
    total: 850.00,
    history: [
      {
        id: 'hist-14',
        timestamp: '12/12/2025 09:45',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-15',
        timestamp: '14/12/2025 13:30',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-16',
        timestamp: '15/12/2025 10:15',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      }
    ]
  },
  {
    id: '2024-024',
    createdAt: '08/11/2025',
    requestedBy: 'João Silva',
    month: '2025-11',
    items: [
      {
        id: 'item-8',
        date: '2025-11-05',
        type: 'Outros',
        description: 'Software de edição de vídeo',
        projectId: 'gamma',
        costCenterId: 5102,
        amount: 299.99,
        status: 'Em análise'
      }
    ],
    attachments: ['nota_software.pdf'],
    status: 'Em análise',
    costCenterIds: [5102],
    notifications: [
      'Gestor Paulo Lima notificado para centro de custo 5102'
    ],
    total: 299.99,
    history: [
      {
        id: 'hist-17',
        timestamp: '08/11/2025 16:20',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      }
    ]
  },
  {
    id: '2024-025',
    createdAt: '25/10/2025',
    requestedBy: 'João Silva',
    month: '2025-10',
    items: [
      {
        id: 'item-9',
        date: '2025-10-22',
        type: 'Alimentação',
        description: 'Coffee break em reunião',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 75.00,
        status: 'Pago'
      },
      {
        id: 'item-10',
        date: '2025-10-23',
        type: 'Transporte',
        description: 'Estacionamento',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 15.00,
        status: 'Pago'
      }
    ],
    attachments: ['recibos_coffee.pdf'],
    status: 'Pago',
    costCenterIds: [3308],
    notifications: [],
    total: 90.00,
    history: [
      {
        id: 'hist-18',
        timestamp: '25/10/2025 12:00',
        actor: 'João Silva',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-19',
        timestamp: '27/10/2025 09:30',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-20',
        timestamp: '28/10/2025 14:45',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      },
      {
        id: 'hist-21',
        timestamp: '30/10/2025 11:00',
        actor: 'Roberto Almeida',
        action: 'Pagamento processado'
      }
    ],
    paymentDate: '30/10/2025'
  },
  // Solicitações de Maria Costa
  {
    id: '2024-026',
    createdAt: '10/04/2026',
    requestedBy: 'Maria Costa',
    month: '2026-04',
    items: [
      {
        id: 'item-11',
        date: '2026-04-08',
        type: 'Transporte',
        description: 'Taxi para visita técnica',
        projectId: 'gamma',
        costCenterId: 5102,
        amount: 120.00,
        status: 'Aprovado'
      }
    ],
    attachments: ['recibo_taxi_maria.pdf'],
    status: 'Aprovado',
    costCenterIds: [5102],
    notifications: [],
    total: 120.00,
    history: [
      {
        id: 'hist-22',
        timestamp: '10/04/2026 14:30',
        actor: 'Maria Costa',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-23',
        timestamp: '12/04/2026 10:15',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-24',
        timestamp: '13/04/2026 16:45',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      }
    ],
    paymentDate: '18/04/2026'
  },
  {
    id: '2024-027',
    createdAt: '25/03/2026',
    requestedBy: 'Maria Costa',
    month: '2026-03',
    items: [
      {
        id: 'item-12',
        date: '2026-03-20',
        type: 'Alimentação',
        description: 'Jantar com equipe',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 85.00,
        status: 'Em análise'
      }
    ],
    attachments: ['nota_jantar.pdf'],
    status: 'Em análise',
    costCenterIds: [3308],
    notifications: [
      'Gestor Paulo Lima notificado para centro de custo 3308'
    ],
    total: 85.00,
    history: [
      {
        id: 'hist-25',
        timestamp: '25/03/2026 19:00',
        actor: 'Maria Costa',
        action: 'Solicitação enviada'
      }
    ]
  },
  // Solicitações de Carlos Santos
  {
    id: '2024-028',
    createdAt: '05/04/2026',
    requestedBy: 'Carlos Santos',
    month: '2026-04',
    items: [
      {
        id: 'item-13',
        date: '2026-04-03',
        type: 'Material',
        description: 'Papelaria para escritório',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 67.50,
        status: 'Pago'
      },
      {
        id: 'item-14',
        date: '2026-04-04',
        type: 'Transporte',
        description: 'Ônibus intermunicipal',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 45.00,
        status: 'Pago'
      }
    ],
    attachments: ['recibos_carlos.pdf'],
    status: 'Pago',
    costCenterIds: [4521],
    notifications: [],
    total: 112.50,
    history: [
      {
        id: 'hist-26',
        timestamp: '05/04/2026 11:20',
        actor: 'Carlos Santos',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-27',
        timestamp: '07/04/2026 09:45',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-28',
        timestamp: '08/04/2026 14:30',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      },
      {
        id: 'hist-29',
        timestamp: '12/04/2026 10:00',
        actor: 'Roberto Almeida',
        action: 'Pagamento processado'
      }
    ],
    paymentDate: '12/04/2026'
  },
  {
    id: '2024-029',
    createdAt: '15/02/2026',
    requestedBy: 'Carlos Santos',
    month: '2026-02',
    items: [
      {
        id: 'item-15',
        date: '2026-02-12',
        type: 'Refeição',
        description: 'Almoço de trabalho',
        projectId: 'beta',
        costCenterId: 3308,
        amount: 32.00,
        status: 'Rejeitado'
      }
    ],
    attachments: ['nota_restaurante_carlos.pdf'],
    status: 'Rejeitado',
    costCenterIds: [3308],
    notifications: [],
    total: 32.00,
    history: [
      {
        id: 'hist-30',
        timestamp: '15/02/2026 13:30',
        actor: 'Carlos Santos',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-31',
        timestamp: '17/02/2026 11:15',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-32',
        timestamp: '18/02/2026 15:20',
        actor: 'Paulo Lima',
        action: 'Rejeitado pelo gestor',
        comments: 'Valor abaixo do limite mínimo para reembolso'
      }
    ]
  },
  // Solicitações de Ana Oliveira
  {
    id: '2024-030',
    createdAt: '20/04/2026',
    requestedBy: 'Ana Oliveira',
    month: '2026-04',
    items: [
      {
        id: 'item-16',
        date: '2026-04-18',
        type: 'Transporte',
        description: 'Uber para reunião externa',
        projectId: 'alpha',
        costCenterId: 4521,
        amount: 78.50,
        status: 'Aguardando ajustes'
      }
    ],
    attachments: ['comprovante_uber_ana.pdf'],
    status: 'Aguardando ajustes',
    costCenterIds: [4521],
    notifications: [],
    total: 78.50,
    history: [
      {
        id: 'hist-33',
        timestamp: '20/04/2026 16:45',
        actor: 'Ana Oliveira',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-34',
        timestamp: '22/04/2026 10:30',
        actor: 'Fernanda Souza',
        action: 'Solicitado ajustes ao colaborador',
        comments: 'Falta especificar o motivo da viagem'
      }
    ]
  },
  {
    id: '2024-031',
    createdAt: '08/03/2026',
    requestedBy: 'Ana Oliveira',
    month: '2026-03',
    items: [
      {
        id: 'item-17',
        date: '2026-03-05',
        type: 'Gráfica',
        description: 'Impressão de apresentações',
        projectId: 'gamma',
        costCenterId: 5102,
        amount: 150.00,
        status: 'Aprovado'
      }
    ],
    attachments: ['orcamento_grafica_ana.pdf'],
    status: 'Aprovado',
    costCenterIds: [5102],
    notifications: [],
    total: 150.00,
    history: [
      {
        id: 'hist-35',
        timestamp: '08/03/2026 14:15',
        actor: 'Ana Oliveira',
        action: 'Solicitação enviada'
      },
      {
        id: 'hist-36',
        timestamp: '10/03/2026 11:45',
        actor: 'Fernanda Souza',
        action: 'Validado pelo técnico administrativo'
      },
      {
        id: 'hist-37',
        timestamp: '11/03/2026 16:20',
        actor: 'Paulo Lima',
        action: 'Aprovado pelo gestor'
      }
    ]
  }
];
