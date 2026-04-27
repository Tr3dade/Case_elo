import React, { useState } from 'react';
import { sampleRequests, ReimbursementRequest, projects, costCenters } from '../../data/reimbursement';

interface TecnicoPagesProps {
  tab: number;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  itemErrors: { [itemId: string]: string[] };
}

const TecnicoPages: React.FC<TecnicoPagesProps> = ({ tab }) => {
  const [validationResults, setValidationResults] = useState<{ [requestId: string]: ValidationResult }>({});
  const [comments, setComments] = useState<{ [requestId: string]: string }>({});

  const validateRequest = (request: ReimbursementRequest): ValidationResult => {
    const errors: string[] = [];
    const itemErrors: { [itemId: string]: string[] } = {};
    let isValid = true;

    const today = new Date();
    const ninetyDaysAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);

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

      // Validar anexos
      if (request.attachments.length === 0) {
        errors.push('Nenhum comprovante fiscal anexado');
        isValid = false;
      } else {
        if (item.type === 'Transporte' && !item.description.toLowerCase().includes('uber') && !item.description.toLowerCase().includes('taxi')) {
          itemErrorList.push('Descrição não corresponde ao tipo de gasto');
          isValid = false;
        }
      }

      if (itemErrorList.length > 0) {
        itemErrors[item.id] = itemErrorList;
      }
    });

    return { isValid, errors, itemErrors };
  };

  const handleValidateRequest = (request: ReimbursementRequest) => {
    const validation = validateRequest(request);
    setValidationResults(prev => ({ ...prev, [request.id]: validation }));
    if (validation.isValid) {
      request.status = 'Em análise';
    } else {
      request.status = 'Aguardando ajustes';
    }
  };

  const handleRequestAdjustments = (request: ReimbursementRequest, comment: string) => {
    const newHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Fernanda Souza',
      action: 'Solicitado ajustes ao colaborador',
      comments: comment || undefined
    };

    request.status = 'Aguardando ajustes';
    request.history.push(newHistory);
    setComments(prev => ({ ...prev, [request.id]: comment }));
  };

  const handleForwardToManager = (request: ReimbursementRequest) => {
    const newHistory = {
      id: `hist-${Date.now()}`,
      timestamp: new Date().toLocaleString('pt-BR'),
      actor: 'Fernanda Souza',
      action: 'Encaminhado ao gestor para aprovação',
      comments: comments[request.id] || undefined
    };

    request.status = 'Em análise';
    request.history.push(newHistory);
  };

  const getPendingRequests = () => {
    return sampleRequests.filter(req => req.status === 'Em análise');
  };

  if (tab === 0) {
    const pendingRequests = getPendingRequests();

    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Validar Conformidade</div>
        <div className="section-sub">Verificar informações e comprovantes antes de encaminhar ao gestor</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Para validar</div>
            <div className="stat-val amber">{pendingRequests.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Validadas hoje</div>
            <div className="stat-val green">3</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Com pendências</div>
            <div className="stat-val red">2</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Aguard. gestor</div>
            <div className="stat-val blue">5</div>
          </div>
        </div>

        {pendingRequests.length === 0 ? (
          <div className="card">
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
              Nenhuma solicitação pendente de validação
            </div>
          </div>
        ) : (
          pendingRequests.map(request => {
            const validation = validationResults[request.id];
            const isValidated = !!validation;

            return (
              <div key={request.id} className="card">
                <div className="card-title">Solicitação #{request.id} — {request.requestedBy}</div>
                <div className="two-col">
                  <div>
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>Itens da solicitação</div>
                      {request.items.map(item => {
                        const project = projects.find(p => p.id === item.projectId);
                        const costCenter = costCenters.find(c => c.id === item.costCenterId);
                        const itemValidationErrors = validation?.itemErrors[item.id] || [];

                        return (
                          <div key={item.id} style={{ 
                            padding: '8px', 
                            border: '0.5px solid var(--color-border-tertiary)', 
                            borderRadius: 'var(--border-radius-sm)', 
                            marginBottom: '8px',
                            background: itemValidationErrors.length > 0 ? 'rgba(255, 85, 85, 0.05)' : 'transparent'
                          }}>
                            <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px' }}>
                              {item.type} - R$ {item.amount.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '2px' }}>
                              {item.description}
                            </div>
                            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                              Data: {new Date(item.date).toLocaleDateString('pt-BR')} | Projeto: {project?.name || 'N/A'} | CC: {costCenter?.code || 'N/A'}
                            </div>
                            {itemValidationErrors.length > 0 && (
                              <div style={{ marginTop: '6px' }}>
                                {itemValidationErrors.map((error, idx) => (
                                  <div key={idx} style={{ fontSize: '11px', color: 'var(--color-accent-red)', marginBottom: '2px' }}>
                                    ⚠ {error}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    {validation && !validation.isValid && (
                      <div style={{ marginTop: '12px', padding: '8px', background: 'rgba(255, 85, 85, 0.05)', border: '0.5px solid var(--color-accent-red)', borderRadius: 'var(--border-radius-sm)' }}>
                        <div style={{ fontSize: '12px', fontWeight: '500', color: 'var(--color-accent-red)', marginBottom: '4px' }}>Inconsistências encontradas:</div>
                        {validation.errors.map((error, idx) => (
                          <div key={idx} style={{ fontSize: '11px', color: 'var(--color-accent-red)' }}>
                            • {error}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>Comprovantes anexados ({request.attachments.length})</div>
                    {request.attachments.length === 0 ? (
                      <div style={{ background: 'var(--color-background-secondary)', border: '0.5px solid var(--color-accent-red)', borderRadius: 'var(--border-radius-md)', padding: '24px', textAlign: 'center', color: 'var(--color-accent-red)' }}>
                        <div style={{ fontSize: '24px', marginBottom: '6px' }}>⚠</div>
                        <div style={{ fontSize: '13px', fontWeight: '500' }}>Nenhum comprovante anexado</div>
                      </div>
                    ) : (
                      request.attachments.map((attachment, idx) => (
                        <div key={idx} style={{ background: 'var(--color-background-secondary)', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 'var(--border-radius-md)', padding: '12px', marginBottom: '8px' }}>
                          <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px' }}>{attachment}</div>
                          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>PDF • 128 KB</div>
                          <button className="btn btn-sm">Visualizar</button>
                        </div>
                      ))
                    )}
                    {isValidated && (
                      <div style={{ marginTop: '12px' }}>
                        <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Observação (opcional)</label>
                        <textarea 
                          rows={3} 
                          placeholder="Apontar pendências ou observações..."
                          value={comments[request.id] || ''}
                          onChange={e => setComments(prev => ({ ...prev, [request.id]: e.target.value }))}
                        />
                      </div>
                    )}
                  </div>
                </div>
                <div className="action-row">
                  {!isValidated ? (
                    <button className="btn btn-primary" onClick={() => handleValidateRequest(request)}>
                      Validar Solicitação
                    </button>
                  ) : validation?.isValid ? (
                    <>
                      <button className="btn btn-danger" onClick={() => handleRequestAdjustments(request, comments[request.id] || '')}>Solicitar ajustes</button>
                      <button className="btn btn-primary" onClick={() => handleForwardToManager(request)}>Encaminhar ao gestor</button>
                    </>
                  ) : (
                    <button className="btn btn-danger" onClick={() => handleRequestAdjustments(request, comments[request.id] || '')}>Solicitar ajustes</button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    );
  }

  if (tab === 1) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Em Andamento</div>
        <div className="section-sub">Solicitações que aguardam resposta de gestor ou financeiro</div>
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Colaborador</th>
                  <th>Gestor</th>
                  <th>Valor</th>
                  <th>Etapa atual</th>
                  <th>Desde</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-018</td>
                  <td>João Silva</td>
                  <td>Paulo Lima</td>
                  <td style={{ fontWeight: '500' }}>R$ 156,00</td>
                  <td><span className="badge badge-review">Aguard. gestor</span></td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>15/04</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ paddingTop: '16px' }}>
      <div className="section-title">Histórico</div>
      <div className="section-sub">Todas as solicitações processadas</div>
      <div className="card">
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <input type="text" placeholder="Buscar por colaborador ou Nº..." style={{ flex: 1, maxWidth: '300px' }} />
          <select style={{ width: '160px' }}>
            <option>Todos os status</option>
            <option>Aprovado</option>
            <option>Rejeitado</option>
            <option>Pago</option>
          </select>
          <input type="month" value="2026-04" style={{ width: '150px' }} />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Nº</th>
                <th>Colaborador</th>
                <th>Gestor</th>
                <th>Valor</th>
                <th>Status</th>
                <th>Encerrado em</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-015</td>
                <td>João Silva</td>
                <td>Paulo Lima</td>
                <td style={{ fontWeight: '500' }}>R$ 89,50</td>
                <td><span className="badge badge-paid">Pago</span></td>
                <td style={{ fontSize: '12px' }}>05/04/2026</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TecnicoPages;