import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Gestao Financeira", page_icon="⚖️", layout="wide")

DB_FILE = "finance_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "despesas_diarias" not in d:
                    d["despesas_diarias"] = []
                for it in d.get("despesas_diarias", []):
                    if "entidade" not in it:
                        it["entidade"] = "Pessoal Familiar"
                return d
        except Exception:
            pass
    return {
        "transitorio": {
            "empreiteiro_saldo": 8622.0,
            "empreiteiro_meses": 6,
            "irs_saldo": 17071.49,
            "irs_prestacoes_total": 12,
            "irs_prestacao_atual": 2
        },
        "despesas_diarias": [],
        "historico": []
    }

def save_data(d):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=4, ensure_ascii=False)

db = load_data()

st.title("Gestao Financeira Familiar & Empresa")

t1, t2, t3, t4 = st.tabs(["Registo Diario", "Orcamento Mensal", "Cronograma", "Passivos"])

with t1:
    st.subheader("1. Lancar Despesa")
    entidade = st.radio("Conta:", ["Pessoal Familiar", "Empresa (ElementarPrivilege)"], horizontal=True)
    if entidade == "Pessoal Familiar":
        cats = [
            "Supermercado & Alimentacao em Casa",
            "Takeaway & Uber Eats",
            "Restaurantes em Familia",
            "Criancas (Vestuario/Farmacia/Escola)",
            "Empregada Domestica Pessoal",
            "Lazer/Livros/Garrafeira",
            "Combustivel Particular",
            "Margem Livre do Casal",
            "Outro Gasto Pessoal"
        ]
    else:
        cats = [
            "Empregada Afeta a Empresa",
            "Impostos Empresa (IRC/Retencoes)",
            "Refeicao Servico / Reuniao",
            "Combustivel / Portagens Servico",
            "Material Clinico / Farmacia",
            "Software / Ferramentas Digitais",
            "Outro Operacional Empresa"
        ]

    c1, c2, c3 = st.columns([2, 3, 2])
    with c1:
        data_mov = st.date_input("Data:", datetime.today())
    with c2:
        cat_mov = st.selectbox("Categoria:", cats)
    with c3:
        valor_mov = st.number_input("Valor (EUR):", min_value=0.01, step=1.0, format="%.2f")

    desc_mov = st.text_input("Descricao (Opcional):")
    if st.button("Gravar Gasto", use_container_width=True):
        novo = {
            "id": int(datetime.now().timestamp()),
            "data": data_mov.strftime("%Y-%m-%d"),
            "entidade": entidade,
            "categoria": cat_mov,
            "descricao": desc_mov if desc_mov else cat_mov,
            "valor": float(valor_mov)
        }
        db["despesas_diarias"].append(novo)
        save_data(db)
        st.success("Gasto registado com sucesso!")
        st.rerun()

    st.divider()
    st.subheader("2. Tetos em Tempo Real")
    df_gastos = pd.DataFrame(db["despesas_diarias"])
    if not df_gastos.empty:
        df_pes = df_gastos[df_gastos["entidade"] == "Pessoal Familiar"]
        df_emp = df_gastos[df_gastos["entidade"] == "Empresa (ElementarPrivilege)"]
        tot_pes = df_pes["valor"].sum() if not df_pes.empty else 0.0
        tot_emp = df_emp["valor"].sum() if not df_emp.empty else 0.0
        
        c_p1, c_p2 = st.columns(2)
        c_p1.metric("Total Pessoal Lancado", f"{tot_pes:.2f} EUR")
        c_p2.metric("Total Empresa Lancado", f"{tot_emp:.2f} EUR")
        
        st.dataframe(df_gastos[["data", "entidade", "categoria", "descricao", "valor"]].sort_values(by="data", ascending=False), use_container_width=True)
        if st.button("Limpar Gastos"):
            db["despesas_diarias"] = []
            save_data(db)
            st.rerun()
    else:
        st.info("Sem movimentos este mes.")

