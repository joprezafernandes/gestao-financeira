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
            "Impostos Empresa (IRC / Retenções / Guias)",
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

    desc_gasto = st.text_input("Descrição / Detalhe (Opcional):", placeholder="Ex.: Horas semanais empregada, Continente, Uber Eats, Guia IRC...")

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
        st.success(f"Gasto de {valor_gasto:.2f} EUR registado em '{entidade_gasto}' -> '{cat_gasto}'!")

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
        if sobra_take < 0:
            st.error(f"Teto de Takeaway ultrapassado em {abs(sobra_take):.2f} EUR!")
        elif sobra_take <= 25:
            st.warning("Atenção: Menos de 25 EUR disponíveis para takeaway este mês.")

        g_rest = gastos_por_cat_pes.get("Restaurantes em Família", 0.0)
        t_rest = tetos_padrao["Restaurantes em Família"]
        sobra_rest = t_rest - g_rest
        prog_rest = min(1.0, g_rest / t_rest) if t_rest > 0 else 1.0
        
        st.write(f"**Restaurantes em Família:** Gastos **{g_rest:.2f} EUR** de **{t_rest:.2f} EUR** (Resta: **{sobra_rest:.2f} EUR**)")
        st.progress(prog_rest)
        if sobra_rest < 0:
            st.error(f"Teto de Restaurantes ultrapassado em {abs(sobra_rest):.2f} EUR!")

    with col_t2:
        st.markdown("#### Totais de Controlo: Pessoal vs Empresa")
        g_sup = gastos_por_cat_pes.get("Supermercado & Alimentação em Casa", 0.0)
        t_sup = tetos_padrao["Supermercado & Alimentação em Casa"]
        sobra_sup = t_sup - g_sup
        prog_sup = min(1.0, g_sup / t_sup) if t_sup > 0 else 1.0
        
        st.write(f"**Supermercado & Casa:** Gastos **{g_sup:.2f} EUR** de **{t_sup:.2f} EUR** (Resta: **{sobra_sup:.2f} EUR**)")
        st.progress(prog_sup)

        total_gastos_pessoais = sum(gastos_por_cat_pes.values())
        teto_global = sum(tetos_padrao.values())
        sobra_global = teto_global - total_gastos_pessoais
        
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Total Variável Pessoal", f"{total_gastos_pessoais:,.2f} EUR", f"Resta {sobra_global:,.2f} EUR")
        c_m2.metric("Total Lançado Empresa", f"{total_gasto_empresa:,.2f} EUR", "Dedutível / Fiscal")

    st.divider()
    st.subheader("3. Movimentos Registados Deste Mês")
    if not gastos_df.empty:
        filtro_entidade = st.radio("Filtrar Tabela por:", ["Todos os Gastos", "Apenas Pessoal Familiar", "Apenas Empresa (ElementarPrivilege)"], horizontal=True)
        if filtro_entidade == "Apenas Pessoal Familiar":
            df_mostrar = gastos_pessoais
        elif filtro_entidade == "Apenas Empresa (ElementarPrivilege)":
            df_mostrar = gastos_empresa
        else:
            df_mostrar = gastos_df

        st.dataframe(df_mostrar[["data", "entidade", "categoria", "descricao", "valor"]].sort_values(by="data", ascending=False), use_container_width=True, hide_index=True)
        if st.button("Limpar Todos os Gastos Registados Deste Mês"):
            db["despesas_diarias"] = []
            save_data(db)
            st.rerun()
    else:
        st.info("Ainda não há gastos diários registados para este mês.")

# ========================================================
# ABA 2: ORÇAMENTO & PLANEAMENTO MENSAL EXAUSTIVO
# ========================================================
with tab_orcamento:
    st.subheader("1. Entradas Reais do Mês Corrente")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        st.markdown("**Conta Pessoal (BPI Particular)**")
        rec_ulsaave = st.number_input(
            "Vencimento Hospitalar Líquido ULSAAVE [EUR]:",
            min_value=0.0,
            value=3500.0,
            step=50.0
        )

    with col_in2:
        st.markdown("**Conta Empresa (ElementarPrivilege - BPI Negócios)**")
        rec_empresa = st.number_input(
            "Faturação Clínica / Cirúrgica Privada Líquida [EUR]:",
            min_value=0.0,
            value=7800.0,
            step=100.0
        )

    st.divider()

    st.subheader("2. Detalhe Completo das Despesas Fixas")
    
    col_fx1, col_fx2 = st.columns(2)
    with col_fx1:
        st.markdown("#### Empresa (ElementarPrivilege - Conta BPI Negócios)")
        fx_emp_empresa = st.number_input("Empregada / Apoio Operacional Sede da Empresa [EUR]:", value=963.78, step=10.0, help="Remuneração afeta à empresa (ex.: serviços de apoio e limpeza da fração/sede)")
        fx_impostos_empresa = st.number_input("Impostos da Empresa (IRC / Pagamentos por Conta / Retenções) [EUR]:", value=0.00, step=50.0, help="Rubrica para acomodar liquidações de IRC ou retenções fiscais da empresa")
        fx_cheque_creche = st.number_input("Cheques-Creche / Infância dos Filhos [EUR]:", value=105
