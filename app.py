import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Laboratório de Estudo Orientado", layout="wide")

# --- DICIONÁRIO DA FGB POR ÁREAS ---
FGB = {
    "Linguagens": ["Português", "Literatura", "Inglês", "Espanhol", "Artes", "Educação Física"],
    "Matemática": ["Matemática (Álgebra)", "Matemática (Geometria)", "Estatística"],
    "Ciências da Natureza": ["Biologia", "Física", "Química"],
    "Ciências Humanas": ["História", "Geografia", "Filosofia", "Sociologia"]
}

# --- MENU LATERAL ---
st.sidebar.title("🚀 Navegação")
menu = st.sidebar.radio("Selecione uma opção:", 
    ["Dashboard", "Inserir Tabela", "Mapa Mental", "Escanear Resumo", "Configurações"])

serie = st.sidebar.selectbox("Série Atual:", ["1ª Série EM", "2ª Série EM", "3ª Série EM"])

# --- LÓGICA DO DASHBOARD ---
if menu == "Dashboard":
    st.header(f"📊 Painel de Desempenho - {serie}")
    
    # Formulário de Registro
    with st.expander("➕ Registrar Novo Estudo", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            area = st.selectbox("Área do Conhecimento", list(FGB.keys()))
        with col2:
            disciplina = st.selectbox("Disciplina", FGB[area])
        with col3:
            tempo = st.number_input("Tempo (minutos)", min_value=15, step=5)
            
        foco = st.select_slider("Nível de Foco", options=[1, 2, 3, 4, 5], value=3)
        gargalo = st.multiselect("Gargalos Identificados:", ["Celular", "Sono", "Barulho", "Falta de Base", "Cansaço"])
        
        if st.button("Salvar Registro"):
            st.success(f"Estudo de {disciplina} salvo com sucesso!")

    st.divider()
    st.subheader("Análise Detalhada")
    # Espaço para os gráficos (Plotly/Pandas)
    st.info("Os gráficos aparecerão aqui conforme os dados forem carregados do Google Sheets.")

# --- FERRAMENTAS ADICIONAIS ---
elif menu == "Inserir Tabela":
    st.header("📋 Gerador de Tabelas e Cronogramas")
    df_modelo = pd.DataFrame([{"Atividade": "", "Prazo": "", "Status": "Pendente"}] * 5)
    st.data_editor(df_modelo, num_rows="dynamic")

elif menu == "Mapa Mental":
    st.header("🧠 Centro de Mapas Mentais")
    upload = st.file_uploader("Subir imagem do seu mapa mental", type=["png", "jpg", "jpeg"])
    link = st.text_input("Link do Mapa (Canva/Miro):")
    if upload: st.image(upload)

elif menu == "Escanear Resumo":
    st.header("📸 Escanear Resumo Manuscrito")
    foto = st.camera_input("Capture a foto do seu caderno")
    if foto: st.image(foto)

# --- EXPORTAÇÃO PDF ---
st.sidebar.divider()
if st.sidebar.button("📥 Gerar Relatório PDF"):
    st.sidebar.write("Gerando PDF... (Simulação)")
    # Aqui entra a lógica da biblioteca FPDF que discutimos