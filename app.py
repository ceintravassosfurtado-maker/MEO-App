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

# Estilização Customizada (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #00ffcc; color: black; font-weight: bold; border-radius: 10px; }
    .stSelectbox, .stNumberInput { background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧭 MEO - Sistema de Registro de Estudos")
st.markdown("---")

# --- FORMULÁRIO DE ENTRADA ---
col1, col2 = st.columns(2)

with col1:
    serie_sel = st.selectbox("Série", ["1ª Série EM", "2ª Série EM", "3ª Série EM"])
    area_sel = st.selectbox("Área do Conhecimento", ["Linguagens", "Matemática", "Ciências Natureza", "Ciências Humanas"])
    disc_sel = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História", "Geografia", "Sociologia", "Filosofia", "Inglês"])

with col2:
    tempo_sel = st.number_input("Tempo de Estudo (minutos)", min_value=15, max_value=300, step=15)
    foco_sel = st.slider("Nível de Foco (1-10)", 1, 10, 8)
    data_hoje = datetime.date.today().strftime("%d/%m/%Y")

st.markdown("---")

# --- BOTÃO SALVAR E GERAR PDF ---
if st.button("🚀 SALVAR REGISTRO E GERAR COMPROVANTE"):
    
    novo_registro = {
        "Data": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Serie": serie_sel,
        "Area": area_sel,
        "Disciplina": disc_sel,
        "Tempo": int(tempo_sel),
        "Foco": int(foco_sel)
    }

    try:
        # 1. Tenta ler e atualizar a planilha
        df_existente = conn.read(worksheet="Página1", ttl=0)
        df_final = pd.concat([df_existente, pd.DataFrame([novo_registro])], ignore_index=True)
        conn.update(worksheet="Página1", data=df_final)
        
        st.success("✅ Sincronizado com Google Sheets com sucesso!")

        # 2. Geração do PDF Real
        pdf = FPDF()
        pdf.add_page()
        
        # Cabeçalho do PDF
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "MEO - COMPROVANTE DE ESTUDO", ln=True, align='C')
        pdf.ln(10)
        
        # Conteúdo
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, f"Data/Hora: {novo_registro['Data']}", ln=True)
        pdf.cell(200, 10, f"Série: {novo_registro['Serie']}", ln=True)
        pdf.cell(200, 10, f"Disciplina: {novo_registro['Disciplina']}", ln=True)
        pdf.cell(200, 10, f"Tempo Dedicado: {novo_registro['Tempo']} minutos", ln=True)
        pdf.cell(200, 10, f"Nível de Foco: {novo_registro['Foco']}/10", ln=True)
        
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(200, 10, "Este documento comprova a realização da atividade de Estudo Orientado.", align='C')

        # Preparar arquivo para download
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 BAIXAR COMPROVANTE PDF",
            data=pdf_bytes,
            file_name=f"Comprovante_MEO_{disc_sel}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Erro na conexão! Verifique se a planilha está como 'Editor' e se o link nos Secrets está correto.")
        st.info(f"Detalhe técnico: {e}")

st.markdown("---")

# --- DASHBOARD DE ANÁLISE REAIS ---
st.subheader("📊 Dashboard de Desempenho")

try:
    # Lê os dados em tempo real para os gráficos
    df_visual = conn.read(worksheet="Página1", ttl=0)
    
    if not df_visual.empty:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            # Gráfico de Pizza: Distribuição por Disciplina
            fig_pizza = px.pie(df_visual, names='Disciplina', title='Matérias Mais Estudadas', hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)
            
        with col_graf2:
            # Gráfico de Barras: Tempo por Área
            df_area = df_visual.groupby('Area')['Tempo'].sum().reset_index()
            fig_barra = px.bar(df_area, x='Area', y='Tempo', title='Tempo Total por Área (min)', color='Area')
            st.plotly_chart(fig_barra, use_container_width=True)
    else:
        st.info("Os gráficos aparecerão aqui assim que você realizar o primeiro registro.")
except:
    st.warning("Aguardando entrada de dados para gerar as análises.")
