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

# --- CONEXÃO COM GOOGLE SHEETS (MÉTODO AUTOMÁTICO - EVITA ERRO DE ARGUMENTO) ---
try:
    # O Streamlit lerá automaticamente as credenciais da seção [connections.gsheets] nos Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("💡 Se o erro persistir, verifique se os Secrets estão formatados corretamente.")
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

# --- LÓGICA DO CRONOMETRO ---
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
        time.sleep(1) 
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
        assunto = st.text_input("Assunto Estudado", placeholder="Ex: Termodinâmica")

    with c2:
        sugestao_tempo = 0
        if not st.session_state.rodando and st.session_state.inicio_time is not None:
            sugestao_tempo = int((time.time() - st.session_state.inicio_time) / 60)
        
        tempo_final = st.number_input("Tempo Total (minutos)", min_value=0, value=max(sugestao_tempo, 0))
        foco_sel = st.slider("Nível de Foco (1-10)", 1, 10, 8)
        
    enviar = st.form_submit_button("🚀 FINALIZAR E SALVAR REGISTRO")

if enviar:
    if tempo_final <= 0:
        st.warning("O tempo deve ser maior que zero!")
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
            # 1. Tenta ler ou criar DataFrame vazio com as colunas certas
            try:
                df_atual = conn.read(worksheet="Dados", ttl=0)
            except:
                df_atual = pd.DataFrame(columns=novo_registro.keys())

            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            conn.update(worksheet="Dados", data=df_final)
            
            st.success("✅ Registro salvo na planilha!")
            st.session_state.inicio_time = None
            
            # Gerar PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 15, clean_text("MEO - COMPROVANTE"), ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            for k, v in novo_registro.items():
                pdf.cell(200, 10, clean_text(f"{k}: {v[0]}"), ln=True)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 BAIXAR PDF", pdf_bytes, f"MEO_{disc_sel}.pdf", "application/pdf")
            
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- DASHBOARD ---
st.markdown("---")
st.subheader("📊 Gráficos de Desempenho")

try:
    df_v = conn.read(worksheet="Dados", ttl=0)
    if not df_v.empty:
        df_v['Tempo'] = pd.to_numeric(df_v['Tempo'])
        
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            fig1 = px.pie(df_v, names='Disciplina', values='Tempo', title="Minutos por Matéria", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c_g2:
            df_v['Data_dt'] = pd.to_datetime(df_v['Data'], format="%d/%m/%Y %H:%M", errors='coerce')
            fig2 = px.bar(df_v, x='Data', y='Tempo', color='Disciplina', title="Histórico de Sessões")
            st.plotly_chart(fig2, use_container_width=True)
except:
    st.info("Gráficos aparecerão após o primeiro registro.")
