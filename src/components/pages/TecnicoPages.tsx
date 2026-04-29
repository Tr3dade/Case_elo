import React, { useState, useMemo } from 'react';
import { sampleRequests, ReimbursementRequest, projects, costCenters } from '../../data/reimbursement';

interface TecnicoPagesProps {
  tab: number;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  itemErrors: { [itemId: string]: string[] };
}

interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
}

interface TechnicianAnalysis {
  requestId: string;
  analysisDate: string;
  decision: 'Aprovada' | 'Devolvida';
  managerName?: string;
  rejectionReason?: string;
}

const TecnicoPages: React.FC<TecnicoPagesProps> = ({ tab }) => {
  const [_validationResults, setValidationResults] = useState<{ [requestId: string]: ValidationResult }>({});
  const [_comments, setComments] = useState<{ [requestId: string]: string }>({});
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null);
  const [checklist, setChecklist] = useState<{ [requestId: string]: ChecklistItem[] }>({});
  const [showVoucherModal, setShowVoucherModal] = useState(false);
  const [selectedVoucher, setSelectedVoucher] = useState<string | null>(null);
  const [showRejectionModal, setShowRejectionModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [technicianAnalyses, setTechnicianAnalyses] = useState<TechnicianAnalysis[]>([
    {
      requestId: '2024-021',
      analysisDate: '15/04/2026',
      decision: 'Aprovada',
      managerName: 'Paulo Lima'
    },
    {
      requestId: '2024-025',
      analysisDate: '16/04/2026',
      decision: 'Devolvida',
      rejectionReason: 'Faltam comprovantes fiscais'
    },
    {
      requestId: '2024-028',
      analysisDate: '17/04/2026',
      decision: 'Aprovada',
      managerName: 'Maria Santos'
    }
  ]);

  const validateRequest = (request: ReimbursementRequest): ValidationResult => {
    const errors: string[] = [];
    const itemErrors: { [itemId: string]: string[] } = {};
    let isValid = true;

    const today = new Date();
    const ninetyDaysAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);

    // Verificar se há comprovantes
    if (request.attachments.length === 0) {
      errors.push('Nenhum comprovante fiscal anexado');
      isValid = false;
    }

    // Validar cada item
    request.items.forEach(item => {
      const itemErrorList: string[] = [];

      // Validar prazo (90 dias)
      const itemDate = new Date(item.date);
      if (itemDate < ninetyDaysAgo) {
        itemErrorList.push('Gasto com data superior a 90 dias não é elegível para reembolso');
        isValid = false;
      }

      // Validar se projeto existe
      const project = projects.find(p => p.id === item.projectId);
      if (!project) {
        itemErrorList.push('Projeto não encontrado');
        isValid = false;
      }

      // Validar centro de custo
      const costCenter = costCenters.find(c => c.id === item.costCenterId);
      if (!costCenter) {
        itemErrorList.push('Centro de custo inválido');
        isValid = false;
      }

      // Validar descrição e campos obrigatórios
      if (!item.description || item.description.trim() === '') {
        itemErrorList.push('Descrição do gasto não preenchida');
        isValid = false;
      }

      if (item.amount <= 0) {
        itemErrorList.push('Valor inválido');
        isValid = false;
      }

      if (itemErrorList.length > 0) {
        itemErrors[item.id] = itemErrorList;
      }
    });

    return { isValid, errors, itemErrors };
  };

  const initializeChecklist = (request: ReimbursementRequest) => {
    const requestChecklist: ChecklistItem[] = [
      {
        id: 'fields',
        label: 'Todos os campos obrigatórios preenchidos',
        checked: false
      },
      {
        id: 'vouchers',
        label: 'Comprovante fiscal presente em cada item',
        checked: request.attachments.length > 0
      },
      {
        id: 'date',
        label: 'Data de execução dentro do prazo de 90 dias',
        checked: request.items.every(item => {
          const itemDate = new Date(item.date);
          const today = new Date();
          const ninetyDaysAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
          return itemDate >= ninetyDaysAgo;
        })
      },
      {
        id: 'values',
        label: 'Valores consistentes com os comprovantes',
        checked: false
      }
    ];
    setChecklist(prev => ({ ...prev, [request.id]: requestChecklist }));
  };

  const toggleChecklistItem = (requestId: string, itemId: string) => {
    setChecklist(prev => ({
      ...prev,
      [requestId]: prev[requestId].map(item =>
        item.id === itemId ? { ...item, checked: !item.checked } : item
      )
    }));
  };

  const handleAnalyzeRequest = (request: ReimbursementRequest) => {
    setSelectedRequestId(request.id);
    const validation = validateRequest(request);
    setValidationResults(prev => ({ ...prev, [request.id]: validation }));
    
    if (!checklist[request.id]) {
      initializeChecklist(request);
    }
  };

  const handleApproveRequest = (request: ReimbursementRequest) => {
    const currentChecklist = checklist[request.id];
    const allChecked = currentChecklist && currentChecklist.every(item => item.checked);
    
    if (!allChecked) {
      alert('Por favor, marque todos os itens do checklist antes de aprovar.');
      return;
    }

    const managerCC = costCenters.find(cc => cc.id === request.costCenterIds[0]);
    const managerName = managerCC?.manager || 'Gestor do CC';

    const newAnalysis: TechnicianAnalysis = {
      requestId: request.id,
      analysisDate: new Date().toLocaleDateString('pt-BR'),
      decision: 'Aprovada',
      managerName
    };

    setTechnicianAnalyses(prev => [...prev, newAnalysis]);
    
    // Atualizar status da solicitação
    request.status = 'Aprovado';
    request.history.push({
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Fernanda Souza',
      action: 'Validado pelo técnico administrativo - Encaminhado ao gestor'
    });

    setSelectedRequestId(null);
    setComments(prev => ({ ...prev, [request.id]: '' }));
    setChecklist(prev => ({ ...prev, [request.id]: [] }));
  };

  const handleRejectRequest = () => {
    if (!rejectionReason.trim()) {
      alert('Por favor, informe o motivo da devolução.');
      return;
    }

    const request = sampleRequests.find(r => r.id === selectedRequestId);
    if (!request) return;

    const newAnalysis: TechnicianAnalysis = {
      requestId: request.id,
      analysisDate: new Date().toLocaleDateString('pt-BR'),
      decision: 'Devolvida',
      rejectionReason
    };

    setTechnicianAnalyses(prev => [...prev, newAnalysis]);

    request.status = 'Aguardando ajustes';
    request.history.push({
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Fernanda Souza',
      action: 'Devolvido para ajustes',
      comments: rejectionReason
    });

    setSelectedRequestId(null);
    setRejectionReason('');
    setShowRejectionModal(false);
    setComments(prev => ({ ...prev, [request.id]: '' }));
    setChecklist(prev => ({ ...prev, [request.id]: [] }));
  };

  const handleExportReport = () => {
    const data = [
      ['ID', 'Colaborador', 'Valor Total', 'Nº de Itens', 'Data de Envio', 'Status'],
      ...pendingRequests.map(req => [
        req.id,
        req.requestedBy,
        `R$ ${req.total.toFixed(2)}`,
        req.items.length,
        req.createdAt,
        'Pendente'
      ]),
      ...technicianAnalyses.map(analysis => {
        const request = sampleRequests.find(r => r.id === analysis.requestId);
        return request ? [
          request.id,
          request.requestedBy,
          `R$ ${request.total.toFixed(2)}`,
          request.items.length,
          request.createdAt,
          analysis.decision
        ] : [];
      }).filter(row => row.length > 0)
    ];

    const csvContent = data.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `Conformidade_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const pendingRequests = useMemo(() => {
    return sampleRequests.filter(req => req.status === 'Em análise').sort((a, b) => {
      const dateA = new Date(a.createdAt.split('/').reverse().join('-'));
      const dateB = new Date(b.createdAt.split('/').reverse().join('-'));
      return dateA.getTime() - dateB.getTime();
    });
  }, []);

  const nonConformRequests = useMemo(() => {
    return sampleRequests.filter(req => req.status === 'Aguardando ajustes');
  }, []);

  const approvedRequests = useMemo(() => {
    return sampleRequests.filter(req => req.status === 'Aprovado' && technicianAnalyses.some(t => t.requestId === req.id && t.decision === 'Aprovada'));
  }, [technicianAnalyses]);

  // Painel de Conformidade - Aba 0
  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Painel de Conformidade</div>
        <div className="section-sub">Gerenciar fila de validação de reembolsos</div>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Pendentes de Revisão</div>
            <div className="stat-val amber">{pendingRequests.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Não Conformes</div>
            <div className="stat-val red">{nonConformRequests.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Aprovadas para Gestor</div>
            <div className="stat-val green">{approvedRequests.length}</div>
          </div>
        </div>

        <div className="card">
          <div className="card-title">Fila de Conformidade</div>
          <div style={{ marginBottom: '12px' }}>
            <button className="btn btn-sm" onClick={handleExportReport} style={{ float: 'right' }}>
              Exportar Relatório
            </button>
            <div style={{ clear: 'both' }}></div>
          </div>

          {pendingRequests.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Nenhuma solicitação pendente de conformidade
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Colaborador</th>
                    <th>Valor Total</th>
                    <th>Nº de Itens</th>
                    <th>Data de Envio</th>
                    <th>Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {pendingRequests.map(request => (
                    <tr key={request.id}>
                      <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{request.id}</td>
                      <td>{request.requestedBy}</td>
                      <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                      <td>{request.items.length}</td>
                      <td style={{ fontSize: '12px' }}>{request.createdAt}</td>
                      <td>
                        <button 
                          className="btn btn-sm" 
                          onClick={() => handleAnalyzeRequest(request)}
                        >
                          Analisar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal de Análise */}
        {selectedRequestId && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              maxWidth: '900px',
              width: '90%',
              maxHeight: '90vh',
              overflow: 'auto',
              padding: '24px'
            }}>
              {(() => {
                const request = sampleRequests.find(r => r.id === selectedRequestId);
                if (!request) return null;

                const requestChecklist = checklist[request.id] || [];
                const allChecked = requestChecklist.every(item => item.checked);

                return (
                  <>
                    <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--color-border-secondary)', paddingBottom: '16px' }}>
                      <h2 style={{ marginTop: 0, marginBottom: '12px' }}>Análise de Conformidade - {request.id}</h2>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', fontSize: '13px' }}>
                        <div>
                          <div style={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Colaborador</div>
                          <strong>{request.requestedBy}</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Centro de Custo</div>
                          <strong>{costCenters.find(c => c.id === request.costCenterIds[0])?.code}</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Valor Total</div>
                          <strong>R$ {request.total.toFixed(2)}</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--color-text-secondary)', marginBottom: '4px' }}>Data de Envio</div>
                          <strong>{request.createdAt}</strong>
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 250px', gap: '24px' }}>
                      <div>
                        <h3 style={{ marginTop: 0 }}>Itens da Solicitação</h3>
                        <div className="table-wrap">
                          <table style={{ width: '100%' }}>
                            <thead>
                              <tr>
                                <th>Tipo</th>
                                <th>Descrição</th>
                                <th>Data</th>
                                <th>Valor</th>
                                <th>Comprovante</th>
                              </tr>
                            </thead>
                            <tbody>
                              {request.items.map(item => (
                                <tr key={item.id}>
                                  <td style={{ fontSize: '12px' }}>{item.type}</td>
                                  <td style={{ fontSize: '12px' }}>{item.description}</td>
                                  <td style={{ fontSize: '12px' }}>{new Date(item.date).toLocaleDateString('pt-BR')}</td>
                                  <td style={{ fontSize: '12px', fontWeight: '500' }}>R$ {item.amount.toFixed(2)}</td>
                                  <td>
                                    {request.attachments.length > 0 ? (
                                      <button
                                        className="btn btn-sm"
                                        onClick={() => {
                                          setSelectedVoucher(request.attachments[0]);
                                          setShowVoucherModal(true);
                                        }}
                                      >
                                        Visualizar
                                      </button>
                                    ) : (
                                      <span style={{ color: 'var(--color-accent-red)' }}>✗</span>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        <div style={{ marginTop: '24px' }}>
                          <h3>Comprovantes Anexados</h3>
                          {request.attachments.length === 0 ? (
                            <div style={{ padding: '16px', backgroundColor: 'rgba(255, 85, 85, 0.1)', borderRadius: '4px', color: 'var(--color-accent-red)', textAlign: 'center' }}>
                              ⚠️ Nenhum comprovante anexado
                            </div>
                          ) : (
                            request.attachments.map((attachment, idx) => (
                              <div
                                key={idx}
                                style={{
                                  padding: '12px',
                                  backgroundColor: 'var(--color-background-secondary)',
                                  border: '1px solid var(--color-border-tertiary)',
                                  borderRadius: '4px',
                                  marginBottom: '8px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center'
                                }}
                              >
                                <div>
                                  <div style={{ fontWeight: '500', fontSize: '13px' }}>{attachment}</div>
                                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>PDF • 128 KB</div>
                                </div>
                                <button
                                  className="btn btn-sm"
                                  onClick={() => {
                                    setSelectedVoucher(attachment);
                                    setShowVoucherModal(true);
                                  }}
                                >
                                  Visualizar
                                </button>
                              </div>
                            ))
                          )}
                        </div>
                      </div>

                      {/* Checklist Lateral */}
                      <div style={{
                        backgroundColor: 'var(--color-background-secondary)',
                        padding: '16px',
                        borderRadius: '8px',
                        height: 'fit-content'
                      }}>
                        <h4 style={{ marginTop: 0 }}>Checklist de Conformidade</h4>
                        {requestChecklist.map(item => (
                          <label key={item.id} style={{
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '8px',
                            marginBottom: '12px',
                            cursor: 'pointer',
                            fontSize: '13px'
                          }}>
                            <input
                              type="checkbox"
                              checked={item.checked}
                              onChange={() => toggleChecklistItem(request.id, item.id)}
                              style={{ marginTop: '2px', cursor: 'pointer' }}
                            />
                            <span>{item.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Ações */}
                    <div style={{ marginTop: '24px', borderTop: '1px solid var(--color-border-secondary)', paddingTop: '16px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          setSelectedRequestId(null);
                          setChecklist(prev => ({ ...prev, [request.id]: [] }));
                        }}
                      >
                        Cancelar
                      </button>
                      <button
                        className="btn btn-danger"
                        onClick={() => setShowRejectionModal(true)}
                      >
                        Devolver para Ajuste
                      </button>
                      <button
                        className="btn btn-primary"
                        disabled={!allChecked}
                        onClick={() => handleApproveRequest(request)}
                        style={{ opacity: allChecked ? 1 : 0.5, cursor: allChecked ? 'pointer' : 'not-allowed' }}
                      >
                        Aprovar e Encaminhar ao Gestor
                      </button>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        {/* Modal de Rejeição */}
        {showRejectionModal && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1001
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '500px',
              width: '90%'
            }}>
              <h3 style={{ marginTop: 0 }}>Devolver para Ajuste</h3>
              <p style={{ color: 'var(--color-text-secondary)' }}>
                Por favor, descreva o motivo da devolução:
              </p>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Ex: Faltam comprovantes, valores inconsistentes, data inválida..."
                rows={4}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '4px',
                  border: '1px solid var(--color-border-secondary)',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
              <div style={{ marginTop: '16px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowRejectionModal(false);
                    setRejectionReason('');
                  }}
                >
                  Cancelar
                </button>
                <button
                  className="btn btn-danger"
                  onClick={handleRejectRequest}
                >
                  Confirmar Devolução
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal de Visualização de Comprovante */}
        {showVoucherModal && selectedVoucher && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1002
          }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '24px',
              maxWidth: '600px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h3 style={{ marginTop: 0 }}>{selectedVoucher}</h3>
                <button
                  className="btn btn-sm"
                  onClick={() => {
                    setShowVoucherModal(false);
                    setSelectedVoucher(null);
                  }}
                  style={{ background: 'transparent', color: 'var(--color-text-secondary)', border: 'none', cursor: 'pointer', fontSize: '24px' }}
                >
                  ✕
                </button>
              </div>
              <div style={{
                backgroundColor: '#f0f0f0',
                borderRadius: '4px',
                minHeight: '400px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                color: 'var(--color-text-secondary)'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>📄</div>
                <div style={{ fontSize: '14px' }}>Visualização de PDF</div>
                <div style={{ fontSize: '12px', marginTop: '8px' }}>Documento: {selectedVoucher}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Aba 1 - Em Andamento
  if (tab === 1) {
    const inProgressRequests = sampleRequests.filter(req => 
      req.status === 'Aprovado' && technicianAnalyses.some(t => t.requestId === req.id && t.decision === 'Aprovada')
    );

    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Em Andamento</div>
        <div className="section-sub">Solicitações aprovadas pelo técnico aguardando decisão do gestor</div>
        
        {inProgressRequests.length === 0 ? (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Nenhuma solicitação em andamento
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Colaborador</th>
                    <th>Gestor</th>
                    <th>Valor</th>
                    <th>Etapa Atual</th>
                    <th>Desde</th>
                  </tr>
                </thead>
                <tbody>
                  {inProgressRequests.map(request => {
                    const analysis = technicianAnalyses.find(t => t.requestId === request.id);
                    return (
                      <tr key={request.id}>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{request.id}</td>
                        <td>{request.requestedBy}</td>
                        <td>{analysis?.managerName || 'N/A'}</td>
                        <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                        <td>
                          <span className="badge badge-review">Aguard. gestor</span>
                        </td>
                        <td style={{ fontSize: '12px' }}>{analysis?.analysisDate || request.createdAt}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Aba 2 - Histórico
  if (tab === 2) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Histórico de Análises</div>
        <div className="section-sub">Todas as solicitações já processadas pelo técnico administrativo</div>

        <div className="card">
          <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <input
              type="text"
              placeholder="Buscar por colaborador ou ID..."
              style={{ flex: 1, minWidth: '250px' }}
            />
            <select style={{ width: '180px' }}>
              <option>Todas as decisões</option>
              <option>Aprovada</option>
              <option>Devolvida</option>
            </select>
            <input type="month" defaultValue="2026-04" style={{ width: '150px' }} />
          </div>

          {technicianAnalyses.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Nenhuma análise realizada ainda
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID Solicitação</th>
                    <th>Colaborador</th>
                    <th>Data da Análise</th>
                    <th>Decisão</th>
                    <th>Gestor Encaminhado</th>
                    <th>Observações</th>
                  </tr>
                </thead>
                <tbody>
                  {technicianAnalyses.map(analysis => {
                    const request = sampleRequests.find(r => r.id === analysis.requestId);
                    if (!request) return null;

                    return (
                      <tr key={analysis.requestId}>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{analysis.requestId}</td>
                        <td>{request.requestedBy}</td>
                        <td style={{ fontSize: '12px' }}>{analysis.analysisDate}</td>
                        <td>
                          <span className={`badge ${analysis.decision === 'Aprovada' ? 'badge-approved' : 'badge-rejected'}`}>
                            {analysis.decision}
                          </span>
                        </td>
                        <td style={{ fontSize: '12px' }}>
                          {analysis.decision === 'Aprovada' ? (
                            <strong>{analysis.managerName || 'N/A'}</strong>
                          ) : (
                            <span style={{ color: 'var(--color-text-secondary)' }}>—</span>
                          )}
                        </td>
                        <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)', maxWidth: '200px' }}>
                          {analysis.decision === 'Devolvida' && analysis.rejectionReason ? (
                            <span title={analysis.rejectionReason}>
                              {analysis.rejectionReason.substring(0, 40)}...
                            </span>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  }

  return <div>Página não encontrada</div>;
};

export default TecnicoPages;