import React, { useState } from 'react';
import { sampleRequests, ReimbursementRequest, projects, costCenters, ActionHistory } from '../../data/reimbursement';

interface GestorPagesProps {
  tab: number;
}

const GestorPages: React.FC<GestorPagesProps> = ({ tab }) => {
  const [selectedRequest, setSelectedRequest] = useState<ReimbursementRequest | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [actionComments, setActionComments] = useState('');
  const [itemDecisions, setItemDecisions] = useState<{ [itemId: string]: 'Aprovado' | 'Rejeitado' }>({});

  const getPendingRequests = () => sampleRequests.filter(req => req.status === 'Em análise');
  const getApprovedRequests = () => sampleRequests.filter(req => req.status === 'Aprovado');
  const getRejectedRequests = () => sampleRequests.filter(req => req.status === 'Rejeitado');

  const handleViewRequest = (request: ReimbursementRequest) => {
    setSelectedRequest(request);
    setShowModal(true);
    setActionComments('');
    setItemDecisions({});
  };

  const handleApproveAll = (request?: ReimbursementRequest) => {
    const req = request ?? selectedRequest;
    if (!req) return;

    const newHistory: ActionHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Paulo Lima',
      action: 'Aprovado totalmente pelo gestor',
      comments: actionComments || undefined,
    };

    req.status = 'Aprovado';
    req.items.forEach(item => {
      item.status = 'Aprovado';
      delete item.rejectionReason;
    });
    req.history.push(newHistory);

    setShowModal(false);
    setSelectedRequest(null);
  };

  const handlePartialApproval = () => {
    if (!selectedRequest) return;

    const approvedItems = Object.keys(itemDecisions).filter(id => itemDecisions[id] === 'Aprovado');
    const rejectedItems = Object.keys(itemDecisions).filter(id => itemDecisions[id] === 'Rejeitado');

    if (approvedItems.length === 0 && rejectedItems.length === 0) {
      alert('Selecione pelo menos um item para aprovar ou rejeitar.');
      return;
    }

    const newHistory: ActionHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Paulo Lima',
      action: 'Aprovação parcial pelo gestor',
      comments: actionComments || undefined,
    };

    selectedRequest.items.forEach(item => {
      const decision = itemDecisions[item.id];
      if (decision) {
        item.status = decision;
        if (decision === 'Rejeitado') {
          item.rejectionReason = 'Rejeitado pelo gestor';
        } else {
          delete item.rejectionReason;
        }
      }
    });

    const allApproved = selectedRequest.items.every(item => item.status === 'Aprovado');
    selectedRequest.status = allApproved ? 'Aprovado' : 'Aprovado';
    selectedRequest.history.push(newHistory);

    setShowModal(false);
    setSelectedRequest(null);
  };

  const handleReject = (request?: ReimbursementRequest) => {
    const req = request ?? selectedRequest;
    if (!req) return;

    const newHistory: ActionHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Paulo Lima',
      action: 'Rejeitado pelo gestor',
      comments: actionComments || undefined,
    };

    req.status = 'Rejeitado';
    req.items.forEach(item => {
      item.status = 'Rejeitado';
      item.rejectionReason = 'Solicitação rejeitada pelo gestor';
    });
    req.history.push(newHistory);

    setShowModal(false);
    setSelectedRequest(null);
  };

  const handleRequestAdjustments = () => {
    if (!selectedRequest) return;

    const newHistory: ActionHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Paulo Lima',
      action: 'Ajustes solicitados pelo gestor',
      comments: actionComments,
    };

    selectedRequest.status = 'Aguardando ajustes';
    selectedRequest.history.push(newHistory);

    setShowModal(false);
    setSelectedRequest(null);
  };

  return (
    <>
      {tab === 0 && (
        <div style={{ paddingTop: '16px' }}>
          <div className="section-title">Pendentes de Aprovação</div>
          <div className="section-sub">Solicitações que aguardam sua avaliação</div>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Pendentes</div>
              <div className="stat-val amber">{getPendingRequests().length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Valor total pendente</div>
              <div className="stat-val blue">R$ {getPendingRequests().reduce((sum, req) => sum + req.total, 0).toFixed(2)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Aprovadas este mês</div>
              <div className="stat-val green">12</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Rejeitadas este mês</div>
              <div className="stat-val red">2</div>
            </div>
          </div>

          {getPendingRequests().length === 0 ? (
            <div className="card">
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
                Nenhuma solicitação pendente de aprovação
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="info-box">
                <p>Você pode aprovar, aprovar parcialmente, solicitar ajustes ou rejeitar cada solicitação. O colaborador será notificado automaticamente.</p>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Solicitação</th>
                      <th>Colaborador</th>
                      <th>Centro de custo</th>
                      <th>Tipo</th>
                      <th>Valor</th>
                      <th>Data envio</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {getPendingRequests().map(request => (
                      <tr key={request.id}>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#{request.id}</td>
                        <td>
                          <div style={{ fontSize: '13px', fontWeight: '500' }}>{request.requestedBy}</div>
                        </td>
                        <td><span className="chip">CC: {request.costCenterIds.join(', ')}</span></td>
                        <td><span className="chip">{request.items.map(item => item.type).join(', ')}</span></td>
                        <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{request.createdAt}</td>
                        <td>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <button className="btn btn-sm btn-success" onClick={() => handleApproveAll(request)}>Aprovar</button>
                            <button className="btn btn-sm btn-danger" onClick={() => handleReject(request)}>Rejeitar</button>
                            <button className="btn btn-sm" onClick={() => handleViewRequest(request)}>Ver detalhes</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 1 && (
        <div style={{ paddingTop: '16px' }}>
          <div className="section-title">Aprovados</div>
          <div className="section-sub">Solicitações que você aprovou</div>
          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Nº</th>
                    <th>Colaborador</th>
                    <th>Valor</th>
                    <th>Aprovado em</th>
                    <th>Status pagamento</th>
                  </tr>
                </thead>
                <tbody>
                  {getApprovedRequests().map(request => (
                    <tr key={request.id}>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#{request.id}</td>
                      <td>{request.requestedBy}</td>
                      <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{request.createdAt}</td>
                      <td><span className="badge badge-paid">Pago</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === 2 && (
        <div style={{ paddingTop: '16px' }}>
          <div className="section-title">Rejeitados</div>
          <div className="section-sub">Solicitações que foram rejeitadas</div>
          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Nº</th>
                    <th>Colaborador</th>
                    <th>Valor</th>
                    <th>Motivo</th>
                    <th>Data</th>
                  </tr>
                </thead>
                <tbody>
                  {getRejectedRequests().map(request => (
                    <tr key={request.id}>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#{request.id}</td>
                      <td>{request.requestedBy}</td>
                      <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Rejeitado pelo gestor</td>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{request.createdAt}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {showModal && selectedRequest && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Solicitação #{selectedRequest.id} - {selectedRequest.requestedBy}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <div className="two-col">
                <div>
                  <h4>Itens da solicitação</h4>
                  {selectedRequest.items.map(item => {
                    const project = projects.find(p => p.id === item.projectId);
                    const costCenter = costCenters.find(c => c.id === item.costCenterId);

                    return (
                      <div key={item.id} style={{
                        padding: '12px',
                        border: '0.5px solid var(--color-border-tertiary)',
                        borderRadius: 'var(--border-radius-sm)',
                        marginBottom: '8px',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                          <div>
                            <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                              {item.type} - R$ {item.amount.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '2px' }}>
                              {item.description}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                              Data: {new Date(item.date).toLocaleDateString('pt-BR')} | Projeto: {project?.name || 'N/A'} | CC: {costCenter?.code || 'N/A'}
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <label>
                              <input
                                type="radio"
                                name={`item-${item.id}`}
                                value="Aprovado"
                                checked={itemDecisions[item.id] === 'Aprovado'}
                                onChange={() => setItemDecisions(prev => ({ ...prev, [item.id]: 'Aprovado' }))}
                              /> Aprovar
                            </label>
                            <label>
                              <input
                                type="radio"
                                name={`item-${item.id}`}
                                value="Rejeitado"
                                checked={itemDecisions[item.id] === 'Rejeitado'}
                                onChange={() => setItemDecisions(prev => ({ ...prev, [item.id]: 'Rejeitado' }))}
                              /> Rejeitar
                            </label>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div>
                  <h4>Comprovantes anexados ({selectedRequest.attachments.length})</h4>
                  {selectedRequest.attachments.map((attachment, idx) => (
                    <div key={idx} style={{ background: 'var(--color-background-secondary)', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 'var(--border-radius-md)', padding: '12px', marginBottom: '8px' }}>
                      <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px' }}>{attachment}</div>
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>PDF • 128 KB</div>
                      <button className="btn btn-sm">Visualizar</button>
                    </div>
                  ))}
                  <h4>Histórico</h4>
                  <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {selectedRequest.history.map(hist => (
                      <div key={hist.id} style={{ padding: '8px', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
                        <div style={{ fontSize: '12px', fontWeight: '500' }}>{hist.action}</div>
                        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                          {hist.timestamp} - {hist.actor}
                        </div>
                        {hist.comments && (
                          <div style={{ fontSize: '11px', marginTop: '4px', fontStyle: 'italic' }}>
                            "{hist.comments}"
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div style={{ marginTop: '16px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                  Comentários (opcional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Adicione observações ou justificativas..."
                  value={actionComments}
                  onChange={e => setActionComments(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-danger" onClick={handleRequestAdjustments}>Solicitar ajustes</button>
              <button className="btn btn-warning" onClick={handlePartialApproval}>Aprovação parcial</button>
              <button className="btn btn-success" onClick={() => handleApproveAll()}>Aprovar tudo</button>
              <button className="btn" onClick={() => setShowModal(false)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GestorPages;
