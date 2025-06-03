# IA Cursos Online - Plataforma de Cursos de Inteligência Artificial

Este repositório contém uma plataforma completa de venda de cursos online focada em Inteligência Artificial aplicada ao mercado de trabalho, inspirada no layout e funcionalidades da Udemy.

## Sobre o Projeto

A plataforma oferece:
- Sistema de autenticação e perfis de usuário
- Catálogo de cursos com filtros e avaliações
- Área do aluno com progresso e certificados
- Sistema de pagamento integrado (Stripe e PagSeguro)
- Painel administrativo para controle de cursos, usuários e vendas
- Conteúdo didático para 6 cursos completos sobre IA

## Deploy no Render

### Passo 1: Conectar este repositório

1. Faça login na sua conta do [Render](https://dashboard.render.com/)
2. Clique em "New +" e selecione "Web Service"
3. Escolha "Connect a repository"
4. Selecione este repositório e clique em "Connect"

### Passo 2: Configurar o Web Service

Configure o serviço com os seguintes parâmetros:
- **Nome**: ia-cursos-online (ou outro nome de sua preferência)
- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn src.wsgi:app`
- **Plano**: Free (ou outro de sua preferência)

### Passo 3: Criar o Banco de Dados PostgreSQL

1. No dashboard do Render, clique em "New +" e selecione "PostgreSQL"
2. Configure seu banco de dados:
   - **Nome**: ia-cursos-db (ou outro nome de sua preferência)
   - **Plano**: Free

### Passo 4: Configurar Variáveis de Ambiente

1. No seu Web Service, vá para a aba "Environment"
2. Adicione as seguintes variáveis:
   - `SECRET_KEY`: uma string aleatória e segura (ex: `python -c "import secrets; print(secrets.token_hex(16))"`)
   - `DATABASE_URL`: use a Internal Database URL do seu PostgreSQL (disponível na página do seu banco de dados)
   - `FLASK_ENV`: production

### Passo 5: Inicializar o Banco de Dados

Após o primeiro deploy, acesse o shell do seu serviço:
1. Vá para a aba "Shell" do seu Web Service
2. Execute os seguintes comandos:
   ```
   flask --app src.migrations db init
   flask --app src.migrations db migrate -m "Migração inicial"
   flask --app src.migrations db upgrade
   ```

### Passo 6: Acessar o Site

Após o deploy, seu site estará disponível em:
- `https://seu-servico.onrender.com`

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
└── main.py         # Ponto de entrada da aplicação
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
