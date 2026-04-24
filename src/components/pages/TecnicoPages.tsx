import React from 'react';

interface TecnicoPagesProps {
  tab: number;
}

const TecnicoPages: React.FC<TecnicoPagesProps> = ({ tab }) => {
  if (tab === 0) {
    return (
      <div style={{ paddingTop: '16px' }}>
        <div className="section-title">Validar Conformidade</div>
        <div className="section-sub">Verificar informações e comprovantes antes de encaminhar ao gestor</div>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Para validar</div>
            <div className="stat-val amber">6</div>
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
        <div className="card">
          <div className="card-title">Solicitação #2024-018 — João Martins</div>
          <div className="two-col">
            <div>
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>Checklist de conformidade</div>
                {[
                  'Planilha preenchida corretamente',
                  'Comprovante fiscal anexado',
                  'Gasto dentro do prazo (90 dias)',
                  'Centro de custo válido',
                  'Descrição compatível com comprovante'
                ].map((item, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
                    <input type="checkbox" defaultChecked={i < 3} style={{ width: 'auto' }} />
                    <span style={{ fontSize: '13px', color: i < 3 ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>Comprovante anexado</div>
              <div style={{ background: 'var(--color-background-secondary)', border: '0.5px solid var(--color-border-tertiary)', borderRadius: 'var(--border-radius-md)', padding: '24px', textAlign: 'center' }}>
                <div style={{ fontSize: '24px', marginBottom: '6px' }}>📄</div>
                <div style={{ fontSize: '13px', fontWeight: '500' }}>comprovante_uber.pdf</div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>128 KB · PDF</div>
                <button className="btn btn-sm" style={{ marginTop: '8px' }}>Visualizar</button>
              </div>
              <div style={{ marginTop: '12px' }}>
                <label style={{ fontSize: '12px', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '4px' }}>Observação (opcional)</label>
                <textarea rows={3} placeholder="Apontar pendências ou observações..."></textarea>
              </div>
            </div>
          </div>
          <div className="action-row">
            <button className="btn btn-danger">Solicitar ajustes</button>
            <button className="btn btn-primary">Encaminhar ao gestor</button>
          </div>
        </div>
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
                  <td>João Martins</td>
                  <td>Ana Lima</td>
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
                <td>João Martins</td>
                <td>Ana Lima</td>
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