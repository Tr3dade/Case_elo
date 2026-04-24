# Sistema de Reembolso - Fullstack

Este é um sistema completo de reembolso corporativo desenvolvido com React (frontend) e Node.js/Express (backend), integrado com Supabase como banco de dados.

## Estrutura do Projeto

```
case-elo/
├── backend/                 # API REST com Node.js/Express
│   ├── src/
│   │   ├── controllers/     # Handlers das rotas
│   │   ├── routes/         # Definição das rotas
│   │   ├── services/       # Lógica de negócio e integração Supabase
│   │   ├── types/          # Interfaces TypeScript
│   │   └── server.ts       # Ponto de entrada da aplicação
│   ├── package.json
│   └── .env               # Configurações do Supabase
├── frontend/               # Interface React/TypeScript
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── services/       # Cliente API
│   │   ├── types/          # Tipos TypeScript
│   │   └── data/           # Dados estáticos (projetos, centros de custo)
│   ├── package.json
│   └── .env               # URL da API
└── sistema_reembolso_prototipo.html  # Versão original (HTML puro)
```

## Funcionalidades

### Colaborador
- Criar solicitações de reembolso
- Visualizar histórico de solicitações
- Anexar comprovantes
- Acompanhar status das solicitações

### Gestor
- Aprovar/rejeitar solicitações
- Aprovação parcial de itens
- Solicitar ajustes nas solicitações
- Visualizar solicitações por centro de custo

### Técnico
- Validar solicitações (prazo, conformidade)
- Verificar anexos obrigatórios
- Identificar inconsistências

### Financeiro
- Agendar pagamentos
- Visualizar solicitações aprovadas
- Gerenciar fluxo de pagamentos

## Tecnologias Utilizadas

### Backend
- **Node.js** - Runtime JavaScript
- **Express.js** - Framework web
- **TypeScript** - Tipagem estática
- **Supabase** - Banco de dados e autenticação
- **CORS** - Controle de acesso cross-origin
- **Helmet** - Segurança HTTP

### Frontend
- **React 18** - Biblioteca UI
- **TypeScript** - Tipagem estática
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework CSS
- **Fetch API** - Cliente HTTP

## Configuração e Instalação

### Pré-requisitos
- Node.js 18+
- npm ou yarn
- Conta Supabase

### 1. Clonagem e Instalação

```bash
# Instalar dependências do backend
cd backend
npm install

# Instalar dependências do frontend
cd ../frontend
npm install
```

### 2. Configuração do Supabase

1. Crie um novo projeto no [Supabase](https://supabase.com)
2. Vá para Settings > API e copie:
   - Project URL
   - Anon/Public Key

### 3. Configuração do Backend

Edite o arquivo `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
PORT=3001
```

### 4. Configuração do Frontend

O arquivo `frontend/.env` já está configurado:

```env
VITE_API_URL=http://localhost:3001/api
```

### 5. Executar a Aplicação

```bash
# Terminal 1 - Backend
cd backend
npm run dev

# Terminal 2 - Frontend
cd frontend
npm run dev
```

A aplicação estará disponível em:
- Frontend: http://localhost:5173
- Backend API: http://localhost:3001

## Estrutura da API

### Endpoints

#### Reimbursements
- `GET /api/reimbursements` - Listar todas as solicitações
- `GET /api/reimbursements/:id` - Obter solicitação por ID
- `POST /api/reimbursements` - Criar nova solicitação
- `PUT /api/reimbursements/:id` - Atualizar solicitação
- `DELETE /api/reimbursements/:id` - Excluir solicitação

### Estrutura dos Dados

#### ReimbursementRequest
```typescript
{
  id: string;
  createdAt: string;
  requestedBy: string;
  month: string;
  items: ReimbursementItem[];
  attachments: string[];
  status: RequestStatus;
  costCenterIds: number[];
  total: number;
  history: ActionHistory[];
}
```

## Desenvolvimento

### Scripts Disponíveis

#### Backend
```bash
npm run dev      # Iniciar servidor em modo desenvolvimento
npm run build    # Compilar TypeScript
npm run start    # Executar versão compilada
```

#### Frontend
```bash
npm run dev      # Iniciar dev server
npm run build    # Build para produção
npm run preview  # Preview do build
npm run lint     # Executar ESLint
```

### Arquitetura

O projeto segue uma arquitetura em camadas:

1. **Routes** - Definem os endpoints HTTP
2. **Controllers** - Handlers das requisições
3. **Services** - Lógica de negócio e acesso aos dados
4. **Models/Types** - Definição dos dados e interfaces

### Próximos Passos

- [ ] Configurar tabelas no Supabase
- [ ] Implementar autenticação
- [ ] Adicionar validações mais robustas
- [ ] Implementar notificações por email
- [ ] Adicionar testes automatizados
- [ ] Configurar CI/CD

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.

## Tecnologias utilizadas

- React 18
- TypeScript
- Vite
- CSS Modules (estilos organizados)

## Estrutura de Componentes

- **App**: Componente principal que gerencia o estado global
- **Topbar**: Cabeçalho com logo e informações do usuário
- **RoleSelector**: Seletor de papel/função
- **NavTabs**: Navegação por abas
- **Content**: Container que renderiza as páginas específicas
- **Páginas**: Componentes específicos para cada papel (Colaborador, Gestor, etc.)

## Estilos

Os estilos estão organizados em:
- `index.css`: Variáveis CSS e estilos globais
- `App.css`: Estilos específicos da aplicação
- `Components.css`: Estilos dos componentes reutilizáveis