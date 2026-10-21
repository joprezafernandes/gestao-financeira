import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, date

st.set_page_config(page_title="Gestao Financeira", page_icon="⚖️", layout="wide")
st.title("Gestao Financeira")

CSV_URL = "https://docs.google.com/spreadsheets/d/1Vb2N6bwiU3XTCGTNGXgocYgnTBePxnsoUOfjrPy7RsU/export?format=csv"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbygTwbK_7qFXX19qf1hDxXe1wB5bIgH5AYOtdlwSt-1G_LjcYHpsA1dT-e0fPqgC7g84A/exec"

def carregar_dados():
    try:
        url_fresca = f"{CSV_URL}&t={int(time.time())}"
        df = pd.read_csv(url_fresca)
        for col in ["data", "entidade", "categoria", "descricao", "valor"]:
            if col not in df.columns:
                df[col] = ""
        df["valor"] = pd.to_numeric(df["valor"].astype(str).str.replace(",", "."), errors="coerce").fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])

df_gastos = carregar_dados()

hoje = date.today()
if hoje.day >= 20:
    inicio_ciclo = date(hoje.year, hoje.month, 20)
else:
    mes_ant = hoje.month - 1 if hoje.month > 1 else 12
    ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
    inicio_ciclo = date(ano_ant, mes_ant, 20)

str_inicio_ciclo = inicio_ciclo.strftime("%Y-%m-%d")

if not df_gastos.empty and "data" in df_gastos.columns:
    df_ciclo = df_gastos[df_gastos["data"] >= str_inicio_ciclo]
else:
    df_ciclo = df_gastos

t1, t2, t3, t4 = st.tabs(["Registo Diario", "Orcamento & Entradas", "Cronograma", "Passivos"])

with t1:
    st.subheader(f"Tetos do Ciclo (Desde {inicio_ciclo.strftime('%d/%m/%Y')})")
    gasto_pes = df_ciclo[df_ciclo["entidade"] == "Pessoal Familiar"]["valor"].sum() if not df_ciclo.empty else 0.0
    gasto_emp = df_ciclo[df_ciclo["entidade"] == "Empresa (ElementarPrivilege)"]["valor"].sum() if not df_ciclo.empty else 0.0

    c_t1, c_t2 = st.columns(2)
    with c_t1:
        t_pes = st.number_input("Teto Pessoal (EUR):", value=250.0, step=50.0)
        st.metric("Saldo Restante Pessoal", f"{(t_pes - gasto_pes):.2f} EUR")
        st.progress(min(1.0, max(0.0, gasto_pes / t_pes)) if t_pes > 0 else 1.0)
    with c_t2:
        t_emp = st.number_input("Teto Operacional Empresa (Via Verde/Comb./Ref.) (EUR):", value=660.0, step=50.0)
        st.metric("Saldo Restante Empresa", f"{(t_emp - gasto_emp):.2f} EUR")
        st.progress(min(1.0, max(0.0, gasto_emp / t_emp)) if t_emp > 0 else 1.0)

    st.divider()
    st.subheader("Lancar Despesa")
    
    # Formulário blindado contra cliques acidentais e recarregamentos prematuros
    with st.form("form_despesa", clear_on_submit=True):
        entidade = st.radio("Conta:", ["Pessoal Familiar", "Empresa (ElementarPrivilege)"], horizontal=True)
        
        cats = [
            "Supermercado & Alimentacao", "Takeaway & Uber Eats", "Restaurantes",
            "Criancas", "Empregada Domestica", "Lazer/Livros/Garrafeira", "Outro"
        ] if entidade == "Pessoal Familiar" else [
            "Via Verde / Combustivel (Empresa)", "Refeicao Servico", "Empregada Empresa",
            "Impostos Empresa", "Material Clinico", "Software", "Outro"
        ]

        c1, c2, c3 = st.columns([2, 3, 2])
        data_mov = c1.date_input("Data:", datetime.today())
        cat_mov = c2.selectbox("Categoria:", cats)
        valor_mov = c3.number_input("Valor (EUR):", min_value=0.01, step=1.0, format="%.2f")
        desc_mov = st.text_input("Descricao:")

        submeter = st.form_submit_button("Gravar Despesa no Google Drive", use_container_width=True)

    if submeter:
        params = {
            "data": data_mov.strftime("%Y-%m-%d"),
            "entidade": entidade,
            "categoria": cat_mov,
            "descricao": desc_mov if desc_mov else cat_mov,
            "valor": str(float(valor_mov))
        }
        with st.spinner("A gravar na Google Sheet..."):
            try:
                r = requests.get(WEBHOOK_URL, params=params, timeout=15)
                if r.status_code == 200:
                    st.success(f"Gravado com sucesso no Google Drive: {float(valor_mov):.2f} EUR em {cat_mov}!")
                else:
                    st.error(f"Erro ao gravar (Codigo {r.status_code}): {r.text}")
            except Exception as ex:
                st.error(f"Falha na ligacao ao Google Sheets: {ex}")

    st.divider()
    col_hist, col_refresh = st.columns([4, 1])
    with col_hist:
        st.subheader("Historico de Gastos Registados")
    with col_refresh:
        if st.button("Atualizar Lista"):
            st.rerun()

    if not df_gastos.empty:
        st.dataframe(df_gastos.sort_values(by="data", ascending=False), use_container_width=True)
    else:
        st.info("Ainda nao existem despesas registadas na folha.")