with t2:
    st.subheader("Orcamento Mensal")
    c_rec1, c_rec2 = st.columns(2)
    with c_rec1:
        st.markdown("**Pessoal**")
        rec_hosp = st.number_input("Vencimento Hospital ULSAAVE (EUR):", value=3500.0, step=50.0)
    with c_rec2:
        st.markdown("**Empresa**")
        rec_clin = st.number_input("Faturacao Clinica Privada (EUR):", value=7800.0, step=100.0)
    
    st.divider()
    col_e, col_p = st.columns(2)
    with col_e:
        st.markdown("#### Empresa (ElementarPrivilege)")
        e_emp = st.number_input("Empregada Empresa (EUR):", value=963.78, step=10.0)
        e_imp = st.number_input("Impostos Empresa (IRC/Guias) (EUR):", value=0.0, step=50.0)
        e_creche = st.number_input("Cheques-Creche (EUR):", value=1050.56, step=10.0)
        e_med = st.number_input("Equipamento Medico BPI (EUR):", value=1120.0, step=10.0)
        e_carro = st.number_input("Carro VW Bank (EUR):", value=618.79, step=10.0)
        e_tsu = st.number_input("Seguranca Social TSU (EUR):", value=620.29, step=10.0)
        e_sede = st.number_input("MEO + Energia Sede (EUR):", value=216.0, step=10.0)
        e_obra = st.number_input("Tranche Obra Empreiteiro (EUR):", value=1437.0, step=10.0)
        tot_fixo_emp = e_emp + e_imp + e_creche + e_med + e_carro + e_tsu + e_sede + e_obra
        st.metric("Total Empresa Fixo", f"{tot_fixo_emp:.2f} EUR")
    
    with col_p:
        st.markdown("#### Pessoal Familiar")
        p_ch1 = st.number_input("Credito Habitacao Tranche 003 (EUR):", value=2856.81, step=10.0)
        p_ch2 = st.number_input("Credito Habitacao Tranche 004 (EUR):", value=722.31, step=10.0)
        p_seg = st.number_input("Seguros Habitacao (EUR):", value=110.0, step=10.0)
        p_horas = st.number_input("Empregada Pessoal (EUR):", value=430.0, step=10.0)
        p_luz = st.number_input("Eletricidade (EUR):", value=277.03, step=10.0)
        p_irs = st.number_input("Prestacao IRS Financas (EUR):", value=1385.52, step=10.0)
        tot_fixo_pes = p_ch1 + p_ch2 + p_seg + p_horas + p_luz + p_irs
        st.metric("Total Pessoal Fixo", f"{tot_fixo_pes:.2f} EUR")

with t3:
    st.subheader("Cronograma de Tesouraria")
    crono = [
        {"Dia": "01", "Origem": "BPI Pessoal -> Revolut", "Descricao": "Orcamento Variavel Familiar", "Valor": "-1.880,00 EUR"},
        {"Dia": "01", "Origem": "ElementarPrivilege", "Descricao": "Empregada Empresa", "Valor": "-963,78 EUR"},
        {"Dia": "01", "Origem": "ElementarPrivilege", "Descricao": "TSU Seg. Social", "Valor": "-620,29 EUR"},
        {"Dia": "04", "Origem": "BPI Pessoal", "Descricao": "Empregada Pessoal", "Valor": "-430,00 EUR"},
        {"Dia": "05", "Origem": "ElementarPrivilege", "Descricao": "VW Bank Viatura", "Valor": "-618,79 EUR"},
        {"Dia": "08", "Origem": "ElementarPrivilege", "Descricao": "Cheques-Creche", "Valor": "-1.050,56 EUR"},
        {"Dia": "10", "Origem": "ElementarPrivilege", "Descricao": "Credito Medico", "Valor": "-1.120,00 EUR"},
        {"Dia": "11-15", "Origem": "ElementarPrivilege", "Descricao": "Entrada Faturacao Privada", "Valor": "+7.800,00 EUR"},
        {"Dia": "15", "Origem": "ElementarPrivilege", "Descricao": "Tranche Empreiteiro Obra", "Valor": "-1.437,00 EUR"},
        {"Dia": "20", "Origem": "ElementarPrivilege", "Descricao": "Impostos Empresa", "Valor": "Variavel"},
        {"Dia": "20-23", "Origem": "BPI Pessoal", "Descricao": "Entrada ULSAAVE", "Valor": "+3.500,00 EUR"},
        {"Dia": "30", "Origem": "BPI Pessoal", "Descricao": "Credito Habitacao (003 + 004)", "Valor": "-3.579,12 EUR"},
        {"Dia": "31", "Origem": "BPI Pessoal", "Descricao": "Prestacao IRS", "Valor": "-1.385,52 EUR"}
    ]
    st.dataframe(pd.DataFrame(crono), use_container_width=True)

with t4:
    st.subheader("Passivos Transitarios")
    st.write(f"Divida Empreiteiro: **{db['transitorio']['empreiteiro_saldo']:.2f} EUR**")
    st.write(f"Divida IRS Financas: **{db['transitorio']['irs_saldo']:.2f} EUR**")
