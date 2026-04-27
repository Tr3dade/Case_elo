# Sistema de Reembolso - Protótipo

Este é um protótipo de sistema de gerenciamento de reembolsos desenvolvido em React com TypeScript e Vite.

## Estrutura do Projeto

```
src/
├── components/
│   ├── pages/
│   │   ├── ColaboradorPages.tsx
│   │   ├── GestorPages.tsx
│   │   ├── TecnicoPages.tsx
│   │   └── FinanceiroPages.tsx
│   ├── Content.tsx
│   ├── NavTabs.tsx
│   ├── RoleSelector.tsx
│   └── Topbar.tsx
├── data/
│   └── roles.ts
├── styles/
│   ├── App.css
│   └── Components.css
├── App.tsx
├── index.css
└── main.tsx
```

## Funcionalidades

O sistema permite visualizar diferentes perspectivas do processo de reembolso:

- **Colaborador**: Criar solicitações, acompanhar status
- **Gestor**: Aprovar ou rejeitar solicitações
- **Técnico Administrativo**: Validar conformidade dos documentos
- **Financeiro**: Processar pagamentos

## Logins Disponíveis

Para testar o sistema, utilize os seguintes logins:

### Colaboradores
- **Nome:** João Silva | **Usuário:** joao.silva | **Senha:** senha123
- **Nome:** Maria Costa | **Usuário:** maria.costa | **Senha:** senha123
- **Nome:** Carlos Santos | **Usuário:** carlos.santos | **Senha:** senha123
- **Nome:** Ana Oliveira | **Usuário:** ana.oliveira | **Senha:** senha123

### Outros Perfis
- **Nome:** Paulo Lima | **Usuário:** paulo.lima | **Senha:** senha123 (Gestor)
- **Nome:** Fernanda Souza | **Usuário:** fernanda.souza | **Senha:** senha123 (Técnico Administrativo)
- **Nome:** Roberto Almeida | **Usuário:** roberto.almeida | **Senha:** senha123 (Financeiro)
- **Nome:** Admin User | **Usuário:** admin.user | **Senha:** senha123 (Admin)

## Como executar

1. Instalar dependências:
   ```bash
   npm install
   ```

2. Executar o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

3. Abrir http://localhost:5173/ no navegador

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