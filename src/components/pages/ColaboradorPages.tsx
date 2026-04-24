import React from 'react';

interface ColaboradorPagesProps {
  tab: number;
}

const ColaboradorPages: React.FC<ColaboradorPagesProps> = ({ tab }) => {
  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Minhas Solicitações</div>
        <div className="section-sub">Histórico de todas as suas solicitações de reembolso</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total solicitado</div>
            <div className="stat-val blue">R$ 1.847</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Aprovadas</div>
            <div className="stat-val green">3</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Pendentes</div>
            <div className="stat-val amber">1</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Rejeitadas</div>
            <div className="stat-val red">1</div>
          </div>
        </div>
        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Data</th>
                  <th>Projeto / Centro de custo</th>
                  <th>Tipo</th>
                  <th>Valor</th>
                  <th>Status</th>
                  <th>Ação</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>#2024-018</td>
                  <td style={{ fontSize: '12px' }}>15/04/2026</td>
                  <td>
                    <div style={{ fontSize: '13px' }}>Projeto Alpha</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>CC: 4521</div>
                  </td>
                  <td><span className="chip">Transporte</span></td>
                  <td style={{ fontWeight: '500' }}>R$ 156,00</td>
                  <td><span className="badge badge-review">Em validação</span></td>
                  <td><button className="btn btn-sm" onClick={() => {}}>Ver detalhes</button></td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>#2024-015</td>
                  <td style={{ fontSize: '12px' }}>02/04/2026</td>
                  <td>
                    <div style={{ fontSize: '13px' }}>Projeto Beta</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>CC: 3308</div>
                  </td>
                  <td><span className="chip">Refeição</span></td>
                  <td style={{ fontWeight: '500' }}>R$ 89,50</td>
                  <td><span className="badge badge-approved">Aprovado</span></td>
                  <td><button className="btn btn-sm">Ver</button></td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>#2024-011</td>
                  <td style={{ fontSize: '12px' }}>18/03/2026</td>
                  <td>
                    <div style={{ fontSize: '13px' }}>Projeto Alpha</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>CC: 4521</div>
                  </td>
                  <td><span className="chip">Gráfica</span></td>
                  <td style={{ fontWeight: '500' }}>R$ 320,00</td>
                  <td><span className="badge badge-partial">Parcialmente aprovado</span></td>
                  <td><button className="btn btn-sm">Ver</button></td>
                </tr>
                <tr>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>#2024-007</td>
                  <td style={{ fontSize: '12px' }}>05/02/2026</td>
                  <td>
                    <div style={{ fontSize: '13px' }}>Projeto Gamma</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>CC: 5102</div>
                  </td>
                  <td><span className="chip">Outros</span></td>
                  <td style={{ fontWeight: '500' }}>R$ 45,00</td>
                  <td><span className="badge badge-rejected">Rejeitado</span></td>
                  <td><button className="btn btn-sm">Ver</button></td>
                </tr>
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
        <div className="section-sub">Preencha os dados das despesas que deseja reembolsar</div>
        <div className="card">
          <div className="card-title">Dados do solicitante</div>
          <div className="form-row">
            <div className="form-group">
              <label>Funcionário</label>
              <input type="text" value="João Martins" disabled style={{ opacity: '0.6' }} />
            </div>
            <div className="form-group">
              <label>Mês de referência</label>
              <input type="month" value="2026-04" />
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Despesas</div>
          <div className="alert-box">
            <p>Gastos realizados há mais de 90 dias não podem ser reembolsados. Certifique-se de que todos os comprovantes estão anexados.</p>
          </div>
          <div className="expense-header">
            <div className="col-label">Data</div>
            <div className="col-label">Tipo (TD)</div>
            <div className="col-label">Descrição</div>
            <div className="col-label">Centro de custo</div>
            <div className="col-label">Valor (R$)</div>
            <div></div>
          </div>
          <div className="expense-row">
            <input type="date" value="2026-04-15" />
            <select>
              <option>Transporte</option>
              <option>Refeição</option>
              <option>Gráfica</option>
              <option>Outros</option>
            </select>
            <input type="text" placeholder="Descrição" />
            <input type="text" placeholder="CC (ex: 4521)" />
            <input type="number" placeholder="0,00" />
            <button className="btn btn-sm" style={{ padding: '4px 6px', color: 'var(--color-text-secondary)' }}>✕</button>
          </div>
          <div className="expense-row">
            <input type="date" />
            <select>
              <option>Transporte</option>
              <option>Refeição</option>
              <option>Gráfica</option>
              <option>Outros</option>
            </select>
            <input type="text" placeholder="Descrição" />
            <input type="text" placeholder="CC (ex: 4521)" />
            <input type="number" placeholder="0,00" />
            <button className="btn btn-sm" style={{ padding: '4px 6px', color: 'var(--color-text-secondary)' }}>✕</button>
          </div>
          <button className="btn btn-sm" style={{ marginTop: '8px' }}>+ Adicionar despesa</button>
          <div className="divider"></div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Total:</span>
            <span style={{ fontSize: '20px', fontWeight: '500', color: 'var(--color-text-primary)' }}>R$ 0,00</span>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Comprovantes fiscais</div>
          <div className="upload-zone">
            <div className="upload-icon">📎</div>
            <div className="upload-text">Arraste os comprovantes aqui ou clique para selecionar</div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>PDF, JPG, PNG — máx. 5MB por arquivo</div>
          </div>
        </div>
        <div className="action-row">
          <button className="btn">Salvar rascunho</button>
          <button className="btn btn-primary">Enviar solicitação</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ paddingTop: '16px' }}>
      <div className="section-title">Acompanhar Solicitação</div>
      <div className="section-sub">Solicitação #2024-018 — R$ 156,00</div>
      <div className="two-col">
        <div className="card">
          <div className="card-title">Detalhes</div>
          <table style={{ width: '100%', fontSize: '13px' }}>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Projeto</td>
              <td style={{ textAlign: 'right', fontWeight: '500' }}>Projeto Alpha</td>
            </tr>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Centro de custo</td>
              <td style={{ textAlign: 'right' }}>CC: 4521</td>
            </tr>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Tipo</td>
              <td style={{ textAlign: 'right' }}>Transporte</td>
            </tr>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Data da despesa</td>
              <td style={{ textAlign: 'right' }}>15/04/2026</td>
            </tr>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Valor</td>
              <td style={{ textAlign: 'right', fontWeight: '500', color: '#185FA5' }}>R$ 156,00</td>
            </tr>
            <tr>
              <td style={{ color: 'var(--color-text-secondary)', padding: '5px 0' }}>Status</td>
              <td style={{ textAlign: 'right' }}><span className="badge badge-review">Em validação</span></td>
            </tr>
          </table>
        </div>
        <div className="card">
          <div className="card-title">Linha do tempo</div>
          <div className="timeline">
            <div className="tl-item">
              <div className="tl-dot done"></div>
              <div className="tl-time">15/04 · 09:12</div>
              <div className="tl-label">Solicitação enviada</div>
              <div className="tl-desc">Enviada pelo colaborador</div>
            </div>
            <div className="tl-item">
              <div className="tl-dot active"></div>
              <div className="tl-time">15/04 · 10:05</div>
              <div className="tl-label">Em validação</div>
              <div className="tl-desc">Técnico administrativo verificando conformidade</div>
            </div>
            <div className="tl-item">
              <div className="tl-dot"></div>
              <div className="tl-time">Aguardando</div>
              <div className="tl-label">Aprovação do gestor</div>
              <div className="tl-desc">—</div>
            </div>
            <div className="tl-item">
              <div className="tl-dot"></div>
              <div className="tl-time">Aguardando</div>
              <div className="tl-label">Pagamento agendado</div>
              <div className="tl-desc">—</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ColaboradorPages;