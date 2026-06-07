import sys
from pathlib import Path

# Adiciona a raiz do projeto (um nível acima da pasta gui/) ao PYTHONPATH em tempo de execução
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import asyncio
from src.core.bot import MarketingBot

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

st.markdown("""
Este robô analisa o site do seu produto digital, identifica dores de potenciais clientes no Instagram
e realiza comentários automatizados e personalizados relacionando a dor do cliente ao seu produto.
""")

# Inicializa o estado dos logs e o estado de execução do bot na sessão do Streamlit
if "logs" not in st.session_state:
    st.session_state.logs = []
if "bot_running" not in st.session_state:
    st.session_state.bot_running = False

# Painel de Credenciais e Acessos (Removida a senha do Instagram por motivos de segurança)
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

# Configurações de Busca e Nicho
st.write("### 🎯 Nicho e Busca")
niche_tags_input = st.text_input("Hashtags Alvo (separadas por vírgula)", placeholder="motoristasdeaplicativo, uberbr, 99pop")

st.write("---")

# Contêiner dinâmico reservado para os logs de execução na tela
log_placeholder = st.empty()

# Se existirem logs de execuções anteriores, exibe-os
if st.session_state.logs:
    log_placeholder.code("\n".join(st.session_state.logs), language="bash")

# Função de callback que o orquestrador do bot chamará para imprimir logs na tela em tempo real
def update_logs(message: str):
    st.session_state.logs.append(message)
    # Atualiza dinamicamente o bloco de código de log na interface gráfica
    log_placeholder.code("\n".join(st.session_state.logs), language="bash")

# Botões de Controle
col_start, col_stop = st.columns(2)

with col_start:
    start_btn = st.button("🚀 Iniciar Automação", use_container_width=True, disabled=st.session_state.bot_running)

with col_stop:
    stop_btn = st.button("⏹️ Parar Automação", use_container_width=True, disabled=not st.session_state.bot_running)

# Tratamento da inicialização da automação
if start_btn:
    if not product_link:
        st.error("Por favor, preencha o Link do Produto!")
    else:
        st.session_state.bot_running = True
        st.session_state.logs = []  # Limpa o histórico de logs anteriores
        update_logs("🤖 Inicializando o Coment-AI...")

        # Cria a instância do bot
        bot = MarketingBot(gemini_api_key=gemini_key)
        st.session_state.bot_instance = bot

        try:
            # Divide as hashtags informadas removendo espaços extras
            tags = [tag.strip() for tag in niche_tags_input.split(",") if tag.strip()]
            
            # Executa o loop assíncrono do bot no orquestrador (sem transmitir a senha)
            asyncio.run(bot.run(
                instagram_user=instagram_user,
                product_link=product_link,
                product_description=product_description,
                niche_tags=tags,
                log_callback=update_logs
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
