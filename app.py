import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Gestão Financeira Dinâmica: Família & Empresa", page_icon="⚖️", layout="wide")

DB_FILE = "finance_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "despesas_diarias" not in data:
                    data["despesas_diarias"] = []
                return data
        except Exception:
            pass
    return {
        "transitorio": {
            "empreiteiro_saldo": 8622.00,
            "empreiteiro_meses": 6,
            "irs_saldo": 17071.49,
            "irs_prestacoes_total": 12,
            "irs_prestacao_atual": 2
        },
        "despesas_diarias": [],
        "historico": []
    }

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

db = load_data()

st.title("Gestão Financeira Familiar & Elementar Privilege")

tab_registo, tab_orcamento, tab_cronograma, tab_historico = st.tabs([
    "Registo Diário de Despesas",
    "Orçamento & Planeamento Mensal",
    "Calendário Mensal por Datas",
    "Histórico & Passivos"
])

# ========================================================
# ABA 1: REGISTO DIÁRIO DE DESPESAS
# ========================================================
with tab_registo:
    st.subheader("1. Registar Novo Gasto do Dia a Dia")
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 2])
    with col_f1:
        data_gasto = st.date_input("Data:", datetime.today())
    with col_f2:
        cat_gasto = st.selectbox("Categoria:", [
            "Takeaway & Uber Eats (Objetivo de Redução)",
            "Restaurantes em Família",
            "Supermercado & Alimentação em Casa",
            "Crianças (Vestuário, Farmácia, Extras)",
            "Lazer Familiar, Livros e Garrafeira",
            "Combustível Pessoal / Fins de Semana",
            "Margem Livre do Casal",
            "Outro Gasto Pontual"
        ])
    with col_f3:
        valor_gasto = st.number_input("Valor (EUR):", min_value=0.01, step=1.0, format="%.2f")
    with col_f4:
        st.write("")
        st.write("")
        btn_adicionar = st.button("Registar Despesa", use_container_width=True)

    desc_gasto = st.text_input("Descrição / Local (Opcional):", placeholder="Ex.: Uber Eats jantar, Continente, Livros...")

    if btn_adicionar:
        novo = {
            "id": int(datetime.now().timestamp()),
            "data": data_gasto.strftime("%Y-%m-%d"),
            "categoria": cat_gasto,
            "descricao": desc_gasto if desc_gasto else cat_gasto,
            "valor": float(valor_gasto)
        }
        db["despesas_diarias"].append(novo)
        save_data(db)
        st.success(f"Gasto de {valor_gasto:.2f} EUR em '{cat_gasto}' registado com sucesso!")

    st.divider()

    st.subheader("2. Acompanhamento dos Limites de Gasto em Tempo Real")
    
    tetos_padrao = {
        "Takeaway & Uber Eats (Objetivo de Redução)": 100.00,
        "Restaurantes em Família": 350.00,
        "Supermercado & Alimentação em Casa": 850.00,
        "Crianças (Vestuário, Farmácia, Extras)": 250.00,
        "Lazer Familiar, Livros e Garrafeira": 200.00,
        "Combustível Pessoal / Fins de Semana": 150.00,
        "Margem Livre do Casal": 200.00
    }

    gastos_df = pd.DataFrame(db["despesas_diarias"])
    if not gastos_df.empty:
        gastos_por_cat = gastos_df.groupby("categoria")["valor"].sum().to_dict()
    else:
        gastos_por_cat = {}

    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("#### Foco Principal: Restauração & Takeaway")
        
        g_take = gastos_por_cat.get("Takeaway & Uber Eats (Objetivo de Redução)", 0.0)
        t_take = tetos_padrao["Takeaway & Uber Eats (Objetivo de Redução)"]
        sobra_take = t_take - g_take
        prog_take = min(1.0, g_take / t_take) if t_take > 0 else 1.0
        
        st.write(f"**Takeaway / Uber Eats:** Gastos **{g_take:.2f} EUR** de **{t_take:.2f} EUR** (Restam: **{sobra_take:.2f} EUR**)")
        st.progress(prog_take)
        if sobra_take < 0:
            st.error(f"Limite de Takeaway excedido em {abs(sobra_take):.2f} EUR!")
        elif sobra_take <= 25:
            st.warning("Atenção: menos de 25 EUR disponíveis para takeaway este mês.")

        g_rest = gastos_por_cat.get("Restaurantes em Família", 0.0)
        t_rest = tetos_padrao["Restaurantes em Família"]
        sobra_rest = t_rest - g_rest
        prog_rest = min(1.0, g_rest / t_rest) if t_rest > 0 else 1.0
        
        st.write(f"**Restaurantes em Família:** Gastos **{g_rest:.2f} EUR** de **{t_rest:.2f} EUR** (Restam: **{sobra_rest:.2f} EUR**)")
        st.progress(prog_rest)
        if sobra_rest < 0:
            st.error(f"Limite de Restaurantes excedido em {abs(sobra_rest):.2f} EUR!")

    with col_t2:
        st.markdown("#### Supermercado e Orçamento Familiar Geral")
        g_sup = gastos_por_cat.get("Supermercado & Alimentação em Casa", 0.0)
        t_sup = tetos_padrao["Supermercado & Alimentação em Casa"]
        sobra_sup = t_sup - g_sup
        prog_sup = min(1.0, g_sup / t_sup) if t_sup > 0 else 1.0
        
        st.write(f"**Supermercado & Alimentação em Casa:** Gastos **{g_sup:.2f} EUR** de **{t_sup:.2f} EUR** (Restam: **{sobra_sup:.2f} EUR**)")
        st.progress(prog_sup)

        total_gastos_geral = sum(gastos_por_cat.values())
        teto_global = sum(tetos_padrao.values())
        sobra_global = teto_global - total_gastos_geral
        st.metric("Total Gasto do Orçamento Familiar", f"{total_gastos_geral:,.2f} EUR", f"Restam {sobra_global:,.2f} EUR do teto de 2.100 EUR")

    st.divider()
    st.subheader("3. Movimentos Registados Neste Mês")
    if not gastos_df.empty:
        st.dataframe(gastos_df[["data", "categoria", "descricao", "valor"]].sort_values(by="data", ascending=False), use_container_width=True, hide_index=True)
        if st.button("Limpar Todos os Gastos Registados Neste Mês"):
            db["despesas_diarias"] = []
            save_data(db)
            st.rerun()
    else:
        st.info("Ainda não há gastos diários registados")