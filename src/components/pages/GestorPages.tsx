import React from 'react';

interface GestorPagesProps {
  tab: number;
}

const GestorPages: React.FC<GestorPagesProps> = ({ tab }) => {
  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Pendentes de Aprovação</div>
        <div className="section-sub">Solicitações que aguardam sua avaliação</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Pendentes</div>
            <div className="stat-val amber">4</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Valor total pendente</div>
            <div className="stat-val blue">R$ 2.340</div>
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
                <tr>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-018</td>
                  <td>
                    <div style={{ fontSize: '13px', fontWeight: '500' }}>João Martins</div>
                  </td>
                  <td><span className="chip">CC: 4521</span></td>
                  <td><span className="chip">Transporte</span></td>
                  <td style={{ fontWeight: '500' }}>R$ 156,00</td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>15/04/2026</td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn btn-sm btn-success">Aprovar</button>
                      <button className="btn btn-sm btn-danger">Rejeitar</button>
                      <button className="btn btn-sm">Ver</button>
                    </div>
                  </td>
                </tr>
                {/* Adicionar mais linhas conforme necessário */}
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
                <tr>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-015</td>
                  <td>João Martins</td>
                  <td style={{ fontWeight: '500' }}>R$ 89,50</td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>03/04/2026</td>
                  <td><span className="badge badge-paid">Pago</span></td>
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
              <tr>
                <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-007</td>
                <td>João Martins</td>
                <td style={{ fontWeight: '500' }}>R$ 45,00</td>
                <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Despesa não relacionada ao projeto</td>
                <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>07/02/2026</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GestorPages;