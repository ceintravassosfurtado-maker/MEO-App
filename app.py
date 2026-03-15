import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from fpdf import FPDF
import datetime
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="MEO - Meu Estudo Orientado", layout="wide", page_icon="🧭")

# --- FUNÇÃO PARA LIMPAR TEXTO DO PDF (EVITA ERRO DE ACENTUAÇÃO) ---
def clean_text(text):
    if text is None: return ""
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- CONEXÃO COM GOOGLE SHEETS (MÉTODO SIMPLIFICADO) ---
try:
    # Deixamos o Streamlit gerenciar as credenciais automaticamente
    # Ele vai buscar sozinho o que está dentro de [connections.gsheets] nos Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.info("💡 Se o erro persistir, verifique a formatação dos Secrets.")
    st.stop()
# --- ESTILIZAÇÃO CSS ---
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
            if df_existente is None or df_existente.empty:
                df_existente = pd.DataFrame(columns=["Data", "Serie", "Area", "Disciplina", "Tempo", "Foco"])
        except Exception:
            df_existente = pd.DataFrame(columns=["Data", "Serie", "Area", "Disciplina", "Tempo", "Foco"])

        # 2. Concatenação segura
        df_final = pd.concat([df_existente, novo_df], ignore_index=True)

        # 3. Atualização no Google Sheets
        conn.update(worksheet="Dados", data=df_final)
        st.success("✅ DADOS SINCRONIZADOS COM A PLANILHA!")

        # 4. Geração do PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 15, clean_text("MEO - COMPROVANTE DE ATIVIDADE"), ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", size=12)
        for col in novo_df.columns:
            valor = novo_df[col].iloc[0]
            texto_linha = f"{col}: {valor}"
            pdf.cell(200, 10, clean_text(texto_linha), ln=True)
        
        pdf_output = pdf.output(dest='S')
        pdf_bytes = pdf_output if isinstance(pdf_output, bytes) else pdf_output.encode('latin-1')
        
        st.download_button(
            label="📥 BAIXAR COMPROVANTE EM PDF",
            data=pdf_bytes,
            file_name=f"Comprovante_MEO_{disc_sel}.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Erro ao salvar os dados: {e}")

# --- DASHBOARD ---
st.markdown("---")
st.subheader("📊 Sua Evolução")

try:
    df_visual = conn.read(worksheet="Dados", ttl=0)
    if df_visual is not None and not df_visual.empty:
        df_visual['Tempo'] = pd.to_numeric(df_visual['Tempo'], errors='coerce')
        
        c1, c2 = st.columns(2)
        with c1:
            fig1 = px.pie(df_visual, names='Disciplina', values='Tempo', title='Distribuição de Tempo por Matéria', hole=0.3)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            df_visual['Data_dt'] = pd.to_datetime(df_visual['Data'], format="%d/%m/%Y %H:%M", errors='coerce')
            df_visual = df_visual.sort_values('Data_dt')
            
            fig2 = px.bar(df_visual, x='Data', y='Tempo', color='Disciplina', title='Tempo de Estudo por Sessão')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Os gráficos aparecerão aqui após o seu primeiro registro!")
except Exception as e:
    st.write("Aguardando dados para gerar gráficos...")
