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

export interface CreateReimbursementRequest {
  requestedBy: string;
  month: string;
  items: Omit<ReimbursementItem, 'id' | 'status'>[];
  attachments: string[];
  costCenterIds: number[];
}

export interface UpdateReimbursementRequest {
  status?: RequestStatus;
  items?: ReimbursementItem[];
  history?: ActionHistory[];
  paymentDate?: string;
  archivedAttachments?: string[];
}