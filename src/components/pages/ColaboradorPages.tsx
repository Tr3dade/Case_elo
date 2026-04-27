import React, { useMemo, useState, useEffect } from 'react';
import {
  costCenters,
  defaultReimbursementConfig,
  financeAdmin,
  projects,
  ReimbursementItem,
  ReimbursementRequest,
  sampleRequests
} from '../../data/reimbursement';
import { User } from '../../data/users';

interface ColaboradorPagesProps {
  tab: number;
  user: User;
  onTabChange: (tabIndex: number) => void;
}

const parseDateString = (dateString: string) => {
  const [day, month, year] = dateString.split('/').map(Number);
  return new Date(year, month - 1, day);
};

const initialItem = (): ReimbursementItem => ({
  id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  date: '',
  type: 'Transporte',
  description: '',
  projectId: projects[0].id,
  costCenterId: projects[0].costCenterId,
  amount: 0
});

const ColaboradorPages: React.FC<ColaboradorPagesProps> = ({ tab, user, onTabChange }) => {
  const [requests, setRequests] = useState<ReimbursementRequest[]>(sampleRequests);
  const [items, setItems] = useState<ReimbursementItem[]>([initialItem()]);
  const [month, setMonth] = useState('2026-04');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [selectedRequestId, setSelectedRequestId] = useState<string>(() => sampleRequests.find((request) => request.requestedBy === user.name)?.id || sampleRequests[0]?.id || '');
  const [message, setMessage] = useState<string>('');
  const [generalNotes, setGeneralNotes] = useState<string>('');
  const [selectedCostCenter, setSelectedCostCenter] = useState<number>(costCenters[0].id);
  const [filterStatus, setFilterStatus] = useState<string>('Todos');
  const [filterDateFrom, setFilterDateFrom] = useState<string>('');
  const [filterDateTo, setFilterDateTo] = useState<string>('');
  const [filterProject, setFilterProject] = useState<string>('Todos');
  const [appliedFilters, setAppliedFilters] = useState({
    status: 'Todos',
    dateFrom: '',
    dateTo: '',
    project: 'Todos'
  });
  const [editingRequestId, setEditingRequestId] = useState<string | null>(null);
  const [showAllRequests, setShowAllRequests] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 5;

  const attachmentsRequired = defaultReimbursementConfig.attachmentsRequired;

  const userRequests = useMemo(
    () => requests.filter((request) => request.requestedBy === user.name),
    [requests, user.name]
  );

  const sortedUserRequests = useMemo(
    () => [...userRequests].sort((a, b) => parseDateString(b.createdAt).getTime() - parseDateString(a.createdAt).getTime()),
    [userRequests]
  );

  const latestRequests = sortedUserRequests.slice(0, 5);

  const selectedRequest = userRequests.find((request) => request.id === selectedRequestId) ?? userRequests[0];

  useEffect(() => {
    if (!userRequests.some((request) => request.id === selectedRequestId)) {
      setSelectedRequestId(userRequests[0]?.id || '');
    }
  }, [userRequests, selectedRequestId]);

  const requestStats = useMemo(() => {
    const total = userRequests.reduce((sum, request) => sum + request.total, 0);
    const approved = userRequests.filter((request) => request.status === 'Aprovado').length;
    const pending = userRequests.filter((request) => request.status === 'Em análise').length;
    const rejected = userRequests.filter((request) => request.status === 'Rejeitado').length;
    return { total, approved, pending, rejected };
  }, [userRequests]);

  const handleItemChange = (
    index: number,
    field: 'date' | 'type' | 'description' | 'projectId' | 'amount',
    value: string | number
  ) => {
    setItems((current) => {
      const next = [...current];
      const item = { ...next[index] };

      if (field === 'projectId' && typeof value === 'string') {
        const project = projects.find((project) => project.id === value);
        item.projectId = value;
        item.costCenterId = project?.costCenterId ?? item.costCenterId;
      } else if (field === 'amount') {
        item.amount = Number(value);
      } else if (field === 'date' && typeof value === 'string') {
        // Validação de 90 dias
        const selectedDate = new Date(value);
        const today = new Date();
        const ninetyDaysAgo = new Date(today);
        ninetyDaysAgo.setDate(today.getDate() - 90);
        
        if (selectedDate < ninetyDaysAgo) {
          setMessage('Erro: Não é possível incluir despesas com mais de 90 dias da data atual.');
          return current; // Não atualiza se inválido
        }
        
        item.date = value;
      } else if (field === 'type' && typeof value === 'string') {
        item.type = value;
      } else if (field === 'description' && typeof value === 'string') {
        item.description = value;
      }

      next[index] = item;
      return next;
    });
  };

  const addItem = () => {
    setItems((current) => [...current, initialItem()]);
  };

  const removeItem = (index: number) => {
    setItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  };

  const handleAttachments = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) {
      return;
    }
    const validFiles: string[] = [];
    for (let i = 0; i < files.length; i += 1) {
      const file = files[i];
      if (defaultReimbursementConfig.allowedMimeTypes.includes(file.type)) {
        validFiles.push(file.name);
      }
    }
    setAttachments(validFiles);
  };

  const handleSubmit = () => {
    if (!month) {
      setMessage('Selecione o mês de referência.');
      return;
    }
    if (items.length === 0) {
      setMessage('Adicione ao menos um item de reembolso.');
      return;
    }
    if (attachmentsRequired && attachments.length === 0) {
      setMessage('Anexe pelo menos um comprovante para enviar a solicitação.');
      return;
    }
    const involvedCostCenters = Array.from(
      new Set(items.map((item) => item.costCenterId))
    );
    const notifications = involvedCostCenters.map((costCenterId) => {
      const costCenter = costCenters.find((center) => center.id === costCenterId);
      return costCenter
        ? `Notificar gestor ${costCenter.manager} (${costCenter.code})`
        : `Notificar gestor do centro ${costCenterId}`;
    });
    notifications.push(`Notificar ${financeAdmin.name} (${financeAdmin.email})`);

    const total = items.reduce((subtotal, item) => subtotal + item.amount, 0);

    if (editingRequestId) {
      // Atualizar solicitação existente
      const updatedRequest: ReimbursementRequest = {
        ...requests.find(r => r.id === editingRequestId)!,
        items,
        attachments,
        total,
        status: 'Em análise',
        history: [
          ...requests.find(r => r.id === editingRequestId)!.history,
          {
            id: `hist-${Date.now()}`,
            timestamp: new Date().toLocaleString('pt-BR'),
            actor: user.name,
            action: 'Solicitação reenviada após ajustes',
          }
        ]
      };

      setRequests((current) => current.map(r => r.id === editingRequestId ? updatedRequest : r));
      setSelectedRequestId(editingRequestId);
      setEditingRequestId(null);
      setMessage('Solicitação reenviada com sucesso. Status: Em análise.');
    } else {
      // Criar nova solicitação
      const newRequest: ReimbursementRequest = {
        id: `REQ-${Date.now()}`,
        createdAt: new Date().toLocaleDateString('pt-BR'),
        requestedBy: user.name,
        month,
        items,
        attachments,
        status: 'Em análise',
        costCenterIds: involvedCostCenters,
        notifications,
        total,
        history: [
          {
            id: `hist-${Date.now()}`,
            timestamp: new Date().toLocaleString('pt-BR'),
            actor: user.name,
            action: 'Solicitação enviada',
          }
        ]
      };

      setRequests((current) => [newRequest, ...current]);
      setSelectedRequestId(newRequest.id);
      setMessage('Solicitação enviada com sucesso. Status: Em análise.');
      setShowAllRequests(true);
      onTabChange(0);
    }

    setItems([initialItem()]);
    setAttachments([]);
    setGeneralNotes('');
  };

  const handleSaveDraft = () => {
    setMessage('Rascunho salvo com sucesso.');
  };

  const handleApplyFilters = () => {
    setAppliedFilters({
      status: filterStatus,
      dateFrom: filterDateFrom,
      dateTo: filterDateTo,
      project: filterProject
    });
    setShowAllRequests(true);
    setPage(1);
  };

  const handleCancel = () => {
    setItems([initialItem()]);
    setAttachments([]);
    setGeneralNotes('');
    setEditingRequestId(null);
    setMessage('');
  };

  const handleEditRequest = (requestId: string) => {
    const request = requests.find(r => r.id === requestId);
    if (request) {
      setEditingRequestId(requestId);
      setItems(request.items.map(item => ({ ...item })));
      setAttachments([...request.attachments]);
      setGeneralNotes('');
      setSelectedCostCenter(request.costCenterIds[0] || costCenters[0].id);
      setMonth(request.month);
      onTabChange(1);
      setMessage('');
    }
  };

  const filteredRequests = useMemo(() => {
    return userRequests.filter((request) => {
      if (appliedFilters.status !== 'Todos' && request.status !== appliedFilters.status) return false;
      if (appliedFilters.project !== 'Todos' && !request.items.some(item => item.projectId === appliedFilters.project)) return false;
      if (appliedFilters.dateFrom && parseDateString(request.createdAt) < new Date(appliedFilters.dateFrom)) return false;
      if (appliedFilters.dateTo && parseDateString(request.createdAt) > new Date(appliedFilters.dateTo)) return false;
      return true;
    });
  }, [userRequests, appliedFilters]);

  const totalPages = Math.max(1, Math.ceil(filteredRequests.length / pageSize));
  const paginatedRequests = filteredRequests.slice((page - 1) * pageSize, page * pageSize);

  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Minhas Solicitações</div>
        <div className="section-sub">Histórico das solicitações de reembolso em uma única base</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total solicitado</div>
            <div className="stat-val blue">R$ {requestStats.total.toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Aprovadas</div>
            <div className="stat-val green">{requestStats.approved}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Em análise</div>
            <div className="stat-val amber">{requestStats.pending}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Rejeitadas</div>
            <div className="stat-val red">{requestStats.rejected}</div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Filtros</div>
          <div className="form-row">
            <div className="form-group">
              <label>Status</label>
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                <option>Todos</option>
                <option>Em análise</option>
                <option>Aprovado</option>
                <option>Rejeitado</option>
                <option>Pago</option>
              </select>
            </div>
            <div className="form-group">
              <label>Projeto</label>
              <select value={filterProject} onChange={(e) => setFilterProject(e.target.value)}>
                <option>Todos</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>{project.name}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Data início</label>
              <input type="date" value={filterDateFrom} onChange={(e) => setFilterDateFrom(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Data fim</label>
              <input type="date" value={filterDateTo} onChange={(e) => setFilterDateTo(e.target.value)} />
            </div>
          </div>
          <div className="action-row">
            <button className="btn btn-primary" onClick={handleApplyFilters}>Filtrar</button>
          </div>
        </div>
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Data</th>
                  <th>Projetos / Centros</th>
                  <th>Itens</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                {filteredRequests.map((request) => (
                  <tr key={request.id}>
                    <td style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>{request.id}</td>
                    <td style={{ fontSize: '12px' }}>{request.createdAt}</td>
                    <td>
                      {Array.from(new Set(request.items.map((item) => {
                        const project = projects.find((projectItem) => projectItem.id === item.projectId);
                        return project ? `${project.name} / CC: ${item.costCenterId}` : `CC: ${item.costCenterId}`;
                      }))).map((label) => (
                        <div key={label} style={{ fontSize: '13px' }}>{label}</div>
                      ))}
                    </td>
                    <td>{request.items.length}</td>
                    <td style={{ fontWeight: '500' }}>R$ {request.total.toFixed(2)}</td>
                    <td>
                      <span className={`badge ${request.status === 'Aprovado' ? 'badge-approved' : request.status === 'Rejeitado' ? 'badge-rejected' : request.status === 'Pago' ? 'badge-paid' : 'badge-review'}`}>
                        {request.status}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-sm" onClick={() => setSelectedRequestId(request.id)}>Ver Detalhes</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  if (tab === 1) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Nova Solicitação de Reembolso</div>
        {editingRequestId && (
          <div style={{ marginBottom: '8px', padding: '8px 12px', backgroundColor: 'var(--color-warning-bg)', border: '1px solid var(--color-warning)', borderRadius: '4px', color: 'var(--color-warning-text)' }}>
            <strong>Editando solicitação:</strong> {editingRequestId}
          </div>
        )}
        <div className="section-sub">Preencha todos os dados em um único envio e anexe comprovantes</div>
        <div className="card">
          <div className="card-title">Dados do solicitante</div>
          <div className="form-row">
            <div className="form-group">
              <label>Funcionário</label>
              <input type="text" value={user.name} disabled style={{ opacity: '0.6' }} />
            </div>
            <div className="form-group">
              <label>Mês de referência</label>
              <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
            </div>
            <div className="form-group">
              <label>Centro de Custo Principal</label>
              <select value={selectedCostCenter} onChange={(e) => setSelectedCostCenter(Number(e.target.value))}>
                {costCenters.map((cc) => (
                  <option key={cc.id} value={cc.id}>{cc.code} - {cc.manager}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="form-row">
            <div className="form-group full">
              <label>Observações Gerais (opcional)</label>
              <textarea 
                value={generalNotes} 
                onChange={(e) => setGeneralNotes(e.target.value)} 
                placeholder="Adicione observações gerais sobre a solicitação..."
                rows={3}
              />
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Itens da planilha de reembolso</div>
          <div className="form-note">
            Cada item deve ser associado a um projeto/centro de custo. O envio único agrupa todos no mesmo pedido.
          </div>
          <div className="expense-header">
            <div className="col-label">Data</div>
            <div className="col-label">Tipo</div>
            <div className="col-label">Descrição</div>
            <div className="col-label">Projeto</div>
            <div className="col-label">Valor</div>
            <div></div>
          </div>
          {items.map((item, index) => {
            const costCenter = costCenters.find((center) => center.id === item.costCenterId);
            return (
              <div key={item.id} className="expense-row">
                <input type="date" value={item.date} onChange={(event) => handleItemChange(index, 'date', event.target.value)} />
                <select value={item.type} onChange={(event) => handleItemChange(index, 'type', event.target.value)}>
                  <option>Transporte</option>
                  <option>Refeição</option>
                  <option>Gráfica</option>
                  <option>Outros</option>
                </select>
                <input type="text" placeholder="Descrição" value={item.description} onChange={(event) => handleItemChange(index, 'description', event.target.value)} />
                <div style={{ display: 'grid', gap: '8px' }}>
                  <select value={item.projectId} onChange={(event) => handleItemChange(index, 'projectId', event.target.value)}>
                    {projects.map((project) => (
                      <option key={project.id} value={project.id}>{project.name}</option>
                    ))}
                  </select>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
                    CC: {costCenter?.code ?? item.costCenterId} — {costCenter?.manager}
                  </div>
                </div>
                <input type="number" placeholder="0,00" value={item.amount || ''} onChange={(event) => handleItemChange(index, 'amount', event.target.value)} />
                <button className="btn btn-sm" style={{ padding: '4px 6px', color: 'var(--color-text-secondary)' }} onClick={() => removeItem(index)}>✕</button>
              </div>
            );
          })}
          <button className="btn btn-sm" style={{ marginTop: '8px' }} onClick={addItem}>+ Adicionar item</button>
          <div className="divider"></div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Total:</span>
            <span style={{ fontSize: '20px', fontWeight: '500', color: 'var(--color-text-primary)' }}>R$ {items.reduce((sum, item) => sum + item.amount, 0).toFixed(2)}</span>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Comprovantes fiscais</div>
          <div className="form-note">{attachmentsRequired ? 'Anexo obrigatório para envio.' : 'Anexo opcional. Use para validar seus documentos.'}</div>
          <label htmlFor="comprovantes-input" className="upload-zone">
            <div className="upload-icon">📎</div>
            <div className="upload-text">Arraste os comprovantes aqui ou clique para selecionar</div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>PDF, JPG, PNG — máx. 5MB por arquivo</div>
          </label>
          <input type="file" multiple style={{ display: 'none' }} id="comprovantes-input" onChange={handleAttachments} />
          {attachments.length > 0 && (
            <div className="file-list">
              {attachments.map((fileName) => (
                <div key={fileName} className="file-badge">{fileName}</div>
              ))}
            </div>
          )}
        </div>
        {message && <div className="info-box"><p>{message}</p></div>}
        <div className="action-row">
          <button className="btn" onClick={handleSaveDraft}>Salvar Rascunho</button>
          <button className="btn btn-primary" onClick={handleSubmit}>Enviar Solicitação</button>
        </div>
      </div>
    );
  }

  if (tab === 2) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Detalhes da Solicitação</div>
        <div className="section-sub">Verifique status, centro de custo e notificações relacionadas</div>
        <div className="card">
          <div className="form-row">
            <div className="form-group full">
              <label>Selecionar solicitação</label>
              <select value={selectedRequest?.id ?? ''} onChange={(event) => setSelectedRequestId(event.target.value)}>
                {requests.map((request) => (
                  <option key={request.id} value={request.id}>{request.id} · {request.createdAt} · {request.status}</option>
                ))}
              </select>
            </div>
          </div>
          {selectedRequest ? (
            <>
              <div className="card-title">Cabeçalho da Solicitação</div>
              <div className="two-col">
                <div>
                  <strong>Solicitante:</strong> {selectedRequest.requestedBy}<br/>
                  <strong>Data de Abertura:</strong> {selectedRequest.createdAt}<br/>
                  <strong>Mês de Referência:</strong> {selectedRequest.month}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <strong>Status Atual:</strong> <span className={`badge ${selectedRequest.status === 'Aprovado' ? 'badge-approved' : selectedRequest.status === 'Rejeitado' ? 'badge-rejected' : selectedRequest.status === 'Pago' ? 'badge-paid' : 'badge-review'}`}>{selectedRequest.status}</span>
                </div>
              </div>
              
              <div className="card-title">Itens da Solicitação</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Data</th>
                      <th>Tipo</th>
                      <th>Descrição</th>
                      <th>Valor</th>
                      <th>Comprovante</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedRequest.items.map((item, index) => (
                      <tr key={index}>
                        <td>{item.date}</td>
                        <td>{item.type}</td>
                        <td>{item.description}</td>
                        <td>R$ {item.amount.toFixed(2)}</td>
                        <td>
                          {selectedRequest.attachments.length > 0 ? (
                            <span className="file-badge">📎 Anexado</span>
                          ) : (
                            <span style={{ color: 'var(--color-text-secondary)' }}>Não anexado</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge ${item.status === 'Aprovado' ? 'badge-approved' : item.status === 'Rejeitado' ? 'badge-rejected' : 'badge-review'}`}>
                            {item.status || 'Pendente'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="card-title">Timeline do Histórico</div>
              <div className="timeline">
                {selectedRequest.history.map((hist, index) => (
                  <div key={hist.id} className="tl-item">
                    <div className={`tl-dot ${index === 0 ? 'active' : ''}`}></div>
                    <div className="tl-time">{hist.timestamp}</div>
                    <div className="tl-label">
                      <strong>{hist.actor}:</strong> {hist.action}
                      {hist.comments && <div style={{ fontSize: '12px', marginTop: '4px', color: 'var(--color-text-secondary)' }}>{hist.comments}</div>}
                    </div>
                  </div>
                ))}
              </div>

              {selectedRequest.status === 'Aguardando ajustes' && (
                <div className="action-row">
                  <button className="btn btn-primary" onClick={() => handleEditRequest(selectedRequest.id)}>Editar e Reenviar</button>
                </div>
              )}
            </>
          ) : (
            <div className="info-box"><p>Não há solicitações selecionadas.</p></div>
          )}
        </div>
      </div>
    );
  }
};

export default ColaboradorPages;
