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

# Função para evitar erros de acentuação no PDF
def clean_text(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# Estilização CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; background-color: #00ffcc; color: black; font-weight: bold; border-radius: 10px; height: 3em; }
    div[data-baseweb="select"] > div { background-color: #262730; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧭 MEO - Sistema de Gestão de Estudos")
st.write(f"Data de hoje: {datetime.date.today().strftime('%d/%m/%Y')}")

# --- FORMULÁRIO DE ENTRADA ---
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        serie_sel = st.selectbox("Série", ["1 EM", "2 EM", "3 EM"])
        area_sel = st.selectbox("Área", ["Linguagens", "Matemática", "Ciências Natureza", "Ciências Humanas"])
        disc_sel = st.selectbox("Disciplina", ["Português", "Matemática", "Física", "Química", "Biologia", "História", "Geografia", "Sociologia", "Filosofia", "Inglês"])

    with col2:
        tempo_sel = st.number_input("Tempo de Estudo (minutos)", min_value=15, max_value=300, step=15, value=45)
        foco_sel = st.slider("Nível de Foco (1-10)", 1, 10, 8)

st.markdown("---")

# --- BOTÃO SALVAR ---
if st.button("🚀 SALVAR REGISTRO E GERAR COMPROVANTE"):
    # Organiza os dados em um formato que o Pandas entende perfeitamente
    novo_registro_dict = {
        "Data": [datetime.datetime.now().strftime("%d/%m/%Y %H:%M")],
        "Serie": [str(serie_sel)],
        "Area": [str(area_sel)],
        "Disciplina": [str(disc_sel)],
        "Tempo": [int(tempo_sel)],
        "Foco": [int(foco_sel)]
    }
    
    novo_df = pd.DataFrame(novo_registro_dict)

    try:
        # 1. Tenta ler os dados existentes
        try:
            df_existente = conn.read(worksheet="Dados", ttl=0)
        except:
            df_existente = pd.DataFrame(columns=["Data", "Serie", "Area", "Disciplina", "Tempo", "Foco"])

        # 2. Junta o novo com o antigo (evita erro 400 por formato inválido)
        if df_existente is not None and not df_existente.empty:
            df_final = pd.concat([df_existente, novo_df], ignore_index=True)
        else:
            df_final = novo_df

        # 3. Faz o upload para o Google Sheets
        conn.update(worksheet="Dados", data=df_final)
        st.success("✅ DADOS SINCRONIZADOS COM A PLANILHA!")

        # 4. Geração do PDF Real (sem erros de acento)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 15, "MEO - COMPROVANTE DE ATIVIDADE", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        for col in novo_df.columns:
            valor = novo_df[col].iloc[0]
            texto_linha = f"{col}: {valor}"
            pdf.cell(200, 10, clean_text(texto_linha), ln=True)
        
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📥 BAIXAR COMPROVANTE EM PDF",
            data=pdf_bytes,
            file_name=f"Comprovante_MEO_{disc_sel}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error("Falha na comunicação com o Google Sheets.")
        st.info(f"Detalhe técnico: {e}")

# --- DASHBOARD ---
st.markdown("---")
st.subheader("📊 Sua Evolução")

try:
    df_visual = conn.read(worksheet="Dados", ttl=0)
    if df_visual is not None and not df_visual.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df_visual, names='Disciplina', title='Matérias Estudadas', hole=0.3)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            fig2 = px.bar(df_visual, x='Data', y='Tempo', color='Disciplina', title='Tempo por Sessão')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Os gráficos aparecerão aqui após o seu primeiro registro!")
except:
    st.write("Conectando aos gráficos...")
