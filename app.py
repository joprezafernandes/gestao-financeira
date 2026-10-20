import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Gestao Financeira", page_icon="⚖️", layout="wide")
st.title("Gestao Financeira")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1Vb2N6bwiU3XTCGTNGXgocYgnTBePxnsoUOfjrPy7RsU/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=SHEET_URL, ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])
        for col in ["data", "entidade", "categoria", "descricao", "valor"]:
            if col not in df.columns:
                df[col] = ""
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])

df_gastos = carregar_dados()

t1, t2, t3, t4 = st.tabs(["Registo Diario", "Orcamento", "Cronograma", "Passivos"])

with t1:
    st.subheader("Tetos Definidos para Este Mes")
    if not df_gastos.empty:
        gasto_pes = df_gastos[df_gastos["entidade"] == "Pessoal Familiar"]["valor"].sum()
        gasto_emp = df_gastos[df_gastos["entidade"] == "Empresa (ElementarPrivilege)"]["valor"].sum()
    else:
        gasto_pes, gasto_emp = 0.0, 0.0

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        t_pes = st.number_input("Teto Pessoal (EUR):", value=250.0, step=50.0)
        st.metric("Saldo Restante Pessoal", f"{(t_pes - gasto_pes):.2f} EUR")
        st.progress(min(1.0, max(0.0, gasto_pes / t_pes)) if t_pes > 0 else 1.0)
    with c_t2:
        t_emp = st.number_input("Teto Empresa (EUR):", value=660.0, step=50.0)
        st.metric("Saldo Restante Empresa", f"{(t_emp - gasto_emp):.2f} EUR")
        st.progress(min(1.0, max(0.0, gasto_emp / t_emp)) if t_emp > 0 else 1.0)

    st.divider()
    st.subheader("Lancar Despesa")
    entidade = st.radio("Conta:", ["Pessoal Familiar", "Empresa (ElementarPrivilege)"], horizontal=True)
    cats = [
        "Supermercado & Alimentacao", "Takeaway & Uber Eats", "Restaurantes",
        "Criancas", "Empregada Domestica", "Lazer/Livros/Garrafeira", "Outro"
    ] if entidade == "Pessoal Familiar" else [
        "Combustivel / Portagens", "Refeicao Servico", "Empregada Empresa",
        "Impostos Empresa", "Material Clinico", "Software", "Outro"
    ]

    c1, c2, c3 = st.columns([2, 3, 2])
    data_mov = c1.date_input("Data:", datetime.today())
    cat_mov = c2.selectbox("Categoria:", cats)
    valor_mov = c3.number_input("Valor (EUR):", min_value=0.01, step=1.0, format="%.2f")
    desc_mov = st.text_input("Descricao:")

    if st.button("Gravar no Google Sheets", use_container_width=True):
        nova = pd.DataFrame([{
            "data": data_mov.strftime("%Y-%m-%d"),
            "entidade": entidade,
            "categoria": cat_mov,
            "descricao": desc_mov if desc_mov else cat_mov,
            "valor": float(valor_mov)
        }])
        df_novo = pd.concat([df_gastos, nova], ignore_index=True)
        try:
            conn.update(spreadsheet=SHEET_URL, data=df_novo)
            st.success("Guardado na Google Sheet com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    st.divider()
    st.subheader("Historico de Gastos")
    if not df_gastos.empty:
        st.dataframe(df_gastos.sort_values(by="data", ascending=False), use_container_width=True)

with t2:
    st.subheader("Orcamento Mensal")
    st.info("Transferencia Dia 01 para Revolut: **1.030,00 EUR** (+ 220 EUR Cartao Refeicao)")
    st.write("- **Empresa Fixos:** 6.785,15 EUR (com obra de 1.437 EUR)")
    st.write("- **Pessoal Fixos:** 6.117,08 EUR (com plano IRS de 1.385,52 EUR)")

with t3:
    st.subheader("Cronograma Mensal de Saidas")
    crono_data = [
        {"Dia": "01", "Conta": "Pessoal", "Descricao": "Revolut Familiar", "Valor": "-1.030,00 EUR"},
        {"Dia": "01", "Conta": "Empresa", "Descricao": "Empregada Empresa", "Valor": "-1.040,00 EUR"},
        {"Dia": "01", "Conta": "Empresa", "Descricao": "TSU Seg. Social", "Valor": "-620,29 EUR"},
        {"Dia": "04", "Conta": "Pessoal", "Descricao": "Empregada Pessoal", "Valor": "-646,50 EUR"},
        {"Dia": "05", "Conta": "Empresa", "Descricao": "Carro VW Bank", "Valor": "-618,79 EUR"},
        {"Dia": "08", "Conta": "Empresa", "Descricao": "Cheques-Creche", "Valor": "-1.050,56 EUR"},
        {"Dia": "10", "Conta": "Empresa", "Descricao": "Credito Medico", "Valor": "-1.120,00 EUR"},
        {"Dia": "15", "Conta": "Empresa", "Descricao": "Obra Empreiteiro", "Valor": "-1.437,00 EUR"},
        {"Dia": "16", "Conta": "Empresa", "Descricao": "Reserva Fiscal IRC", "Valor": "-546,00 EUR"},
        {"Dia": "24", "Conta": "Pessoal", "Descricao": "Reserva Fiscal IRS", "Valor": "-250,00 EUR"},
        {"Dia": "30", "Conta": "Pessoal", "Descricao": "Credito Habitacao", "Valor": "-3.579,12 EUR"},
        {"Dia": "31", "Conta": "Pessoal", "Descricao": "Prestacao IRS", "Valor": "-1.385,52 EUR"}
    ]
    st.dataframe(pd.DataFrame(crono_data), use_container_width=True)

with t4:
    st.subheader("Passivos Transitarios")
    st.write("Divida Obra: **8.622,00 EUR** (Termina em Mar/2027)")
    st.write("Divida IRS: **17.071,49 EUR** (Termina em Ago/2027)")
