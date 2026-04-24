import { supabase } from './supabase';
import { ReimbursementRequest, CreateReimbursementRequest, UpdateReimbursementRequest } from '../types/reimbursement';

export class ReimbursementService {
  async getAll(): Promise<ReimbursementRequest[]> {
    const { data, error } = await supabase
      .from('reimbursements')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) throw error;
    return data || [];
  }

  async getById(id: string): Promise<ReimbursementRequest | null> {
    const { data, error } = await supabase
      .from('reimbursements')
      .select('*')
      .eq('id', id)
      .single();

    if (error) throw error;
    return data;
  }

  async create(request: CreateReimbursementRequest): Promise<ReimbursementRequest> {
    const newRequest = {
      ...request,
      id: `REQ-${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: 'Enviado' as const,
      notifications: [],
      total: request.items.reduce((sum, item) => sum + item.amount, 0),
      history: [{
        id: `hist-${Date.now()}`,
        timestamp: new Date().toISOString(),
        actor: request.requestedBy,
        action: 'Solicitação enviada'
      }]
    };

    const { data, error } = await supabase
      .from('reimbursements')
      .insert(newRequest)
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async update(id: string, updates: UpdateReimbursementRequest): Promise<ReimbursementRequest> {
    const { data, error } = await supabase
      .from('reimbursements')
      .update(updates)
      .eq('id', id)
      .select()
      .single();

    if (error) throw error;
    return data;
  }

  async delete(id: string): Promise<void> {
    const { error } = await supabase
      .from('reimbursements')
      .delete()
      .eq('id', id);

    if (error) throw error;
  }
}