import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import datetime
import time
import plotly.express as px
import qrcode
from io import BytesIO
import os

# --- CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira linha de código) ---
st.set_page_config(page_title="MEO - Oficial", layout="wide", page_icon="🧭")

# --- FUNÇÕES DE APOIO ---
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1') if text else ""

def gerar_qr(dados):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(dados)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img_qr.save(buf, format="PNG")
    return buf

# --- CONEXÃO G-SHEETS ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# --- ESTADO DA SESSÃO (TIMER) ---
if 'rodando' not in st.session_state: st.session_state.rodando = False
if 'inicio_time' not in st.session_state: st.session_state.inicio_time = None

# --- MENU LATERAL (EVITA O ERRO REMOVECHILD) ---
st.sidebar.title("🧭 MEO - NAVEGAÇÃO")
pagina = st.sidebar.radio("Selecione a função:", ["📝 Registrar Estudo", "📑 Editar Planilha", "📊 Ver Gráficos"])

# --- CRONÔMETRO (Sempre visível no topo da barra lateral para estabilidade) ---
st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Cronômetro")
if not st.session_state.rodando:
    if st.sidebar.button("▶️ INICIAR", type="primary"):
        st.session_state.rodando = True
        st.session_state.inicio_time = time.time()
        st.rerun()
else:
    tempo_atual = int((time.time() - st.session_state.inicio_time) / 60)
    st.sidebar.metric("Tempo Decorrido", f"{tempo_atual} min")
    if st.sidebar.button("⏹️ PARAR"):
        st.session_state.rodando = False
        st.rerun()

# --- CONTEÚDO PRINCIPAL ---

if pagina == "📝 Registrar Estudo":
    st.header("📝 Novo Registro de Estudo")
    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            serie = st.selectbox("Série", ["1 EM", "2 EM", "3 EM"])
            disc = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História", "Geografia"])
            assunto = st.text_input("Assunto")
            # Câmera dentro do formulário para evitar bugs de renderização
            foto = st.camera_input("Capturar Foto")
            
        with c2:
            # Pega o tempo do cronômetro automaticamente se ele foi usado
            sugestao = 0
            if not st.session_state.rodando and st.session_state.inicio_time:
                sugestao = int((time.time() - st.session_state.inicio_time) / 60)
            
            tempo = st.number_input("Tempo Total (minutos)", min_value=0, value=max(sugestao, 0))
            foco = st.slider("Foco (1-10)", 1, 10, 8)
            pesquisa = st.text_area("Notas/Pesquisa")
            
        enviar = st.form_submit_button("🚀 SALVAR REGISTRO")

    if enviar:
        novo = {
            "Data": [datetime.datetime.now().strftime("%d/%m/%Y %H:%M")],
            "Serie": [serie], "Disciplina": [disc], "Assunto": [assunto],
            "Tempo": [tempo], "Foco": [foco], "Pesquisa": [pesquisa]
        }
        try:
            df_atual = conn.read(worksheet="Dados", ttl=0)
            df_final = pd.concat([df_atual, pd.DataFrame(novo)], ignore_index=True)
            conn.update(worksheet="Dados", data=df_final)
            st.success("✅ Salvo com sucesso!")
            
            # PDF com QR Code
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "MEO - COMPROVANTE", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            for k, v in novo.items():
                pdf.cell(200, 8, clean_text(f"{k}: {v[0]}"), ln=True)
            
            qr_buf = gerar_qr(f"MEO-VALID-{assunto}-{datetime.datetime.now().strftime('%Y%m%d')}")
            with open("qr_temp.png", "wb") as f: f.write(qr_buf.getbuffer())
            pdf.image("qr_temp.png", x=160, y=10, w=35)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF", pdf_bytes, "comprovante.pdf", "application/pdf")
            st.session_state.inicio_time = None # Reseta após salvar
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

elif pagina == "📑 Editar Planilha":
    st.header("📑 Editor de Planilha (Excel Style)")
    try:
        df_edit = conn.read(worksheet="Dados", ttl=0)
        df_editado = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Salvar Alterações"):
            conn.update(worksheet="Dados", data=df_editado)
            st.success("Planilha atualizada!")
    except:
        st.error("Erro ao carregar dados.")

elif pagina == "📊 Ver Gráficos":
    st.header("📊 Evolução dos Estudos")
    try:
        df_v = conn.read(worksheet="Dados", ttl=0)
        if not df_v.empty:
            df_v['Tempo'] = pd.to_numeric(df_v['Tempo'], errors='coerce')
            fig = px.bar(df_v, x="Disciplina", y="Tempo", color="Foco", title="Tempo por Disciplina")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
    except:
        st.error("Erro nos gráficos.")
