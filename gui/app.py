import sys
from pathlib import Path

# Adiciona a raiz do projeto (um nível acima da pasta gui/) ao PYTHONPATH em tempo de execução
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import asyncio
from src.core.bot import MarketingBot
from src.services.scraper_service import ScraperService
from src.services.api.gemini import GeminiService

# Configurações de layout da página do Streamlit
st.set_page_config(
    page_title="Coment-AI - Robô de Marketing",
    page_icon="🤖",
    layout="centered"
)

# Estilo para os botões e espaçamentos
st.markdown("""
    <style>
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Coment-AI")
st.subheader("Divulgação Inteligente no Instagram direcionada por IA")

# Inicializa o estado dos logs, do histórico de comentários e do estado de execução do bot
if "logs" not in st.session_state:
    st.session_state.logs = []
if "history" not in st.session_state:
    st.session_state.history = []
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

# Estados novos para fluxo em duas etapas
if "product_mapped" not in st.session_state:
    st.session_state.product_mapped = False
if "persona" not in st.session_state:
    st.session_state.persona = ""
if "dores" not in st.session_state:
    st.session_state.dores = ""
if "exclusoes" not in st.session_state:
    st.session_state.exclusoes = ""

# Definição das Abas Visuais
tab1, tab2 = st.tabs(["🚀 Automação e Logs", "📊 Histórico de Comentários"])

with tab1:
    st.markdown("""
    Este robô analisa o site do seu produto digital, identifica dores de potenciais clientes no Instagram
    e realiza comentários automatizados e personalizados relacionando a dor do cliente ao seu produto.
    """)

    # Painel de Credenciais e Acessos
    st.write("### 🔑 Credenciais e Acessos")
    col1, col2 = st.columns(2)
    with col1:
        instagram_user = st.text_input("Usuário do Instagram", placeholder="seu_usuario (opcional para histórico de cookies)", value="")
    with col2:
        gemini_key = st.text_input("Chave de API do Gemini", type="password", placeholder="Chave da API (ou deixe vazio se configurado no .env)", value="")

    # Configurações do Produto
    st.write("### 📦 Informações do Produto")
    product_link = st.text_input("Link do Produto (URL do Site)", placeholder="https://meuproduto.com.br")
    product_description = st.text_area(
        "Proposta de Valor / Dor que resolve", 
        placeholder="Ex: Planilha de gestão financeira para motoristas de aplicativo que ajuda a calcular o lucro real e economizar combustível."
    )

    # Botão para Etapa 1: Mapear Regras da IA
    st.write("")
    map_rules_btn = st.button("🔍 Etapa 1: Mapear Proposta de Valor e Regras da IA", use_container_width=True)

    if map_rules_btn:
        if not product_description:
            st.error("Por favor, digite a Proposta de Valor / Dor que resolve antes de mapear!")
        else:
            with st.spinner("Analisando o produto e gerando regras de inteligência..."):
                # Realiza scrape do site
                website_text = ""
                if product_link:
                    scraper = ScraperService()
                    website_text = scraper.scrape_website(product_link)

                # Roda mapeamento com o Gemini
                gemini_service = GeminiService(api_key=gemini_key)
                analysis = gemini_service.analyze_product(product_description, website_text)

                # Salva os resultados no session_state para edição na tela
                st.session_state.persona = analysis.get("persona", "Motoristas de aplicativo")
                st.session_state.dores = "\n".join(analysis.get("dores", [product_description]))
                st.session_state.exclusoes = "\n".join(analysis.get("exclusoes", ["Anúncios de venda de carros", "Promoções comerciais"]))
                st.session_state.product_mapped = True
                st.success("Mapeamento gerado com sucesso! Revise as regras abaixo:")

    # Se o produto já foi mapeado, exibe os campos de edição e as regras da IA
    if st.session_state.product_mapped:
        st.write("---")
        st.write("### 📝 Ajuste e Revisão de Regras da IA (Opcional)")
        st.info("Você pode ajustar os textos abaixo para deixar a IA mais cirúrgica antes de iniciar o robô!")
        
        editable_persona = st.text_input("Persona Alvo", value=st.session_state.persona)
        editable_dores = st.text_area("Regras Positivas (Dores a buscar - uma por linha)", value=st.session_state.dores, height=120)
        editable_exclusoes = st.text_area("Regras Negativas (O que ignorar/pular - uma por linha)", value=st.session_state.exclusoes, height=120)

        st.write("---")
        # Configurações de Busca e Nicho
        st.write("### 🎯 Nicho e Limites do Robô")
        niche_tags_input = st.text_input("Hashtags Alvo (separadas por vírgula)", placeholder="motoristasdeaplicativo, uberbr, 99pop")
        
        col_lim1, col_lim2 = st.columns(2)
        with col_lim1:
            limit_posts_tag = st.number_input("Limite de posts analisados por Hashtag", min_value=1, max_value=20, value=5)
        with col_lim2:
            limit_total_comments = st.number_input("Limite de comentários por execução (segurança)", min_value=1, max_value=50, value=3)

        st.write("---")

        # Contêiner dinâmico reservado para os logs de execução na tela
        log_placeholder = st.empty()

        # Se existirem logs de execuções anteriores, exibe-os
        if st.session_state.logs:
            log_placeholder.code("\n".join(st.session_state.logs), language="bash")

        # Função de callback de logs
        def update_logs(message: str):
            st.session_state.logs.append(message)
            log_placeholder.code("\n".join(st.session_state.logs), language="bash")

        # Função de callback do histórico de comentários
        def add_comment_to_history(comment_data: dict):
            st.session_state.history.append(comment_data)

        # Botões de Controle da Etapa 2
        col_start, col_stop = st.columns(2)

        with col_start:
            start_btn = st.button("🚀 Etapa 2: Iniciar Automação", use_container_width=True, disabled=st.session_state.bot_running)

        with col_stop:
            stop_btn = st.button("⏹️ Parar Automação", use_container_width=True, disabled=not st.session_state.bot_running)

        # Tratamento da inicialização da automação
        if start_btn:
            if not product_link:
                st.error("Por favor, preencha o Link do Produto!")
            elif not niche_tags_input:
                st.error("Por favor, digite ao menos uma Hashtag Alvo!")
            else:
                st.session_state.bot_running = True
                st.session_state.logs = []  # Limpa o histórico de logs anteriores
                update_logs("🤖 Inicializando o Coment-AI...")

                # Cria a estrutura de análise revisada
                revised_analysis = {
                    "persona": editable_persona,
                    "dores": [d.strip() for d in editable_dores.split("\n") if d.strip()],
                    "exclusoes": [e.strip() for e in editable_exclusoes.split("\n") if e.strip()]
                }

                # Cria a instância do bot
                bot = MarketingBot(gemini_api_key=gemini_key)
                st.session_state.bot_instance = bot

                try:
                    # Divide as hashtags informadas removendo espaços extras
                    tags = [tag.strip() for tag in niche_tags_input.split(",") if tag.strip()]
                    
                    # Executa o loop assíncrono do bot no orquestrador
                    asyncio.run(bot.run(
                        instagram_user=instagram_user,
                        product_link=product_link,
                        product_analysis=revised_analysis,
                        niche_tags=tags,
                        limit_per_tag=int(limit_posts_tag),
                        limit_comments=int(limit_total_comments),
                        log_callback=update_logs,
                        comment_callback=add_comment_to_history
                    ))
                except Exception as e:
                    update_logs(f"❌ Ocorreu um erro no loop principal: {e}")
                finally:
                    st.session_state.bot_running = False
                    st.rerun()

        # Tratamento da interrupção manual
        if stop_btn:
            if "bot_instance" in st.session_state and st.session_state.bot_instance:
                st.session_state.bot_instance.stop()
                update_logs("⏹️ Enviando sinal de parada para o navegador do robô...")
            st.session_state.bot_running = False
            st.rerun()

with tab2:
    st.write("### 📊 Histórico de Comentários Publicados nesta Sessão")
    if not st.session_state.history:
        st.info("Nenhum comentário foi enviado ainda nesta sessão.")
    else:
        # Exibe em formato de cards ordenados do mais recente para o mais antigo
        for idx, item in enumerate(reversed(st.session_state.history)):
            with st.container(border=True):
                col_card1, col_card2 = st.columns([4, 1])
                with col_card1:
                    st.markdown(f"💬 **Comentário #{len(st.session_state.history) - idx}**")
                    st.write(f"\"{item['comentario']}\"")
                with col_card2:
                    st.link_button("🔗 Ver Post", item['url'], use_container_width=True)
