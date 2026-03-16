import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import time

# Configuração da página - MANTENHA NO TOPO
st.set_page_config(page_title="MEO - Sistema de Questões", layout="wide")

# Título e Estilo
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO COM GOOGLE SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Erro na conexão com o Banco de Dados. Verifique os Secrets.")
    st.stop()

# --- BARRA LATERAL (SIDEBAR) - EVITA O ERRO DE NODE ---
with st.sidebar:
    st.title("🚀 MEO - Menu")
    menu = st.radio("Navegação:", ["📝 Lançar Questões", "📊 Ver Desempenho", "⏱️ Cronômetro"])
    
    st.divider()
    
    # CRONÔMETRO NA SIDEBAR (Onde ele não quebra o app)
    if menu == "⏱️ Cronômetro":
        st.subheader("⏱️ Timer de Estudo")
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.start_time = 0

        col1, col2 = st.columns(2)
        if col1.button("Iniciar"):
            st.session_state.start_time = time.time()
            st.session_state.timer_running = True
        if col2.button("Parar"):
            st.session_state.timer_running = False
            st.success("Tempo pausado!")

        if st.session_state.timer_running:
            placeholder = st.empty()
            while st.session_state.timer_running:
                elapsed = time.time() - st.session_state.start_time
                mins, secs = divmod(int(elapsed), 60)
                placeholder.metric("Tempo decorrido", f"{mins:02d}:{secs:02d}")
                time.sleep(1)

# --- CONTEÚDO PRINCIPAL ---
if menu == "📝 Lançar Questões":
    st.header("📝 Cadastro de Questões")
    with st.form("questoes_form", clear_on_submit=True):
        materia = st.selectbox("Matéria", ["Português", "Matemática", "Direito", "Informática"])
        acertos = st.number_input("Quantidade de Acertos", min_value=0, step=1)
        erros = st.number_input("Quantidade de Erros", min_value=0, step=1)
        data = st.date_input("Data", datetime.now())
        
        submit = st.form_submit_button("Salvar na Planilha")
        
        if submit:
            try:
                # Criar DataFrame com os dados
                df_novo = pd.DataFrame([{
                    "Data": data.strftime("%d/%m/%Y"),
                    "Materia": materia,
                    "Acertos": acertos,
                    "Erros": erros,
                    "Total": acertos + erros
                }])
                
                # Ler dados existentes
                df_antigo = conn.read()
                df_final = pd.concat([df_antigo, df_novo], ignore_index=True)
                
                # Salvar de volta
                conn.update(data=df_final)
                st.success("Dados salvos com sucesso!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

elif menu == "📊 Ver Desempenho":
    st.header("📊 Seu Desempenho")
    try:
        df = conn.read()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            # Gráfico Simples
            st.bar_chart(df.set_index("Materia")[["Acertos", "Erros"]])
        else:
            st.info("Nenhum dado encontrado na planilha.")
    except:
        st.warning("Ainda não existem dados lançados.")
