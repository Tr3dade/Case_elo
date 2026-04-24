import { Request, Response } from 'express';
import { ReimbursementService } from '../services/reimbursement.service';
import { CreateReimbursementRequest, UpdateReimbursementRequest } from '../types/reimbursement';

const reimbursementService = new ReimbursementService();

export class ReimbursementController {
  async getAll(req: Request, res: Response) {
    try {
      const reimbursements = await reimbursementService.getAll();
      res.json(reimbursements);
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch reimbursements' });
    }
  }

  async getById(req: Request, res: Response) {
    try {
      const { id } = req.params;
      const reimbursement = await reimbursementService.getById(id);
      if (!reimbursement) {
        return res.status(404).json({ error: 'Reimbursement not found' });
      }
      res.json(reimbursement);
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch reimbursement' });
    }
  }

  async create(req: Request, res: Response) {
    try {
      const requestData: CreateReimbursementRequest = req.body;
      const reimbursement = await reimbursementService.create(requestData);
      res.status(201).json(reimbursement);
    } catch (error) {
      res.status(500).json({ error: 'Failed to create reimbursement' });
    }
  }

  async update(req: Request, res: Response) {
    try {
      const { id } = req.params;
      const updates: UpdateReimbursementRequest = req.body;
      const reimbursement = await reimbursementService.update(id, updates);
      res.json(reimbursement);
    } catch (error) {
      res.status(500).json({ error: 'Failed to update reimbursement' });
    }
  }

  async delete(req: Request, res: Response) {
    try {
      const { id } = req.params;
      await reimbursementService.delete(id);
      res.status(204).send();
    } catch (error) {
      res.status(500).json({ error: 'Failed to delete reimbursement' });
    }
  }
}