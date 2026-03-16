import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import datetime
import time
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MEO - Meu Estudo Orientado", layout="wide", page_icon="🧭")

# --- FUNÇÃO PARA LIMPAR TEXTO DO PDF ---
def clean_text(text):
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- CONEXÃO COM GOOGLE SHEETS ---
try:
    creds_dict = dict(st.secrets["connections"]["gsheets"])
    tipo_conta = creds_dict.pop("type") if "type" in creds_dict else "service_account"
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].strip()
    
    conn = st.connection(
        "gsheets", 
        type=GSheetsConnection, 
        type_service_account=tipo_conta,
        **creds_dict
    )
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧭 MEO - Sistema de Gestão de Estudos")

# --- LÓGICA DO CRONÔMETRO (TIMER) ---
if 'rodando' not in st.session_state:
    st.session_state.rodando = False
if 'inicio_time' not in st.session_state:
    st.session_state.inicio_time = None

col_t1, col_t2, col_t3 = st.columns([1, 1, 2])

with col_t1:
    if st.button("▶️ INICIAR ESTUDO", type="primary"):
        st.session_state.rodando = True
        st.session_state.inicio_time = time.time()

with col_t2:
    if st.button("⏹️ PARAR/RESETAR"):
        st.session_state.rodando = False
        st.session_state.inicio_time = None

with col_t3:
    if st.session_state.rodando:
        tempo_passado = int((time.time() - st.session_state.inicio_time) / 60)
        st.metric("Tempo Decorrido", f"{tempo_passado} min", delta="Em progresso...")
        time.sleep(1) # Força atualização visual
        st.rerun()
    else:
        st.metric("Status", "Pausado", delta_color="off")

st.markdown("---")

# --- FORMULÁRIO DE ENTRADA ---
with st.form("form_estudo"):
    c1, c2 = st.columns(2)
    with c1:
        serie_sel = st.selectbox("Série", ["1 EM", "2 EM", "3 EM"])
        area_sel = st.selectbox("Área", ["Linguagens", "Matemática", "Ciências Natureza", "Ciências Humanas"])
        disc_sel = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História", "Geografia", "Sociologia", "Filosofia", "Inglês"])
        assunto = st.text_input("O que você estudou? (Assunto)", placeholder="Ex: Equações de 2º Grau")

    with c2:
        # Se o cronômetro foi usado, ele sugere o tempo. Se não, permite digitar.
        sugestao_tempo = 0
        if not st.session_state.rodando and st.session_state.inicio_time is not None:
            sugestao_tempo = int((time.time() - st.session_state.inicio_time) / 60)
        
        tempo_final = st.number_input("Tempo Total (minutos)", min_value=0, value=max(sugestao_tempo, 0))
        foco_sel = st.slider("Nível de Foco (1-10)", 1, 10, 8)
        
    enviar = st.form_submit_button("🚀 FINALIZAR E SALVAR REGISTRO")

if enviar:
    if tempo_final <= 0:
        st.warning("O tempo de estudo deve ser maior que zero!")
    else:
        novo_registro = {
            "Data": [datetime.datetime.now().strftime("%d/%m/%Y %H:%M")],
            "Serie": [str(serie_sel)],
            "Area": [str(area_sel)],
            "Disciplina": [str(disc_sel)],
            "Assunto": [str(assunto)],
            "Tempo": [int(tempo_final)],
            "Foco": [int(foco_sel)]
        }
        
        df_novo = pd.DataFrame(novo_registro)

        try:
            # Sincronização
            df_atual = conn.read(worksheet="Dados", ttl=0)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            conn.update(worksheet="Dados", data=df_final)
            
            st.success("✅ Estudo registrado com sucesso!")
            st.session_state.inicio_time = None # Reseta o timer após salvar
            
            # Gerar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 15, clean_text("MEO - COMPROVANTE DE ESTUDO"), ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            for k, v in novo_registro.items():
                pdf.cell(200, 10, clean_text(f"{k}: {v[0]}"), ln=True)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR COMPROVANTE PDF", pdf_bytes, f"MEO_{disc_sel}.pdf", "application/pdf")
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- DASHBOARD ---
st.markdown("---")
st.subheader("📊 Análise de Desempenho")

try:
    df_v = conn.read(worksheet="Dados", ttl=0)
    if not df_v.empty:
        df_v['Tempo'] = pd.to_numeric(df_v['Tempo'])
        
        tab1, tab2 = st.tabs(["Tempo por Matéria", "Evolução Diária"])
        with tab1:
            fig1 = px.sunburst(df_v, path=['Area', 'Disciplina'], values='Tempo', color='Foco', 
                               title="Distribuição de Estudos (Área > Disciplina)")
            st.plotly_chart(fig1, use_container_width=True)
        with tab2:
            df_v['Data_dt'] = pd.to_datetime(df_v['Data'], format="%d/%m/%Y %H:%M")
            fig2 = px.line(df_v, x='Data_dt', y='Tempo', color='Disciplina', markers=True, title="Minutos estudados ao longo do tempo")
            st.plotly_chart(fig2, use_container_width=True)
except:
    st.info("Aguardando registros para gerar gráficos...")
