import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import datetime
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="MEO - Meu Estudo Orientado", layout="wide", page_icon="🧭")

# --- CONEXÃO COM GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para limpar texto para o PDF (remove problemas de acento)
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# Estilização
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #00ffcc; color: black; font-weight: bold; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧭 MEO - Registro de Estudos")

# --- FORMULÁRIO ---
col1, col2 = st.columns(2)
with col1:
    serie_sel = st.selectbox("Serie", ["1 EM", "2 EM", "3 EM"])
    area_sel = st.selectbox("Area", ["Linguagens", "Matematica", "Ciencias Natureza", "Ciencias Humanas"])
    disc_sel = st.selectbox("Disciplina", ["Portugues", "Matematica", "Fisica", "Quimica", "Biologia", "Historia", "Geografia", "Sociologia", "Filosofia", "Ingles"])

with col2:
    tempo_sel = st.number_input("Tempo (minutos)", min_value=15, max_value=300, step=15)
    foco_sel = st.slider("Foco (1-10)", 1, 10, 8)

if st.button("🚀 SALVAR E GERAR COMPROVANTE"):
    novo_registro = {
        "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Serie": clean_text(serie_sel),
        "Area": clean_text(area_sel),
        "Disciplina": clean_text(disc_sel),
        "Tempo": int(tempo_sel),
        "Foco": int(foco_sel)
    }

    try:
        # Lendo a aba "Dados" (Renomeie sua planilha para Dados!)
        df_existente = conn.read(worksheet="Dados", ttl=0)
        df_final = pd.concat([df_existente, pd.DataFrame([novo_registro])], ignore_index=True)
        conn.update(worksheet="Dados", data=df_final)
        
        st.success("✅ Sincronizado com Google Sheets!")

        # Geração do PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "MEO - COMPROVANTE DE ESTUDO", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, clean_text(f"Data: {novo_registro['Data']}"), ln=True)
        pdf.cell(200, 10, clean_text(f"Disciplina: {novo_registro['Disciplina']}"), ln=True)
        pdf.cell(200, 10, clean_text(f"Tempo: {novo_registro['Tempo']} min"), ln=True)
        pdf.cell(200, 10, clean_text(f"Foco: {novo_registro['Foco']}/10"), ln=True)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 BAIXAR COMPROVANTE PDF",
            data=pdf_bytes,
            file_name=f"MEO_{disc_sel}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Erro: Verifique se a aba da planilha se chama 'Dados' e se e Editor.")
        st.info(f"Detalhe: {e}")

st.markdown("---")
st.subheader("📊 Dashboard")

try:
    df_visual = conn.read(worksheet="Dados", ttl=0)
    if not df_visual.empty:
        fig_pizza = px.pie(df_visual, names='Disciplina', title='Distribuicao por Materia')
        st.plotly_chart(fig_pizza, use_container_width=True)
except:
    st.info("Aguardando dados...")
