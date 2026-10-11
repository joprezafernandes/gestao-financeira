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

t1, t2, t3, t4 = st.tabs(["Registo Diario", "Orcamento & Impostos", "Cronograma", "Passivos"])

with t1:
    st.subheader("1. Tetos Definidos para Este Mes")
    
    df_gastos = pd.DataFrame(db["despesas_diarias"])
    if not df_gastos.empty:
        df_pes = df_gastos[df_gastos["entidade"] == "Pessoal Familiar"]
        df_emp = df_gastos[df_gastos["entidade"] == "Empresa (ElementarPrivilege)"]
        gasto_pes = df_pes["valor"].sum() if not df_pes.empty else 0.0
        gasto_emp = df_emp["valor"].sum() if not df_emp.empty else 0.0
    else:
        gasto_pes = 0.0
        gasto_emp = 0.0

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        teto_pes = st.number_input("Teto Pessoal Familiar (EUR):", value=250.0, step=50.0)
        resta_pes = teto_pes - gasto_pes
        prog_pes = min(1.0, max(0.0, gasto_pes / teto_pes)) if teto_pes > 0 else 1.0
        st.write(f"Gasto: **{gasto_pes:.2f} EUR** / Teto: **{teto_pes:.2f} EUR**")
        st.progress(prog_pes)
        if resta_pes < 0:
            st.error(f"Teto Pessoal ultrapassado em {abs(resta_pes):.2f} EUR!")
        else:
            st.metric("Saldo Restante Pessoal", f"{resta_pes:.2f} EUR")

    with col_t2:
        teto_emp = st.number_input("Teto Operacional Empresa (EUR):", value=660.0, step=50.0)
        resta_emp = teto_emp - gasto_emp
        prog_emp = min(1.0, max(0.0, gasto_emp / teto_emp)) if teto_emp > 0 else 1.0
        st.write(f"Gasto: **{gasto_emp:.2f} EUR** / Teto: **{teto_emp:.2f} EUR**")
        st.progress(prog_emp)
        if resta_emp < 0:
            st.error(f"Teto Empresa ultrapassado em {abs(resta_emp):.2f} EUR!")
        else:
            st.metric("Saldo Restante Empresa", f"{resta_emp:.2f} EUR")

    st.divider()
    st.subheader("2. Lancar Despesa")
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
    st.subheader("3. Historico de Gastos Registados")
    if not df_gastos.empty:
        st.dataframe(df_gastos[["data", "entidade", "categoria", "descricao", "valor"]].sort_values(by="data", ascending=False), use_container_width=True)
        if st.button("Limpar Gastos"):
            db["despesas_diarias"] = []
            save_data(db)
            st.rerun()
    else:
        st.info("Ainda nao existem despesas registadas.")

with t2:
    st.subheader("1. Entradas e Provisao de Impostos do Proximo Ano")
    c_rec1, c_rec2 = st.columns(2)
    with c_rec1:
        st.markdown("#### Pessoal Familiar (BPI Particular - Hospital)")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            rec_fixo_hosp = st.number_input("Fixo Liquido Hospital (Ded. Plena):", value=3000.0, step=50.0)
        with col_f2:
            rec_var_hosp = st.number_input("Variavel Liquido (SIGIC/Urgencia):", value=1500.0, step=100.0)
        
        tot_liq_hosp = rec_fixo_hosp + rec_var_hosp
        st.write(f"Total Liquido Hospitalar: **{tot_liq_hosp:,.2f} EUR**")
        
        st.markdown("**Reserva Fiscal IRS Pessoal (25% Renda Predial Moradia + Ajuste):**")
        prov_irs = st.number_input("Cativar para Cofre IRS Pessoal (EUR/mes):", value=250.0, step=25.0)
        st.info(f"Cativar no Dia 24 para IRS: **{prov_irs:.2f} EUR / mes** (~{prov_irs*12:,.0f} EUR/ano)")

    with c_rec2:
        st.markdown("#### Empresa (ElementarPrivilege - BPI Negocios)")
        rec_clin = st.number_input("Faturacao Clinica Privada (EUR):", value=7800.0, step=100.0)
        st.markdown("**Reserva Fiscal Empresa (IRC + Derrama Municipal):**")
        perc_irc = st.slider("% Provisao IRC Empresa (Sobre Faturacao):", min_value=0.0, max_value=15.0, value=7.0, step=0.5)
        prov_irc = round(rec_clin * (perc_irc / 100.0), 2)
        st.info(f"Cativar no Dia 16 para Poupanca IRC: **{prov_irc:.2f} EUR / mes** (~{prov_irc*12:,.0f} EUR/ano)")

    st.divider()
    st.subheader("2. Despesas Fixas Mensais")
    col_e, col_p = st.columns(2)
    with col_e:
        st.markdown("#### Empresa (ElementarPrivilege)")
        e_emp = st.number_input("Empregada Empresa (EUR):", value=963.78, step=10.0)
        e_imp = st.number_input("Impostos Pagos no Mes (Guias Correntes) (EUR):", value=0.0, step=50.0)
        e_creche = st.number_input("Cheques-Creche (EUR):", value=1050.56, step=10.0)
        e_med = st.number_input("Equipamento Medico BPI (EUR):", value=1120.0, step=10.0)
        e_carro = st.number_input("Carro VW Bank (EUR):", value=618.79, step=10.0)
        e_tsu = st.number_input("Seguranca Social TSU (EUR):", value=620.29, step=10.0)
        e_sede = st.number_input("MEO + Energia Sede (EUR):", value=216.0, step=10.0)
        e_obra = st.number_input("Tranche Obra Empreiteiro (EUR):", value=1437.0, step=10.0)
        tot_fixo_emp = e_emp + e_imp + e_creche + e_med + e_carro + e_tsu + e_sede + e_obra
        sobra_empresa_apos_reserva = rec_clin - tot_fixo_emp - prov_irc
        
        c_e1, c_e2 = st.columns(2)
        c_e1.metric("Total Empresa Fixo", f"{tot_fixo_emp:.2f} EUR")
        c_e2.metric("Saldo Empresa (Apos Reserva IRC)", f"{sobra_empresa_apos_reserva:.2f} EUR")

    with col_p:
        st.markdown("#### Pessoal Familiar")
        p_ch1 = st.number_input("Credito Habitacao Tranche 003 (EUR):", value=2856.81, step=10.0)
        p_ch2 = st.number_input("Credito Habitacao Tranche 004 (EUR):", value=722.31, step=10.0)
        p_seg = st.number_input("Seguros Habitacao (EUR):", value=110.0, step=10.0)
        p_horas = st.number_input("Empregada Pessoal (EUR):", value=646.50, step=10.0)
        p_luz = st.number_input("Eletricidade (EUR):", value=277.03, step=10.0)
        p_irs = st.number_input("Prestacao IRS Divida Atual (EUR):", value=1385.52, step=10.0)
        tot_fixo_pes = p_ch1 + p_ch2 + p_seg + p_horas + p_luz + p_irs
        sobra_pessoal_apos_reserva = tot_liq_hosp - tot_fixo_pes - prov_irs
        
        c_p1, c_p2 = st.columns(2)
        c_p1.metric("Total Pessoal Fixo", f"{tot_fixo_pes:.2f} EUR")
        c_p2.metric("Saldo Pessoal (Apos Reserva IRS)", f"{sobra_pessoal_apos_reserva:.2f} EUR")

