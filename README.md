# IA Cursos Online - Plataforma de Cursos de Inteligência Artificial

Este repositório contém uma plataforma completa de venda de cursos online focada em Inteligência Artificial aplicada ao mercado de trabalho, inspirada no layout e funcionalidades da Udemy.

## Sobre o Projeto

A plataforma oferece:
- Sistema de autenticação e perfis de usuário
- Catálogo de cursos com filtros e avaliações
- Área do aluno com progresso e certificados
- Sistema de pagamento integrado (Stripe)
- Painel administrativo para controle de cursos, usuários e vendas
- Conteúdo didático para 6 cursos completos sobre IA

## Deploy no Netlify

### Passo 1: Conectar este repositório

1. Faça login na sua conta do [Netlify](https://app.netlify.com/)
2. Clique em "Add new site" e selecione "Import an existing project"
3. Escolha "Deploy with GitHub"
4. Selecione este repositório e clique em "Deploy site"

### Passo 2: Configurar Variáveis de Ambiente

1. No seu site Netlify, vá para Site settings > Environment variables
2. Adicione as seguintes variáveis:
   - `SUPABASE_URL`: URL do seu projeto Supabase
   - `SUPABASE_ANON_KEY`: Chave anônima do seu projeto Supabase
   - `JWT_SECRET`: Uma string aleatória e segura para tokens JWT

## Estrutura do Projeto

```
src/
├── models/         # Modelos de dados
│   ├── user.py     # Modelo de usuário
│   ├── course.py   # Modelo de curso
│   └── payment.py  # Modelo de pagamento
├── routes/         # Rotas da API
│   ├── auth.py     # Autenticação
│   ├── course.py   # Cursos
│   ├── payment.py  # Pagamentos
│   ├── content.py  # Conteúdo
│   └── admin.py    # Painel administrativo
├── static/         # Arquivos estáticos
└── main.py         # Ponto de entrada da aplicação Flask
```

## Desenvolvimento Local

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Inicie o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

## Customização

Para personalizar o site:
1. Modifique os arquivos HTML em `src/static/`
2. Atualize os estilos CSS em `src/static/css/`
3. Adicione novos cursos através do painel administrativo

## Integração com Frontend React/Next.js

Esta API está preparada para integração com frontend React ou Next.js:
1. O CORS está habilitado para permitir requisições de outros domínios
2. Todas as rotas da API começam com `/api/`
3. A autenticação é feita via JWT para facilitar a integração

## Suporte

Para dúvidas ou problemas, abra uma issue neste repositório.

---

Desenvolvido com ❤️ para o mercado de educação em IA