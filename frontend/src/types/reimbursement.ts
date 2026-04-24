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

export interface ActionHistory {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  comments?: string;
}

export type RequestStatus = 'Enviado' | 'Em análise' | 'Aprovado' | 'Rejeitado' | 'Aguardando ajustes' | 'Pago';

export interface ReimbursementRequest {
  id: string;
  createdAt: string;
  requestedBy: string;
  month: string;
  items: ReimbursementItem[];
  attachments: string[];
  status: RequestStatus;
  costCenterIds: number[];
  notifications?: string[];
  total: number;
  history: ActionHistory[];
  paymentDate?: string;
  archivedAttachments?: string[];
}

export interface CreateReimbursementRequest {
  requestedBy: string;
  month: string;
  items: Omit<ReimbursementItem, 'id' | 'status' | 'rejectionReason'>[];
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

export interface Project {
  id: string;
  name: string;
  costCenterId: number;
}

export interface CostCenter {
  id: number;
  code: string;
  name: string;
  manager: string;
}