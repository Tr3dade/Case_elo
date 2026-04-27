import React, { useState } from 'react';
import { sampleRequests, ReimbursementRequest } from '../../data/reimbursement';

interface FinanceiroPagesProps {
  tab: number;
}

const FinanceiroPages: React.FC<FinanceiroPagesProps> = ({ tab }) => {
  const [paymentDate, setPaymentDate] = useState('');
  const [selectedRequest, setSelectedRequest] = useState<ReimbursementRequest | null>(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);

  const getPendingPayments = () => {
    return sampleRequests.filter(req => req.status === 'Aprovado' && !req.paymentDate);
  };

  const getPaidRequests = () => {
    return sampleRequests.filter(req => req.status === 'Pago');
  };

  const handleSchedulePayment = (request: ReimbursementRequest) => {
    setSelectedRequest(request);
    setShowScheduleModal(true);
    setPaymentDate(new Date().toISOString().split('T')[0]); // Today
  };

  const handleConfirmPayment = () => {
    if (!selectedRequest || !paymentDate) return;

    selectedRequest.paymentDate = paymentDate;
    selectedRequest.status = 'Pago';
    selectedRequest.archivedAttachments = [...selectedRequest.attachments];

    setShowScheduleModal(false);
    setSelectedRequest(null);
  };

  if (tab === 0) {
    const pendingPayments = getPendingPayments();

    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Aguardando Pagamento</div>
        <div className="section-sub">Solicitações aprovadas pelo gestor e validadas pelo técnico administrativo</div>
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-label">Total a pagar</div>
            <div className="stat-val blue">R$ {pendingPayments.reduce((sum, req) => sum + req.total, 0).toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Solicitações</div>
            <div className="stat-val amber">{pendingPayments.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Colaboradores</div>
            <div className="stat-val">{new Set(pendingPayments.map(req => req.requestedBy)).size}</div>
          </div>
        </div>

        {pendingPayments.length === 0 ? (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Nenhuma solicitação aguardando pagamento
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Nº</th>
                    <th>Colaborador</th>
                    <th>Gestor aprovador</th>
                    <th>Valor</th>
                    <th>Aprovado em</th>
                    <th>Ação</th>
                </tr>
                </thead>
                <tbody>
                  {pendingPayments.map(request => {
                    const lastApproval = request.history
                      .filter(h => h.action.includes('Aprovado') || h.action.includes('aprovado'))
                      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];

                    return (
                      <tr key={request.id}>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#{request.id}</td>
                        <td>
                          <div style={{ fontWeight: '500' }}>{request.requestedBy}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>joao.martins@empresa.com</div>
                        </td>
                        <td>Paulo Lima</td>
                        <td style={{ fontWeight: '500', color: 'var(--color-accent-cyan)' }}>R$ {request.total.toFixed(2)}</td>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                          {lastApproval ? lastApproval.timestamp.split(' ')[0] : request.createdAt}
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button className="btn btn-sm btn-primary" onClick={() => handleSchedulePayment(request)}>
                              Agendar pgto.
                            </button>
                            <button className="btn btn-sm">Ver comprov.</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {showScheduleModal && selectedRequest && (
          <div className="modal-overlay" onClick={() => setShowScheduleModal(false)}>
            <div className="modal-content" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
              <div className="modal-header">
                <h3>Agendar Pagamento</h3>
                <button className="modal-close" onClick={() => setShowScheduleModal(false)}>×</button>
              </div>
              <div className="modal-body">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                    Solicitação #{selectedRequest.id} - {selectedRequest.requestedBy}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>
                    Valor: R$ {selectedRequest.total.toFixed(2)}
                  </div>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                    Data do pagamento
                  </label>
                  <input 
                    type="date" 
                    value={paymentDate}
                    onChange={e => setPaymentDate(e.target.value)}
                    style={{ width: '100%', padding: '8px', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 'var(--border-radius-md)' }}
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button className="btn btn-success" onClick={handleConfirmPayment}>Confirmar Pagamento</button>
                <button className="btn" onClick={() => setShowScheduleModal(false)}>Cancelar</button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ paddingTop: '16px' }}>
      <div className="section-title">Pagamentos Realizados</div>
      <div className="section-sub">Histórico de reembolsos efetuados e comprovantes arquivados</div>
      <div className="card">
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input type="text" placeholder="Buscar..." style={{ flex: 1, maxWidth: '250px' }} />
          <input type="month" value="2026-04" style={{ width: '150px' }} />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nº</th>
                <th>Colaborador</th>
                <th>Valor</th>
                <th>Data pagamento</th>
                <th>Comprovante</th>
              </tr>
            </thead>
            <tbody>
              {getPaidRequests().map(request => (
                <tr key={request.id}>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#{request.id}</td>
                  <td>{request.requestedBy}</td>
                  <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                  <td style={{ fontSize: '12px' }}>{request.paymentDate}</td>
                  <td>
                    {request.archivedAttachments && request.archivedAttachments.length > 0 ? (
                      <button className="btn btn-sm">📁 Abrir ({request.archivedAttachments.length})</button>
                    ) : (
                      <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Não arquivado</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FinanceiroPages;