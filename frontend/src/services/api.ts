import type {
  ReimbursementRequest,
  CreateReimbursementRequest,
  UpdateReimbursementRequest
} from '../types/reimbursement';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

class ApiService {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Reimbursements
  async getReimbursements() {
    return this.request<ReimbursementRequest[]>('/reimbursements');
  }

  async getReimbursement(id: string) {
    return this.request<ReimbursementRequest>(`/reimbursements/${id}`);
  }

  async createReimbursement(data: CreateReimbursementRequest) {
    return this.request<ReimbursementRequest>('/reimbursements', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateReimbursement(id: string, data: UpdateReimbursementRequest) {
    return this.request<ReimbursementRequest>(`/reimbursements/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteReimbursement(id: string) {
    return this.request<void>(`/reimbursements/${id}`, {
      method: 'DELETE',
    });
  }
}

export const api = new ApiService(API_BASE_URL);

// Re-export types for convenience
export type {
  ReimbursementRequest,
  CreateReimbursementRequest,
  UpdateReimbursementRequest,
  ReimbursementItem,
  ActionHistory,
  RequestStatus,
  Project,
  CostCenter
} from '../types/reimbursement';