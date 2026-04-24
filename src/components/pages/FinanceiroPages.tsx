import React from 'react';

interface FinanceiroPagesProps {
  tab: number;
}

const FinanceiroPages: React.FC<FinanceiroPagesProps> = ({ tab }) => {
  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Aguardando Pagamento</div>
        <div className="section-sub">Solicitações aprovadas pelo gestor e validadas pelo técnico administrativo</div>
        <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card">
            <div className="stat-label">Total a pagar</div>
            <div className="stat-val blue">R$ 1.245,50</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Solicitações</div>
            <div className="stat-val amber">5</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Colaboradores</div>
            <div className="stat-val">3</div>
          </div>
        </div>
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
                <tr>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-018</td>
                  <td>
                    <div style={{ fontWeight: '500' }}>João Martins</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>joao.martins@empresa.com</div>
                  </td>
                  <td>Ana Lima</td>
                  <td style={{ fontWeight: '500', color: '#185FA5' }}>R$ 156,00</td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>16/04/2026</td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn btn-sm btn-primary">Agendar pgto.</button>
                      <button className="btn btn-sm">Ver comprov.</button>
                    </div>
                  </td>
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
              <tr>
                <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>#2024-015</td>
                <td>João Martins</td>
                <td style={{ fontWeight: '500' }}>R$ 89,50</td>
                <td style={{ fontSize: '12px' }}>05/04/2026</td>
                <td><button className="btn btn-sm">📁 Abrir</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FinanceiroPages;