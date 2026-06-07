# Importância da Modularização, SOLID e Práticas de Testes no Projeto Robo_marketing (Streamlit)

Este documento detalha as decisões de design arquitetural para o **Robo_marketing**, focando na modularização física e lógica das pastas e arquivos usando o **Streamlit** no frontend e os serviços em Python no backend, seguindo as diretrizes de código limpo (Clean Code), os princípios **SOLID** e as melhores práticas de testes.

---

## 🏛️ Por que Modularizar no Streamlit?
Embora o Streamlit permita escrever todo o código da tela em um único arquivo, fazer isso em projetos reais gera códigos difíceis de manter. A modularização é vital para:
* **Separar Tela de Lógica:** A interface visual (widgets do Streamlit) deve apenas ler dados do usuário e disparar funções. Ela não deve conter a lógica de automação do Instagram nem as chamadas diretas ao Gemini.
* **Reutilização:** Componentes visuais como formulários ou visualizadores de logs podem ser isolados em funções ou módulos separados.

---

## 📐 Aplicando os Princípios SOLID na Estrutura

### 1. S - Single Responsibility Principle (Princípio da Responsabilidade Única)
Cada arquivo e pasta tem apenas uma função definida:
* A pasta `gui/` cuida apenas da interface e renderização do Streamlit.
* A pasta `src/` cuida da lógica pura (automação do Playwright, scraping e chamadas de IA do Gemini).
* A pasta `tests/` valida o código em isolamento total.

### 2. O - Open/Closed Principle (Princípio Aberto/Fechado)
* O robô de automação do Instagram é escrito como um serviço injetável. Se no futuro adicionarmos automação para outra plataforma, basta plugar um novo serviço sem reescrever a tela principal do Streamlit.

### 3. D - Dependency Inversion Principle (Princípio da Inversão de Dependências)
* A interface gráfica do Streamlit depende de abstrações de serviços (`services`), sem instanciar configurações pesadas de baixo nível diretamente nos arquivos de tela.

---

## 🧪 Práticas de Teste (Garantia de Qualidade)

Adotamos uma estratégia rígida de testes com o framework **`pytest`**:
1. **Mock de APIs e Navegador:** As chamadas à API do Gemini e as ações do Playwright no navegador são completamente mockadas nos testes usando `unittest.mock`. Isso garante testes rápidos e que não dependem de conexão com a internet ou login real.
2. **Separação de Testabilidade:** Como o código do Streamlit pode ser difícil de testar de forma automatizada, mantemos toda a lógica de negócio importante na pasta `services/`, o que permite testar 100% das regras de automação, scraping e IA de forma unitária rápida.

---

## 📂 Estrutura de Pastas Detalhada (Arquitetura Streamlit)

```text
Robo_marketing/
│
├── gui/                       # 🎨 INTERFACE GRÁFICA (Streamlit)
│   ├── __init__.py
│   ├── app.py                 # Ponto de entrada da GUI do Streamlit
│   └── components/            # Módulos visuais encapsulados
│       ├── __init__.py
│       ├── config_form.py     # Formulário de credenciais, link e proposta
│       └── log_viewer.py      # Área de logs e andamento do bot
│
├── src/                       # ⚙️ BACKEND (Lógica do Robô)
│   ├── __init__.py
│   │
│   ├── core/                  # Orquestração principal
│   │   ├── __init__.py
│   │   └── bot.py             # Fluxo de controle principal do robô
│   │
│   ├── services/              # Integrações externas e lógica de negócio
│   │   ├── __init__.py
│   │   ├── gemini_service.py  # Análise semântica e geração de comentários (IA)
│   │   ├── automation_service.py # Playwright para automação do Instagram
│   │   └── scraper_service.py # Web scraping do site do produto
│   │
│   └── utils/                 # Helpers e configurações do sistema
│       ├── __init__.py
│       ├── config.py          # Gerenciamento de chaves e variáveis de ambiente
│       └── logger.py          # Configurações de log em arquivo e console
│
├── tests/                     # 🧪 Testes Automatizados (pytest)
│   ├── __init__.py
│   ├── conftest.py            # Fixtures e mocks globais
│   ├── test_services/         # Testes de unidade dos serviços
│   │   ├── test_gemini.py
│   │   └── test_scraper.py
│   └── test_core/
│       └── test_bot.py
│
├── arquitetura.md             # Especificação técnica do robô
├── GEMINI.md                  # Este guia
└── requirements.txt           # Dependências do projeto (streamlit, playwright, etc.)
```
