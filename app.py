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

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DA SESSÃO (TIMER) ---
if 'rodando' not in st.session_state: st.session_state.rodando = False
if 'inicio_time' not in st.session_state: st.session_state.inicio_time = None

# --- BARRA LATERAL (NAVEGAÇÃO) ---
st.sidebar.title("🧭 MENU MEO")
escolha = st.sidebar.radio("Ir para:", ["📝 Registro", "📑 Edição Excel", "❓ Questionários", "📊 Dashboard"])

# --- CONTEÚDO PRINCIPAL ---
st.title("MEO - Gestão de Estudos Avançada")

# --- CRONÔMETRO (Sempre visível no topo) ---
with st.expander("⏱️ CRONÔMETRO DE ESTUDO", expanded=st.session_state.rodando):
    c_timer, c_status = st.columns([1, 1])
    with c_timer:
        if not st.session_state.rodando:
            if st.button("▶️ INICIAR SESSÃO", type="primary"):
                st.session_state.rodando = True
                st.session_state.inicio_time = time.time()
                st.rerun()
        else:
            if st.button("⏹️ PARAR CRONÔMETRO"):
                st.session_state.rodando = False
                st.rerun()
    with c_status:
        if st.session_state.rodando:
            minutos = int((time.time() - st.session_state.inicio_time) / 60)
            st.metric("Tempo Decorrido", f"{minutos} min")
            if st.button("🔄 Atualizar"): st.rerun()
        else:
            st.write("Cronômetro pausado.")

st.markdown("---")

# --- LÓGICA DAS PÁGINAS ---

if escolha == "📝 Registro":
    with st.form("form_registro"):
        st.subheader("Novo Registro de Estudo")
        c1, c2 = st.columns(2)
        with c1:
            serie = st.selectbox("Série", ["1 EM", "2 EM", "3 EM"])
            disc = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História", "Geografia", "Inglês"])
            assunto = st.text_input("Assunto Estudado")
            foto = st.camera_input("📸 Foto da anotação")
        
        with c2:
            sugestao = 0
            if not st.session_state.rodando and st.session_state.inicio_time:
                sugestao = int((time.time() - st.session_state.inicio_time) / 60)
            
            tempo = st.number_input("Tempo Total (minutos)", min_value=0, value=max(sugestao, 0))
            foco = st.slider("Nível de Foco", 1, 10, 8)
            pesquisa = st.text_area("Notas / Temas de Pesquisa")

        enviar = st.form_submit_button("🚀 SALVAR REGISTRO")

    if enviar:
        novo_registro = {
            "Data": [datetime.datetime.now().strftime("%d/%m/%Y %H:%M")],
            "Serie": [serie], "Disciplina": [disc], "Assunto": [assunto],
            "Tempo": [tempo], "Foco": [foco], "Pesquisa": [pesquisa]
        }
        try:
            df_atual = conn.read(worksheet="Dados", ttl=0)
            df_novo = pd.DataFrame(novo_registro)
            df_final = pd.concat([df_atual, df_novo], ignore_index=True)
            conn.update(worksheet="Dados", data=df_final)
            st.success("✅ Sincronizado com sucesso!")
            
            # Gerar PDF com QR Code
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "COMPROVANTE MEO", ln=True, align='C')
            pdf.ln(5)
            pdf.set_font("Arial", size=12)
            for k, v in novo_registro.items():
                pdf.cell(200, 8, clean_text(f"{k}: {v[0]}"), ln=True)
            
            # QR Code
            qr_buf = gerar_qr(f"MEO-VALID: {assunto} | {datetime.datetime.now()}")
            with open("temp_qr.png", "wb") as f: f.write(qr_buf.getbuffer())
            pdf.image("temp_qr.png", x=160, y=10, w=35)
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Baixar Comprovante PDF", pdf_bytes, f"MEO_{assunto}.pdf", "application/pdf")
            os.remove("temp_qr.png") # Limpa arquivo temporário
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

elif escolha == "📑 Edição Excel":
    st.subheader("📑 Editor de Planilha (Direto)")
    try:
        df_edit = conn.read(worksheet="Dados", ttl=0)
        df_editado = st.data_editor(df_edit, num_rows="dynamic", use_container_width=True)
        if st.button("💾 Salvar Alterações"):
            conn.update(worksheet="Dados", data=df_editado)
            st.success("Planilha atualizada no Google Sheets!")
    except:
        st.warning("Não foi possível carregar os dados para edição.")

elif escolha == "❓ Questionários":
    st.subheader("❓ Gerador de Questionário")
    with st.expander("Criar Nova Pergunta"):
        pergunta = st.text_input("Enunciado")
        c_q1, c_q2 = st.columns(2)
        alt_a = c_q1.text_input("A)")
        alt_b = c_q1.text_input("B)")
        alt_c = c_q2.text_input("C)")
        alt_d = c_q2.text_input("D)")
        alt_e = st.text_input("E)")
        correta = st.selectbox("Correta", ["A", "B", "C", "D", "E"])
        if st.button("Gravar Questão"):
            st.info("Funcionalidade de banco de questões em desenvolvimento.")

elif escolha == "📊 Dashboard":
    st.subheader("📊 Gráficos de Evolução")
    try:
        df_v = conn.read(worksheet="Dados", ttl=0)
        if not df_v.empty:
            df_v['Tempo'] = pd.to_numeric(df_v['Tempo'], errors='coerce')
            fig = px.bar(df_v, x="Disciplina", y="Tempo", color="Foco", title="Tempo por Disciplina (com Nível de Foco)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado para gerar gráficos.")
    except:
        st.error("Erro ao carregar gráficos.")