with t3:
    st.subheader("Cronograma de Tesouraria (Incluindo Reservas Fiscais)")
    crono = [
        {"Dia": "01", "Origem": "BPI Pessoal -> Revolut", "Descricao": "Orcamento Variavel Familiar", "Valor": "-1.880,00 EUR"},
        {"Dia": "01", "Origem": "ElementarPrivilege", "Descricao": "Empregada Empresa", "Valor": "-963,78 EUR"},
        {"Dia": "01", "Origem": "ElementarPrivilege", "Descricao": "TSU Seg. Social", "Valor": "-620,29 EUR"},
        {"Dia": "04", "Origem": "BPI Pessoal", "Descricao": "Empregada Pessoal", "Valor": "-646,50 EUR"},
        {"Dia": "05", "Origem": "ElementarPrivilege", "Descricao": "VW Bank Viatura", "Valor": "-618,79 EUR"},
        {"Dia": "08", "Origem": "ElementarPrivilege", "Descricao": "Cheques-Creche", "Valor": "-1.050,56 EUR"},
        {"Dia": "10", "Origem": "ElementarPrivilege", "Descricao": "Credito Medico", "Valor": "-1.120,00 EUR"},
        {"Dia": "11-15", "Origem": "ElementarPrivilege", "Descricao": "Entrada Faturacao Privada", "Valor": "+7.800,00 EUR"},
        {"Dia": "15", "Origem": "ElementarPrivilege", "Descricao": "Tranche Empreiteiro Obra", "Valor": "-1.437,00 EUR"},
        {"Dia": "16", "Origem": "ElementarPrivilege -> Poupanca", "Descricao": "RESERVA FISCAL IRC (ANO SEGUINTE)", "Valor": f"-{prov_irc:.2f} EUR"},
        {"Dia": "20", "Origem": "ElementarPrivilege", "Descricao": "Impostos Empresa Correntes", "Valor": "Variavel"},
        {"Dia": "20-23", "Origem": "BPI Pessoal", "Descricao": "Entrada Hospital (Fixo + Variavel)", "Valor": f"+{tot_liq_hosp:,.2f} EUR"},
        {"Dia": "24", "Origem": "BPI Pessoal -> Cofre", "Descricao": "RESERVA FISCAL IRS (ANO SEGUINTE)", "Valor": f"-{prov_irs:.2f} EUR"},
        {"Dia": "30", "Origem": "BPI Pessoal", "Descricao": "Credito Habitacao (003 + 004)", "Valor": "-3.579,12 EUR"},
        {"Dia": "31", "Origem": "BPI Pessoal", "Descricao": "Prestacao IRS (Plano Atual)", "Valor": "-1.385,52 EUR"}
    ]
    st.dataframe(pd.DataFrame(crono), use_container_width=True)

with t4:
    st.subheader("Passivos Transitarios")
    st.write(f"Divida Empreiteiro: **{db['transitorio']['empreiteiro_saldo']:.2f} EUR**")
    st.write(f"Divida IRS Financas: **{db['transitorio']['irs_saldo']:.2f} EUR**"
