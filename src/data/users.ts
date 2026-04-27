export interface User {
  username: string;
  password: string;
  role: string;
  name: string;
}

export const users: User[] = [
  // Colaboradores
  { username: 'joao.silva', password: 'senha123', role: 'colaborador', name: 'João Silva' },
  { username: 'maria.costa', password: 'senha123', role: 'colaborador', name: 'Maria Costa' },
  { username: 'carlos.santos', password: 'senha123', role: 'colaborador', name: 'Carlos Santos' },
  { username: 'ana.oliveira', password: 'senha123', role: 'colaborador', name: 'Ana Oliveira' },
  // Gestor
  { username: 'paulo.lima', password: 'senha123', role: 'gestor', name: 'Paulo Lima' },
  // Técnico Administrativo
  { username: 'fernanda.souza', password: 'senha123', role: 'tecnico', name: 'Fernanda Souza' },
  // Financeiro
  { username: 'roberto.almeida', password: 'senha123', role: 'financeiro', name: 'Roberto Almeida' },
  // Admin
  { username: 'admin.user', password: 'senha123', role: 'admin', name: 'Admin User' }
];