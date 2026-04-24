import React, { useMemo, useState } from 'react';
import {
  costCenters,
  defaultReimbursementConfig,
  financeAdmin,
  projects,
  ReimbursementItem,
  ReimbursementRequest,
  sampleRequests
} from '../../data/reimbursement';

interface ColaboradorPagesProps {
  tab: number;
}

const initialItem = (): ReimbursementItem => ({
  id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  date: '',
  type: 'Transporte',
  description: '',
  projectId: projects[0].id,
  costCenterId: projects[0].costCenterId,
  amount: 0
});

const ColaboradorPages: React.FC<ColaboradorPagesProps> = ({ tab }) => {
  const [requests, setRequests] = useState<ReimbursementRequest[]>(sampleRequests);
  const [items, setItems] = useState<ReimbursementItem[]>([initialItem()]);
  const [month, setMonth] = useState('2026-04');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [selectedRequestId, setSelectedRequestId] = useState<string>(sampleRequests[0]?.id || '');
  const [message, setMessage] = useState<string>('');

  const attachmentsRequired = defaultReimbursementConfig.attachmentsRequired;

  const selectedRequest = requests.find((request) => request.id === selectedRequestId) ?? requests[0];

  const requestStats = useMemo(() => {
    const total = requests.reduce((sum, request) => sum + request.total, 0);
    const approved = requests.filter((request) => request.status === 'Aprovado').length;
    const pending = requests.filter((request) => request.status === 'Enviado' || request.status === 'Em análise').length;
    const rejected = requests.filter((request) => request.status === 'Rejeitado').length;
    return { total, approved, pending, rejected };
  }, [requests]);

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
    const newRequest: ReimbursementRequest = {
      id: `REQ-${Date.now()}`,
      createdAt: new Date().toLocaleDateString('pt-BR'),
      requestedBy: 'João Martins',
      month,
      items,
      attachments,
      status: 'Enviado',
      costCenterIds: involvedCostCenters,
      notifications,
      total,
      history: [
        {
          id: `hist-${Date.now()}`,
          timestamp: new Date().toLocaleString('pt-BR'),
          actor: 'João Martins',
          action: 'Solicitação enviada',
        }
      ]
    };

    setRequests((current) => [newRequest, ...current]);
    setSelectedRequestId(newRequest.id);
    setItems([initialItem()]);
    setAttachments([]);
    setMessage('Solicitação enviada com sucesso. Notificações disparadas.');
  };

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
            <div className="stat-label">Pendentes</div>
            <div className="stat-val amber">{requestStats.pending}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Rejeitadas</div>
            <div className="stat-val red">{requestStats.rejected}</div>
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
                {requests.map((request) => (
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
                      <span className={`badge ${request.status === 'Aprovado' ? 'badge-approved' : request.status === 'Rejeitado' ? 'badge-rejected' : 'badge-review'}`}>
                        {request.status}
                      </span>
                    </td>
                    <td>
                      <button className="btn btn-sm" onClick={() => setSelectedRequestId(request.id)}>Ver</button>
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
        <div className="section-sub">Preencha todos os dados em um único envio e anexe comprovantes</div>
        <div className="card">
          <div className="card-title">Dados do solicitante</div>
          <div className="form-row">
            <div className="form-group">
              <label>Funcionário</label>
              <input type="text" value="João Martins" disabled style={{ opacity: '0.6' }} />
            </div>
            <div className="form-group">
              <label>Mês de referência</label>
              <input type="month" value={month} onChange={(event) => setMonth(event.target.value)} />
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
          <button className="btn" onClick={() => setMessage('Rascunho salvo localmente.')}>Salvar rascunho</button>
          <button className="btn btn-primary" onClick={handleSubmit}>Enviar solicitação</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ paddingTop: '16px' }}>
      <div className="section-title">Acompanhar Solicitação</div>
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
            <div className="card-title">Status atual</div>
            <div className="request-status">{selectedRequest.status}</div>
            <div className="two-col">
              <div className="card">
                <div className="card-title">Detalhes da solicitação</div>
                <table style={{ width: '100%', fontSize: '13px' }}>
                  <tbody>
                    <tr>
                      <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Solicitante</td>
                      <td style={{ textAlign: 'right' }}>{selectedRequest.requestedBy}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Mês</td>
                      <td style={{ textAlign: 'right' }}>{selectedRequest.month}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Itens</td>
                      <td style={{ textAlign: 'right' }}>{selectedRequest.items.length}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Total</td>
                      <td style={{ textAlign: 'right', fontWeight: '500' }}>R$ {selectedRequest.total.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Centros de custo</td>
                      <td style={{ textAlign: 'right' }}>{selectedRequest.costCenterIds.join(', ')}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="card">
                <div className="card-title">Notificações geradas</div>
                <div className="timeline">
                  {selectedRequest.notifications.map((note, index) => (
                    <div key={index} className="tl-item">
                      <div className={`tl-dot ${index === 0 ? 'active' : ''}`}></div>
                      <div className="tl-time">{index === 0 ? 'Agora' : 'Em breve'}</div>
                      <div className="tl-label">{note}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="info-box"><p>Não há solicitações selecionadas.</p></div>
        )}
      </div>
    </div>
  );
};

export default ColaboradorPages;
