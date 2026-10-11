import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Gestão Financeira: Família & Empresa", page_icon="⚖️", layout="wide")

DB_FILE = "finance_db.json"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "despesas_diarias" not in data:
                    data["despesas_diarias"] = []
                for item in data.get("despesas_diarias", []):
                    if "entidade" not in item:
                        item["entidade"] = "Pessoal Familiar"
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

st.title("Gestão Financeira Familiar & ElementarPrivilege")

tab_registo, tab_orcamento, tab_cronograma, tab_historico = st.tabs([
    "Registo Diário de Gastos", 
    "Orçamento & Planeamento Mensal", 
    "Cronograma Mensal por Datas",
    "Histórico & Passivos"
])

# ========================================================
# ABA 1: REGISTO DIÁRIO DE GASTOS
# ========================================================
with tab_registo:
    st.subheader("1. Lançar Novo Gasto do Dia a Dia")
    
    entidade_gasto = st.radio(
        "Conta / Entidade:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True
    )
    
    if entidade_gasto == "Pessoal Familiar":
        opcoes_cat = [
            "Supermercado & Alimentação em Casa",
            "Takeaway & Uber Eats (Alvo de Corte)",
            "Restaurantes em Família",
            "Crianças (Vestuário, Farmácia, Extras)",
            "Empregada Doméstica Pessoal (À Hora / Extras)",
            "Lazer Familiar, Livros e Garrafeira",
            "Combustível Particular / Fins de Semana",
            "Margem Livre do Casal",
            "Outro Gasto Pessoal"
        ]
    else:
        opcoes_cat = [
            "Empregada Afeta à Empresa / Apoio Operacional",
            "Impostos Empresa (IRC / Retenções)",
            "Refeição de Serviço / Reunião Clínica",
            "Combustível de Serviço / Deslocações",
            "Material Clínico / Consumíveis / Farmácia",
            "Livros / Formação / Congressos Médicos",
            "Software / Ferramentas Digitais",
            "Outro Gasto Operacional Empresa"
        ]

    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 3, 2, 2])
    with col_f1:
        data_gasto = st.date_input("Data:", datetime.today())
    with col_f2:
        cat_gasto = st.selectbox("Categoria:", opcoes_cat)
    with col_f3:
        valor_gasto = st.number_input("Valor (EUR):", min_value=0.01, step=1.0, format="%.2f")
    with col_f4:
        st.write("")
        st.write("")
        btn_adicionar = st.button("Registar Gasto", use_container_width=True)

    desc_gasto = st.text_input("Descrição / Detalhe (Opcional):", placeholder="Ex.: Continente, Uber Eats, Horas empregada...")

    if btn_adicionar:
        novo = {
            "id": int(datetime.now().timestamp()),
            "data": data_gasto.strftime("%Y-%m-%d"),
            "entidade": entidade_gasto,
            "categoria": cat_gasto,
            "descricao": desc_gasto if desc_gasto else cat_gasto,
            "valor": float(valor_gasto)
        }
        db["despesas_diarias"].append(novo)
        save_data(db)
        st.success(f"Gasto registado em '{entidade_gasto}'!")

    st.divider()

    st.subheader("2. Acompanhamento dos Tetos de Gastos em Tempo Real")

    tetos_padrao = {
        "Takeaway & Uber Eats (Alvo de Corte)": 100.00,
        "Restaurantes em Família": 350.00,
        "Supermercado & Alimentação em Casa": 850.00,
        "Crianças (Vestuário, Farmácia, Extras)": 250.00,
        "Lazer Familiar, Livros e Garrafeira": 200.00,
        "Combustível Particular / Fins de Semana": 150.00,
        "Margem Livre do Casal": 200.00
    }

    gastos_df = pd.DataFrame(db["despesas_diarias"])
    
    if not gastos_df.empty:
        gastos_pessoais = gastos_df[gastos_df.get("entidade", "Pessoal Familiar") == "Pessoal Familiar"]
        gastos_empresa = gastos_df[gastos_df.get("entidade", "") == "Empresa (ElementarPrivilege)"]
        gastos_por_cat_pes = gastos_pessoais.groupby("categoria")["valor"].sum().to_dict() if not gastos_pessoais.empty else {}
        total_gasto_empresa = gastos_empresa["valor"].sum() if not gastos_empresa.empty else 0.0
    else:
        gastos_pessoais = pd.DataFrame()
        gastos_empresa = pd.DataFrame()
        gastos_por_cat_pes = {}
        total_gasto_empresa = 0.0

    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("#### Foco Prioritário Pessoal: Restauração & Takeaway")
        
        g_take = gastos_por_cat_pes.get("Takeaway & Uber Eats (Alvo de Corte)", 0.0)
        t_take = tetos_padrao["Takeaway & Uber Eats (Alvo de Corte)"]
        sobra_take = t_take - g_take
        prog_take = min(1.0, g_take / t_take) if t_take > 0 else 1.0
        
        st.write(f"**Takeaway / Uber Eats:** Gastos **{g_take:.2f} EUR** de **{t_take:.2f} EUR** (Resta: **{sobra_take:.2f} EUR**)")
        st.progress(prog_take)

        g_rest = gastos_por_cat_pes.get("Restaurantes em Família", 0
