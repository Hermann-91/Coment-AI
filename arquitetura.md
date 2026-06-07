# Especificação de Requisitos e Fluxo - Robo_marketing

Este documento descreve os requisitos, a pilha de tecnologia e o fluxo do **Robo_marketing**, um robô de automação inteligente voltado para a divulgação direcionada de produtos digitais no Instagram usando **Streamlit**.

---

## 🎯 Objetivo Geral do Projeto
Desenvolver um robô com interface gráfica web local (Streamlit) que permita ao usuário inserir suas credenciais do Instagram, o link do produto a ser promovido e uma descrição da proposta de valor. 
O robô deve:
1. Analisar o site do produto para extrair a persona e entender os problemas/dores que ele resolve.
2. Navegar no Instagram simulando comportamento humano real de forma automatizada.
3. Localizar perfis e posts de interesse do nicho correspondente.
4. Identificar dores específicas relatadas nos posts (ex: motoristas de aplicativo reclamando de tarifas).
5. Gerar e publicar um comentário personalizado relacionando a dor identificada ao produto que está sendo promovido.

---

## 🛠️ Stack Tecnológica
* **Interface Gráfica (GUI):** `Streamlit` (Página web local gerada 100% em Python, visual moderno e ágil).
* **Automação Web:** `Playwright` (Persistência de cookies e sessões de navegador local para simular navegação humana segura).
* **Inteligência Artificial (IA):** API do Google Gemini (para análise semântica da proposta do site, mapeamento de dores nos posts e geração contextual do comentário personalizado).
* **Web Scraping:** `BeautifulSoup4` + `requests` (para leitura e processamento rápidos do site do produto).
* **Testes:** `pytest` + `unittest.mock` (para validação segura e isolada do sistema).

---

## 🚀 Fluxo de Funcionamento Interno

```mermaid
graph TD
    A[Usuário abre o app Streamlit no navegador] --> B[Insere Credenciais, Link e Proposta]
    B --> C[Clique em 'Iniciar Automação']
    C --> D[Scraper analisa o Link do Produto]
    D --> E[Gemini API define a Persona e as Dores que o produto resolve]
    E --> F[Playwright abre o Instagram e faz Login]
    F --> G[Robo varre hashtags/perfis do Nicho]
    G --> H[Para cada post, Gemini analisa a legenda/contexto da imagem]
    H -->|Dor Identificada| I[Gemini gera comentário relacionando a dor ao produto]
    I --> J[Playwright insere o comentário no post]
    H -->|Nenhuma dor relevante| K[Pula o post]
    J --> L[Aguardando intervalo de tempo seguro - anti-ban]
    L --> G
```

---

## 🔒 Boas Práticas e Segurança (Anti-Ban)
* **Persistência de Cookies:** Usar perfis de contexto persistentes no Playwright para evitar logins repetitivos.
* **Intervalos Dinâmicos (Delays):** Intervalos de tempo aleatórios entre as interações humanas simuladas.
* **Limites Diários:** Restrição de quantidade máxima de comentários diários configuráveis pelo usuário na tela.
