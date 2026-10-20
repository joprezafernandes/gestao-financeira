import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

st.set_page_config(page_title="Gestao Financeira", page_icon="⚖️", layout="wide")
st.title("Gestao Financeira")

CSV_URL = "https://docs.google.com/spreadsheets/d/1Vb2N6bwiU3XTCGTNGXgocYgnTBePxnsoUOfjrPy7RsU/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyzreCAbgrp9r7WJKtpTOz5__JplbY9TB0C0qYRfB0E785dpeBdDT21cXBxCrk5huN14Q/exec"

def carregar_dados():
    try:
        df = pd.read_csv(CSV_URL)
        for col in ["data", "entidade", "categoria", "descricao", "valor"]:
            if col not in df.columns:
                df[col] = ""
        df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])

df_gastos = carregar_dados()

# Calculo automatico do ciclo de tesouraria (Dia 20 ao Dia 19 seguinte)
hoje = date.today()
if hoje.day >= 20:
    inicio_ciclo = date(hoje.year, hoje.month, 20)
else:
    mes_ant = hoje.month - 1 if hoje.month > 1 else 12
    ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
    inicio_ciclo = date(ano_ant, mes_ant, 20)

str_inicio_ciclo = inicio_ciclo.strftime("%Y-%m-%d")

# Filtra despesas apenas do ciclo em vigor para calcular os tetos
if not df_gastos.empty and "data" in df_gastos.columns:
    df_ciclo = df_gastos[df_gastos["data"] >= str_inicio_ciclo]
else:
    df_ciclo = df_gastos

t1, t2, t3, t4 = st.tabs(["Registo Diario", "Orcamento", "Cronograma", "Passivos"])

with t1:
    st.subheader(f"Tetos do Ciclo em Vigor (Desde {inicio_ciclo.strftime('%d/%m/%Y')})")
    if not df_ciclo.empty:
        gasto_pes = df_ciclo[df_ciclo["entidade"] == "Pessoal Familiar"]["valor"].sum()
        gasto_emp = df_ciclo[df_ciclo["entidade"] == "Empresa (ElementarPrivilege)"]["valor"].sum()
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

    if st.button("Gravar Despesa", use_container_width=True):
        params = {
            "data": data_mov.strftime("%Y-%m-%d"),
            "entidade": entidade,
            "categoria": cat_mov,
            "descricao": desc_mov if desc_mov else cat_mov,
            "valor": float(valor_mov)
        }
        try:
            r = requests.get(WEBHOOK_URL, params=params, timeout=10)
            if r.status_code == 200:
                st.success("Guardado na Google Sheet com sucesso!")
                st.rerun()
            else:
                st.error(f"Erro ao enviar: Codigo {r.status_code}")
        except Exception as e:
            st.error(f"Erro na ligacao: {e}")

    st.divider()
    st.subheader("Historico de Gastos Registados")
    if not df_gastos.empty:
        st.dataframe(df_gastos.sort_values(by="data", ascending=False), use_container_width=True)
    else:
        st.info("Ainda nao existem despesas registadas na folha.")

with t2:
    st.subheader("Orcamento Mensal")
    st.info("Transferencia Dia 01 para Revolut: **1.030,00 EUR** (+ 220 EUR Cartao Refeicao)")
    st.write("- **Empresa Fixos:** 6.785,15 EUR (com obra de 1.437 EUR)")
    st.write("- **Pessoal Fixos:** 6.117,08 EUR (com plano IRS de 1.385,52 EUR)")

with t3:
    st.subheader("Cronograma do Ciclo de Tesouraria (Dia 20 ao Dia 19)")
    crono_data = [
        {"Dia": "18-19", "Tipo": "Entrada", "Conta": "Empresa", "Descricao": "Faturacao Hospital da Luz / Privado", "Valor": "+7.800,00 EUR"},
        {"Dia": "20-23", "Tipo": "Entrada", "Conta": "Pessoal", "Descricao": "Vencimento Hospital (Fixo + SIGIC)", "Valor": "+4.500,00 EUR"},
        {"Dia": "24", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Reserva Fiscal IRS (Ano Seguinte)", "Valor": "-250,00 EUR"},
        {"Dia": "30", "Tipo": "Entrada", "Conta": "Empresa", "Descricao": "Entrada Consultorio & Clinicas", "Valor": "Variavel"},
        {"Dia": "30", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Credito Habitacao (003 + 004)", "Valor": "-3.579,12 EUR"},
        {"Dia": "31", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Prestacao IRS (Plano Atual)", "Valor": "-1.385,52 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Revolut Orcamento Variavel Familiar", "Valor": "-1.030,00 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Empregada Empresa (com Duodecimos)", "Valor": "-1.040,00 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "TSU Seguranca Social", "Valor": "-620,29 EUR"},
        {"Dia": "04", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Empregada Pessoal", "Valor": "-646,50 EUR"},
        {"Dia": "05", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Carro VW Bank", "Valor": "-618,79 EUR"},
        {"Dia": "08", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Cheques-Creche", "Valor": "-1.050,56 EUR"},
        {"Dia": "10", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Credito Equipamento Medico", "Valor": "-1.120,00 EUR"},
        {"Dia": "15", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Tranche Empreiteiro Obra", "Valor": "-1.437,00 EUR"},
        {"Dia": "16", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Reserva Fiscal IRC (Ano Seguinte)", "Valor": "-546,00 EUR"}
    ]
    st.dataframe(pd.DataFrame(crono_data), use_container_width=True)

with t4:
    st.subheader("Passivos Transitarios")
    st.write("Divida Obra: **8.622,00 EUR** (Termina em Mar/2027)")
    st.write("Divida IRS: **17.071,49 EUR** (Termina em Ago/2027)")
