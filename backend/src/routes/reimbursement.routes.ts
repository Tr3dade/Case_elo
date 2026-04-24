import { Router } from 'express';
import { ReimbursementController } from '../controllers/reimbursement.controller';

const router = Router();
const reimbursementController = new ReimbursementController();

router.get('/', reimbursementController.getAll.bind(reimbursementController));
router.get('/:id', reimbursementController.getById.bind(reimbursementController));
router.post('/', reimbursementController.create.bind(reimbursementController));
router.put('/:id', reimbursementController.update.bind(reimbursementController));
router.delete('/:id', reimbursementController.delete.bind(reimbursementController));

export default router;