with t2:
    st.subheader("1. Entradas Reais Deste Ciclo")
    c_in1, c_in2 = st.columns(2)
    with c_in1:
        st.markdown("#### Empresa (ElementarPrivilege)")
        rec_luz = st.number_input("Faturacao Hospital da Luz / Privado (Dia 18-19):", value=7800.0, step=100.0)
        rec_consultorio = st.number_input("Entrada Consultorio & Outras Clinicas (Dia 30):", value=0.0, step=100.0)
        tot_receita_emp = rec_luz + rec_consultorio
        
        perc_irc = st.slider("% Provisao IRC Empresa:", min_value=0.0, max_value=15.0, value=7.0, step=0.5)
        reserva_irc = round(tot_receita_emp * (perc_irc / 100.0), 2)
        st.info(f"Reserva IRC a cativar a dia 16 ({perc_irc}%): **{reserva_irc:.2f} EUR**")

    with c_in2:
        st.markdown("#### Pessoal Familiar (Hospital Publico)")
        rec_pub_fixo = st.number_input("Vencimento Fixo Hospital Liquido:", value=3000.0, step=50.0)
        rec_pub_var = st.number_input("Producao Adicional / SIGIC Liquido:", value=1500.0, step=100.0)
        tot_receita_pes = rec_pub_fixo + rec_pub_var
        
        prov_irs = st.number_input("Reserva Fiscal IRS a cativar a dia 24:", value=250.0, step=25.0)
        st.info(f"Reserva IRS a cativar a dia 24: **{prov_irs:.2f} EUR**")

    st.divider()
    st.subheader("2. Balanco Operacional do Mes")
    col_b1, col_b2 = st.columns(2)
    
    fixos_emp = 5734.59
    fixos_pes = 6117.08
    
    saldo_emp_livre = tot_receita_emp - fixos_emp - reserva_irc
    saldo_pes_livre = tot_receita_pes - fixos_pes - prov_irs
    
    with col_b1:
        st.metric("Total Entradas Empresa", f"{tot_receita_emp:,.2f} EUR")
        st.write(f"- Fixos Empresa (Obra + Salarios + Carro + BPI): **{fixos_emp:,.2f} EUR**")
        st.caption("*(Cheques-creche de 1.050,56 EUR suspensos/isentos ate Jan)*")
        st.write(f"- Reserva IRC ({perc_irc}%): **{reserva_irc:,.2f} EUR**")
        st.metric("Margem Livre Empresa", f"{saldo_emp_livre:,.2f} EUR")
        
    with col_b2:
        st.metric("Total Entradas Pessoal", f"{tot_receita_pes:,.2f} EUR")
        st.write(f"- Fixos Pessoais (CH + Divida IRS): **{fixos_pes:,.2f} EUR**")
        st.write(f"- Reserva IRS: **{prov_irs:,.2f} EUR**")
        st.metric("Margem Livre Pessoal", f"{saldo_pes_livre:,.2f} EUR")

with t3:
    st.subheader("Cronograma Dinamico de Tesouraria (Dia 20 ao Dia 19)")
    crono_data = [
        {"Dia": "18-19", "Tipo": "Entrada", "Conta": "Empresa (Revolut)", "Descricao": "Faturacao Hospital da Luz / Privado", "Valor": f"+{rec_luz:,.2f} EUR"},
        {"Dia": "20-23", "Tipo": "Entrada", "Conta": "Pessoal", "Descricao": "Vencimento Hospital (Fixo + SIGIC)", "Valor": f"+{tot_receita_pes:,.2f} EUR"},
        {"Dia": "24", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Reserva Fiscal IRS (Ano Seguinte)", "Valor": f"-{prov_irs:,.2f} EUR"},
        {"Dia": "30", "Tipo": "Entrada", "Conta": "Empresa (Revolut)", "Descricao": "Consultorio & Outras Clinicas", "Valor": f"+{rec_consultorio:,.2f} EUR"},
        {"Dia": "30", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Credito Habitacao (003 + 004)", "Valor": "-3.579,12 EUR"},
        {"Dia": "31", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Prestacao IRS (Plano Atual)", "Valor": "-1.385,52 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Revolut Orcamento Variavel Familiar", "Valor": "-630,00 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Empregada Empresa (com Duodecimos)", "Valor": "-1.040,00 EUR"},
        {"Dia": "01", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "TSU Seguranca Social", "Valor": "-620,29 EUR"},
        {"Dia": "04", "Tipo": "Saida", "Conta": "Pessoal", "Descricao": "Empregada Pessoal", "Valor": "-646,50 EUR"},
        {"Dia": "05", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Carro VW Bank", "Valor": "-618,79 EUR"},
        {"Dia": "08", "Tipo": "Isento", "Conta": "Empresa", "Descricao": "Cheques-Creche (Ja Pagos ate Jan)", "Valor": "0,00 EUR"},
        {"Dia": "10", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Credito Equipamento Medico", "Valor": "-1.120,00 EUR"},
        {"Dia": "15", "Tipo": "Saida", "Conta": "Empresa", "Descricao": "Tranche Empreiteiro Obra", "Valor": "-1.437,00 EUR"},
        {"Dia": "16", "Tipo": "Saida", "Conta": "Empresa (Revolut Pocket)", "Descricao": "Reserva Fiscal IRC (Ano Seguinte)", "Valor": f"-{reserva_irc:,.2f} EUR"}
    ]
    st.dataframe(pd.DataFrame(crono_data), use_container_width=True)

with t4:
    st.subheader("Passivos Transitarios")
    st.write("Divida Obra: **8.622,00 EUR** (Termina em Mar/2027)")
    st.write("Divida IRS: **17.071,49 EUR** (Termina em Ago/2027)")
