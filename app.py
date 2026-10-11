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
# ABA 1: REGISTO DIÁRIO DE GASTOS (COM SELEÇÃO PESSOAL vs EMPRESA)
# ========================================================
with tab_registo:
    st.subheader("1. Lançar Novo Gasto do Dia a Dia")
    
    # SELETOR DE CONTA / ENTIDADE
    entidade_gasto = st.radio(
        "Conta / Entidade:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True
    )
    
    # Categorias adaptadas a cada entidade
    if entidade_gasto == "Pessoal Familiar":
        opcoes_cat = [
            "Supermercado & Alimentação em Casa",
            "Takeaway & Uber Eats (Alvo de Corte)",
            "Restaurantes em Família",
            "Crianças (Vestuário, Farmácia, Extras)",
            "Lazer Familiar, Livros e Garrafeira",
            "Combustível Particular / Fins de Semana",
            "Margem Livre do Casal",
            "Outro Gasto Pessoal"
        ]
    else:
        opcoes_cat = [
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

    desc_gasto = st.text_input("Descrição / Detalhe (Opcional):", placeholder="Ex.: Continente, Uber Eats, Restaurante reunião clínica, Livro ICBAS...")

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
        c_m2.metric("Total Pontual Empresa", f"{total_gasto_empresa:,.2f} EUR", "Dedutível em IRC")

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
    st.markdown("Introduza os valores efetivamente auferidos para que o motor calcule a distribuição exata.")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        st.markdown("**Conta Pessoal (BPI Particular)**")
        rec_ulsaave = st.number_input(
            "Vencimento Hospitalar Líquido ULSAAVE (Apenas Titular) [EUR]:",
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
        fx_cheque_creche = st.number_input("Cheques-Creche / Infância dos Filhos [EUR]:", value=1050.56, step=10.0)
        fx_credito_medico = st.number_input("Crédito Equipamento Médico BPI [EUR]:", value=1120.00, step=10.0)
        fx_carro = st.number_input("Crédito Automóvel (Volkswagen Bank) [EUR]:", value=618.79, step=10.0)
        fx_tsu = st.number_input("Segurança Social / TSU Gerência [EUR]:", value=620.29, step=10.0)
        fx_aida = st.number_input("Prestação Serviços Médicos (Apoio Clínico) [EUR]:", value=963.78, step=10.0)
        fx_meo_energia = st.number_input("MEO Fibra Sede + Quota Energia Sede (~25%) [EUR]:", value=216.00, step=10.0)
        fx_via_verde = st.number_input("Via Verde Pay Empresa [EUR]:", value=45.00, step=5.0)
        fx_software = st.number_input("Google Workspace + KnowUro [EUR]:", value=59.20, step=5.0)
        fx_bpi_empresa = st.number_input("Comissão Conta BPI Negócios [EUR]:", value=8.31, step=1.0)
        fx_cartao_ref = st.number_input("Cartão Refeição Gerente (Isento) [EUR]:", value=220.00, step=10.0)
        
    with col_fx2:
        st.markdown("#### Pessoal Familiar (Conta BPI Particular)")
        fx_ch_003 = st.number_input("Crédito Habitação Tranche 003 (Taxa Fixa 2,7%) [EUR]:", value=2856.81, step=10.0)
        fx_ch_004 = st.number_input("Crédito Habitação Tranche 004 (Taxa Fixa 2,7%) [EUR]:", value=722.31, step=10.0)
        fx_seguros_ch = st.number_input("Seguros CH (Vida + Multirriscos) [EUR]:", value=110.00, step=10.0)
        fx_empregada = st.number_input("Apoio Doméstico Familiar (Empregada) [EUR]:", value=430.00, step=10.0)
        fx_eletricidade = st.number_input("Eletricidade Moradia Líquida (Gold Energy) [EUR]:", value=277.03, step=10.0)
        fx_agua = st.number_input("Água e Saneamento Residencial [EUR]:", value=50.00, step=5.0)
        fx_deco_unicef = st.number_input("Deco Proteste + UNICEF [EUR]:", value=41.74, step=5.0)
        fx_lazer_digital = st.number_input("Spotify + Amazon Prime [EUR]:", value=21.98, step=1.0)
        fx_bpi_pessoal = st.number_input("Comissão Conta Valor BPI [EUR]:", value=5.19, step=1.0)

    st.markdown("#### Passivos Transitórios do Mês")
    c_tr1, c_tr2 = st.columns(2)
    with c_tr1:
        tranche_empreiteiro_ativa = st.checkbox("Incluir Tranche Mensal Empreiteiro (Obra)", value=True)
        val_empreiteiro = 1437.00 if tranche_empreiteiro_ativa else 0.00

    with c_tr2:
        prestacao_irs_ativa = st.checkbox("Incluir Prestação Mensal IRS (Finanças)", value=True)
        val_irs = 1385.52 if prestacao_irs_ativa else 0.00

    total_fixo_empresa = (fx_cheque_creche + fx_credito_medico + fx_carro + fx_tsu + 
                          fx_aida + fx_meo_energia + fx_via_verde + fx_software + 
                          fx_bpi_empresa + fx_cartao_ref + val_empreiteiro)

    total_fixo_pessoal = (fx_ch_003 + fx_ch_004 + fx_seguros_ch + fx_empregada + 
                          fx_eletricidade + fx_agua + fx_deco_unicef + fx_lazer_digital + 
                          fx_bpi_pessoal + val_irs)

    renda_sede = 850.00
    saldo_operacional_empresa = rec_empresa - total_fixo_empresa
    deficit_pessoal_pre = total_fixo_pessoal - (rec_ulsaave + renda_sede)
    ajuste_gerencia = max(0.0, deficit_pessoal_pre)

    if saldo_operacional_empresa >= (renda_sede + ajuste_gerencia):
        transf_efetiva = renda_sede + ajuste_gerencia
        saldo_final_empresa = saldo_operacional_empresa - transf_efetiva
    else:
        transf_efetiva = max(0.0, saldo_operacional_empresa)
        saldo_final_empresa = 0.0

    liquidez_disponivel_pessoal = rec_ulsaave + transf_efetiva - total_fixo_pessoal

    teto_criancas = 250.00
    teto_supermercado = 630.00
    teto_combustivel = 150.00
    teto_lazer = 200.00
    teto_casal = 200.00
    teto_restaurantes = 350.00
    teto_takeaway = 100.00

    sobra = max(0.0, liquidez_disponivel_pessoal)
    aloc_criancas = min(sobra, teto_criancas); sobra -= aloc_criancas
    aloc_supermercado = min(sobra, teto_supermercado); sobra -= aloc_supermercado
    aloc_combustivel = min(sobra, teto_combustivel); sobra -= aloc_combustivel
    aloc_lazer = min(sobra, teto_lazer); sobra -= aloc_lazer
    aloc_casal = min(sobra, teto_casal); sobra -= aloc_casal
    aloc_restaurantes = min(sobra, teto_restaurantes); sobra -= aloc_restaurantes
    aloc_takeaway = min(sobra, teto_takeaway); sobra -= aloc_takeaway
    excedente_investimento = sobra

    st.divider()
    st.subheader("3. Balanço Dinâmico")
    c_res1, c_res2, c_res3, c_res4 = st.columns(4)
    c_res1.metric("Fixos Empresa (com Obra)", f"{total_fixo_empresa:,.2f} EUR")
    c_res2.metric("Fixos Pessoais & IRS", f"{total_fixo_pessoal:,.2f} EUR")
    c_res3.metric("Transf. Empresa -> Pessoal", f"{transf_efetiva:,.2f} EUR")
    c_res4.metric("Saldo Retido na Empresa", f"{saldo_final_empresa:,.2f} EUR")

    total_aprovado_revolut = (aloc_criancas + aloc_supermercado + aloc_combustivel + 
                              aloc_lazer + aloc_casal + aloc_restaurantes + aloc_takeaway)

    st.info(f"Valor a Transferir a Dia 01 para o Revolut Familiar: **{total_aprovado_revolut:,.2f} EUR**")

# ========================================================
# ABA 3: CRONOGRAMA MENSAL POR DATAS
# ========================================================
with tab_cronograma:
    st.subheader("Cronograma Mensal de Tesouraria")
    df_crono = pd.DataFrame([
        {"Dia": "Dia 01", "Entidade": "BPI Pessoal -> Revolut", "Movimento": "Transferência Teto Variável Familiar", "Valor": "-1.880,00 EUR"},
        {"Dia": "Dia 01", "Entidade": "ElementarPrivilege", "Movimento": "TSU Gerência + Aida Esteves", "Valor": "-1.584,07 EUR"},
        {"Dia": "Dia 01", "Entidade": "ElementarPrivilege", "Movimento": "Cartão Refeição Gerente", "Valor": "-220,00 EUR"},
        {"Dia": "Dia 04", "Entidade": "BPI Pessoal", "Movimento": "Apoio Doméstico (Empregada)", "Valor": "-430,00 EUR"},
        {"Dia": "Dia 05", "Entidade": "ElementarPrivilege", "Movimento": "Financiamento Viatura (VW Bank)", "Valor": "-618,79 EUR"},
        {"Dia": "Dia 05", "Entidade": "Empresa -> Pessoal", "Movimento": "Renda Gabinete Moradia", "Valor": "+850,00 EUR"},
        {"Dia": "Dia 08", "Entidade": "ElementarPrivilege", "Movimento": "Cheques-Creche Filhos", "Valor": "-1.050,56 EUR"},
        {"Dia": "Dia 10", "Entidade": "ElementarPrivilege", "Movimento": "Crédito Equipamento Médico BPI", "Valor": "-1.120,00 EUR"},
        {"Dia": "Dia 11 a 15", "Entidade": "ElementarPrivilege", "Movimento": "FATURAÇÃO CLÍNICA PRIVADA", "Valor": "+7.500 a 8.500 EUR"},
        {"Dia": "Dia 12", "Entidade": "BPI Pessoal", "Movimento": "Eletricidade Moradia (Gold Energy)", "Valor": "-277,03 EUR"},
        {"Dia": "Dia 15", "Entidade": "ElementarPrivilege", "Movimento": "Tranche Empreiteiro Obra (6x)", "Valor": "-1.437,00 EUR"},
        {"Dia": "Dia 20", "Entidade": "BPI Pessoal", "Movimento": "Água Residencial", "Valor": "-50,00 EUR"},
        {"Dia": "Dia 20 a 23", "Entidade": "BPI Pessoal", "Movimento": "VENCIMENTO ULSAAVE", "Valor": "+3.500,00 EUR"},
        {"Dia": "Dia 30", "Entidade": "BPI Pessoal", "Movimento": "Crédito Habitação (Tranches 003 + 004)", "Valor": "-3.579,12 EUR"},
        {"Dia": "Dia 31", "Entidade": "BPI Pessoal", "Movimento": "Prestação IRS Finanças", "Valor": "-1.385,52 EUR"}
    ])
    st.dataframe(df_crono, use_container_width=True, hide_index=True)

# ========================================================
# ABA 4: HISTÓRICO & PASSIVOS
# ========================================================
with tab_historico:
    st.subheader("Estado dos Passivos de Curto Prazo")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.markdown("#### Empreiteiro (Obra na Moradia)")
        st.write(f"Saldo total em dívida: **{db['transitorio']['empreiteiro_saldo']:.2f} EUR**")
        st.write("Plano: 6 parcelas de 1.437,00 EUR (Out/26 a Mar/27)")
    with c_p2:
        st.markdown("#### Autoridade Tributária (IRS)")
        st.write(f"Saldo total em dívida: **{db['transitorio']['irs_saldo']:.2f} EUR**")
        st.write(f"Prestação atual: **{db['transitorio']['irs_prestacao_atual']} de 12** (~1.390 EUR/mês até Ago/27)")
