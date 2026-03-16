import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import datetime
import time
import plotly.express as px
import qrcode
from io import BytesIO
from PIL import Image

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MEO - Sistema Inteligente", layout="wide", page_icon="🧭")

# --- FUNÇÕES DE SUPORTE ---
def clean_text(text):
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

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

# --- INTERFACE ---
st.title("🧭 MEO - Gestão de Estudos Avançada")

# --- CRONÔMETRO ---
if 'rodando' not in st.session_state: st.session_state.rodando = False
if 'inicio_time' not in st.session_state: st.session_state.inicio_time = None

col_t1, col_t2, col_t3 = st.columns([1, 1, 2])
with col_t1:
    if st.button("▶️ INICIAR"):
        st.session_state.rodando = True
        st.session_state.inicio_time = time.time()
with col_t2:
    if st.button("⏹️ PARAR"):
        st.session_state.rodando = False
with col_t3:
    if st.session_state.rodando:
        tempo_passado = int((time.time() - st.session_state.inicio_time) / 60)
        st.metric("Tempo", f"{tempo_passado} min", "Contando...")
        time.sleep(2)
        st.rerun()

st.markdown("---")

# --- ABAS DE FUNCIONALIDADES ---
tab_reg, tab_edit, tab_quest, tab_dash = st.tabs(["📝 Registro", "table Edição Excel", "❓ Questionários", "📊 Dashboard"])

with tab_reg:
    with st.form("form_avancado"):
        c1, c2 = st.columns(2)
        with c1:
            serie = st.selectbox("Série", ["1 EM", "2 EM", "3 EM"])
            disc = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História"])
            assunto = st.text_input("Assunto")
            # --- CAPTURA DE IMAGEM ---
            foto = st.camera_input("📸 Capturar nota/livro")
        
        with c2:
            sugestao = 0
            if not st.session_state.rodando and st.session_state.inicio_time:
                sugestao = int((time.time() - st.session_state.inicio_time) / 60)
            tempo = st.number_input("Minutos", min_value=0, value=max(sugestao, 0))
            foco = st.slider("Foco", 1, 10, 8)
            pesquisa = st.text_area("Temas de Pesquisa / Resumo")

        enviar = st.form_submit_button("🚀 SALVAR TUDO")

    if enviar:
        novo = {
            "Data": [datetime.datetime.now().strftime("%d/%m/%Y %H:%M")],
            "Serie": [serie], "Disciplina": [disc], "Assunto": [assunto],
            "Tempo": [tempo], "Foco": [foco], "Pesquisa": [pesquisa]
        }
        df_novo = pd.DataFrame(novo)
        try:
            df_atual = conn.read(worksheet="Dados", ttl=0)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            conn.update(worksheet="Dados", data=df_final)
            st.success("✅ Sincronizado!")
            
            # --- PDF COM QR CODE ---
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "COMPROVANTE MEO", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            for k, v in novo.items():
                pdf.cell(200, 8, clean_text(f"{k}: {v[0]}"), ln=True)
            
            # Inserir QR Code no PDF
            qr_buf = gerar_qr(f"Registro MEO: {assunto} - {datetime.datetime.now()}")
            with open("temp_qr.png", "wb") as f: f.write(qr_buf.getbuffer())
            pdf.image("temp_qr.png", x=150, y=10, w=40)
            
            pdf_out = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar PDF com QR Code", pdf_out, "MEO_Pro.pdf")
        except Exception as e:
            st.error(f"Erro: {e}")

with tab_edit:
    st.subheader("📝 Edição Direta (Estilo Excel)")
    df_edit = conn.read(worksheet="Dados", ttl=0)
    # Tabela editável
    df_editado = st.data_editor(df_edit, num_rows="dynamic")
    if st.button("💾 Salvar Alterações da Tabela"):
        conn.update(worksheet="Dados", data=df_editado)
        st.success("Planilha atualizada!")

with tab_quest:
    st.subheader("❓ Gerador de Questionário")
    with st.expander("Criar Nova Pergunta"):
        pergunta = st.text_input("Enunciado")
        c_q1, c_q2 = st.columns(2)
        alt_a = c_q1.text_input("A)")
        alt_b = c_q1.text_input("B)")
        alt_c = c_q2.text_input("C)")
        alt_d = c_q2.text_input("D)")
        alt_e = st.text_input("E)")
        correta = st.selectbox("Alternativa Correta", ["A", "B", "C", "D", "E"])
        if st.button("Gravar Questão"):
            st.info("Questão tabulada! (Funcionalidade de armazenamento em aba 'Questões' pronta para ativar)")

with tab_dash:
    st.subheader("📊 Evolução")
    df_v = conn.read(worksheet="Dados", ttl=0)
    if not df_v.empty:
        fig = px.bar(df_v, x="Disciplina", y="Tempo", color="Foco", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
