-- Sistema de Reembolso - Tabelas Supabase
-- Execute estes comandos no SQL Editor do Supabase

-- Tabela de solicitações de reembolso
CREATE TABLE IF NOT EXISTS reimbursements (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  requested_by TEXT NOT NULL,
  month TEXT NOT NULL,
  items JSONB NOT NULL DEFAULT '[]'::jsonb,
  attachments TEXT[] DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'Enviado',
  cost_center_ids INTEGER[] DEFAULT '{}',
  notifications TEXT[] DEFAULT '{}',
  total DECIMAL(10,2) NOT NULL DEFAULT 0,
  history JSONB NOT NULL DEFAULT '[]'::jsonb,
  payment_date DATE,
  archived_attachments TEXT[] DEFAULT '{}'
);

-- Políticas RLS (Row Level Security)
ALTER TABLE reimbursements ENABLE ROW LEVEL SECURITY;

-- Política para permitir leitura/escrita para usuários autenticados
-- (Ajuste conforme sua estratégia de autenticação)
CREATE POLICY "Enable all operations for authenticated users" ON reimbursements
  FOR ALL USING (auth.role() = 'authenticated');

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_reimbursements_status ON reimbursements(status);
CREATE INDEX IF NOT EXISTS idx_reimbursements_requested_by ON reimbursements(requested_by);
CREATE INDEX IF NOT EXISTS idx_reimbursements_month ON reimbursements(month);
CREATE INDEX IF NOT EXISTS idx_reimbursements_created_at ON reimbursements(created_at DESC);

-- Tabela de centros de custo (dados estáticos)
CREATE TABLE IF NOT EXISTS cost_centers (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  manager TEXT NOT NULL
);

-- Tabela de projetos (dados estáticos)
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  cost_center_id INTEGER REFERENCES cost_centers(id)
);

-- Inserir dados iniciais dos centros de custo
INSERT INTO cost_centers (id, code, name, manager) VALUES
  (1, 'CC001', 'Tecnologia da Informação', 'Ana Lima'),
  (2, 'CC002', 'Recursos Humanos', 'Carlos Silva'),
  (3, 'CC003', 'Financeiro', 'Maria Santos'),
  (4, 'CC004', 'Marketing', 'João Oliveira'),
  (5, 'CC005', 'Vendas', 'Paula Costa')
ON CONFLICT (id) DO NOTHING;

-- Inserir dados iniciais dos projetos
INSERT INTO projects (id, name, cost_center_id) VALUES
  ('PROJ001', 'Sistema de Gestão', 1),
  ('PROJ002', 'Recrutamento Digital', 2),
  ('PROJ003', 'Auditoria Financeira', 3),
  ('PROJ004', 'Campanha Marketing', 4),
  ('PROJ005', 'Expansão Vendas', 5),
  ('PROJ006', 'Modernização TI', 1),
  ('PROJ007', 'Treinamento RH', 2)
ON CONFLICT (id) DO NOTHING;