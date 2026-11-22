import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="Gestao Financeira Dinamica: Familia & Empresa", page_icon="⚖️", layout="wide")

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

st.title("Gestao Financeira Familiar & ElementarPrivilege")

tab_registo, tab_orcamento, tab_cronograma, tab_historico = st.tabs([
    "Registo Diario de Gastos", 
    "Orcamento & Planeamento Mensal", 
    "Cronograma Mensal por Datas",
    "Historico & Passivos"
])

# ========================================================
# ABA 1: REGISTO DIARIO DE GASTOS (COM SELECAO PESSOAL vs EMPRESA)
# ========================================================
with tab_registo:
    st.subheader("1. Lancar Novo Gasto do Dia a Dia")
    
    # SELETOR DE CONTA / ENTIDADE
    entidade_gasto = st.radio(
        "Conta / Entidade:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True
    )
    
    # Categorias adaptadas a cada entidade
    if entidade_gasto == "Pessoal Familiar":
        opcoes_cat = [
            "Takeaway & Uber Eats (Alvo de Corte)",
            "Restaurantes em Familia",
            "Supermercado & Alimentacao em Casa",
            "Criancas (Vestuario, Farmacia, Extras)",
            "Lazer Familiar, Livros e Garrafeira",
            "Combustivel Particular / Fins de Semana",
            "Margem Livre do Casal",
            "Outro Gasto Pessoal"
        ]
    else:
        opcoes_cat = [
            "Refeicao de Servico / Reuniao Clinica",
            "Combustivel de Servico / Deslocacoes",
            "Material Clinico / Consumiveis / Farmacia",
            "Livros / Formacao / Congressos Medicos",
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

    desc_gasto = st.text_input("Descricao / Detalhe (Opcional):", placeholder="Ex.: Continente, Uber Eats, Restaurante reuniao clinica, Livro ICBAS...")

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
        "Restaurantes em Familia": 350.00,
        "Supermercado & Alimentacao em Casa": 850.00,
        "Criancas (Vestuario, Farmacia, Extras)": 250.00,
        "Lazer Familiar, Livros e Garrafeira": 200.00,
        "Combustivel Particular / Fins de Semana": 150.00,
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
        st.markdown("#### Foco Prioritario Pessoal: Restauracao & Takeaway")
        
        g_take = gastos_por_cat_pes.get("Takeaway & Uber Eats (Alvo de Corte)", 0.0)
        t_take = tetos_padrao["Takeaway & Uber Eats (Alvo de Corte)"]
        sobra_take = t_take - g_take
        prog_take = min(1.0, g_take / t_take) if t_take > 0 else 1.0
        
        st.write(f"**Takeaway / Uber Eats:** Gastos **{g_take:.2f} EUR** de **{t_take:.2f} EUR** (Resta: **{sobra_take:.2f} EUR**)")
        st.progress(prog_take)
        if sobra_take < 0:
            st.error(f"Teto de Takeaway ultrapassado em {abs(sobra_take):.2f} EUR!")
        elif sobra_take <= 25:
            st.warning("Atencao: Menos de 25 EUR disponiveis para takeaway este mes.")

        g_rest = gastos_por_cat_pes.get("Restaurantes em Familia", 0.0)
        t_rest = tetos_padrao["Restaurantes em Familia"]
        sobra_rest = t_rest - g_rest
        prog_rest = min(1.0, g_rest / t_rest) if t_rest > 0 else 1.0
        
        st.write(f"**Restaurantes em Familia:** Gastos **{g_rest:.2f} EUR** de **{t_rest:.2f} EUR** (Resta: **{sobra_rest:.2f} EUR**)")
        st.progress(prog_rest)
        if sobra_rest < 0:
            st.error(f"Teto de Restaurantes ultrapassado em {abs(sobra_rest):.2f} EUR!")

    with col_t2:
        st.markdown("#### Totais de Controlo: Pessoal vs Empresa")
        g_sup = gastos_por_cat_pes.get("Supermercado & Alimentacao em Casa", 0.0)
        t_sup = tetos_padrao["Supermercado & Alimentacao em Casa"]
        sobra_sup = t_sup - g_sup
        prog_sup = min(1.0, g_sup / t_sup) if t_sup > 0 else 1.0
        
        st.write(f"**Supermercado & Casa:** Gastos **{g_sup:.2f} EUR** de **{t_sup:.2f} EUR** (Resta: **{sobra_sup:.2f} EUR**)")
        st.progress(prog_sup)

        total_gastos_pessoais = sum(gastos_por_cat_pes.values())
        teto_global = sum(tetos_padrao.values())
        sobra_global = teto_global - total_gastos_pessoais
        
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Total Variavel Pessoal", f"{total_gastos_pessoais:,.2f} EUR", f"Resta {sobra_global:,.2f} EUR")
        c_m2.metric("Total Pontual Empresa", f"{total_gasto_empresa:,.2f} EUR", "Dedutivel em IRC")

    st.divider()
    st.subheader("3. Movimentos Registados Deste Mes")
    if not gastos_df.empty:
        filtro_entidade = st.radio("Filtrar Tabela por:", ["Todos os Gastos", "Apenas Pessoal Familiar", "Apenas Empresa (ElementarPrivilege)"], horizontal=True)
        if filtro_entidade == "Apenas Pessoal Familiar":
            df_mostrar = gastos_pessoais
        elif filtro_entidade == "Apenas Empresa (ElementarPrivilege)":
            df_mostrar = gastos_empresa
        else:
            df_mostrar = gastos_df

        st.dataframe(df_mostrar[["data", "entidade", "categoria", "descricao", "valor"]].sort_values(by="data", ascending=False), use_container_width=True, hide_index=True)
        if st.button("Limpar Todos os Gastos Registados Deste Mes"):
            db["despesas_diarias"] = []
            save_data(db)
            st.rerun()
    else:
        st.info("Ainda nao ha gastos diarios registados para este mes.")

# ========================================================
# ABA 2: ORCAMENTO & PLANEAMENTO MENSAL EXAUSTIVO
# ========================================================
with tab_orcamento:
    st.subheader("1. Entradas Reais do Mes Corrente")
    st.markdown("Introduza os valores efetivamente auferidos para que o motor calcule a distribuicao exata.")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        st.markdown("**Conta Pessoal (BPI Particular)**")
        rec_ulsaave = st.number_input(
            "Vencimento Hospitalar Liquido ULSAAVE (Apenas Titular, sem Sara) [EUR]:",
            min_value=0.0,
            value=3500.0,
            step=50.0,
            help="Valor liquido transferido pela ULS do Alto Ave entre o dia 20 e 23."
        )

    with col_in2:
        st.markdown("**Conta Empresa (ElementarPrivilege - BPI Negocios)**")
        rec_empresa = st.number_input(
            "Faturacao Clinica / Cirurgica Privada Liquida [EUR]:",
            min_value=0.0,
            value=7800.0,
            step=100.0,
            help="Total faturado no Hospital da Luz, Guimadent, Espirito Santo e atividade privada."
        )

    st.divider()

    st.subheader("2. Detalhe Completo das Despesas Fixas (Validadas nos Extratos)")
    
    col_fx1, col_fx2 = st.columns(2)
    with col_fx1:
        st.markdown("#### Empresa (ElementarPrivilege - Conta BPI Negocios)")
        fx_cheque_creche = st.number_input("Cheques-Creche / Infancia dos 2 Filhos [EUR]:", value=1050.56, step=10.0, help="Faturado a empresa. Dedutivel IRC / Isento TSU e IRS.")
        fx_credito_medico = st.number_input("Credito Equipamento Medico BPI (...830-004) [EUR]:", value=1120.00, step=10.0, help="Prestacao de financiamento de equipamento clinico.")
        fx_carro = st.number_input("Credito Automovel (Volkswagen Bank GMBH) [EUR]:", value=618.79, step=10.0, help="Contrato viatura de servico da sociedade.")
        fx_tsu = st.number_input("Seguranca Social / TSU Gerencia [EUR]:", value=620.29, step=10.0, help="Guia mensal da Seguranca Social.")
        fx_aida = st.number_input("Prestacao Servicos Medicos (Aida Esteves) [EUR]:", value=963.78, step=10.0, help="Transferencia SEPA recorrente de apoio clinico.")
        fx_meo_energia = st.number_input("MEO Fibra Sede + Quota Energia Sede (~25%) [EUR]:", value=216.00, step=10.0, help="Infraestrutura de comunicacoes e energia afeta a sede.")
        fx_via_verde = st.number_input("Via Verde Pay Empresa [EUR]:", value=45.00, step=5.0, help="Portagens em servico hospitalar e cirurgico.")
        fx_software = st.number_input("Google Workspace + KnowUro.com [EUR]:", value=59.20, step=5.0, help="Ferramentas digitais e cientificas da sociedade.")
        fx_bpi_empresa = st.number_input("Comissao Conta BPI Negocios + Imposto Selo [EUR]:", value=8.31, step=1.0)
        fx_cartao_ref = st.number_input("Cartao Refeicao Gerente (Isento) [EUR]:", value=220.00, step=10.0, help="Alimentacao carregada em cartao da empresa para o supermercado.")
        
    with col_fx2:
        st.markdown("#### Pessoal Familiar (Conta BPI Particular)")
        fx_ch_003 = st.number_input("Credito Habitacao Tranche 003 (Taxa Fixa 2,7%) [EUR]:", value=2856.81, step=10.0, help="Contrato BPI n. 5579717-165-003 renegociado a taxa fixa.")
        fx_ch_004 = st.number_input("Credito Habitacao Tranche 004 (Taxa Fixa 2,7%) [EUR]:", value=722.31, step=10.0, help="Contrato BPI n. 5579717-165-004 renegociado a taxa fixa.")
        fx_seguros_ch = st.number_input("Seguros CH em Vigor (Vida + Multirriscos) [EUR]:", value=110.00, step=10.0, help="Apolices pre-existentes mantidas sem agravamento.")
        fx_empregada = st.number_input("Apoio Domestico Familiar (Empregada) [EUR]:", value=430.00, step=10.0, help="Transferencia SEPA mensal.")
        fx_eletricidade = st.number_input("Eletricidade Moradia Liquida (Gold Energy) [EUR]:", value=277.03, step=10.0, help="Valor liquido domestico (deduzida quota da sede).")
        fx_agua = st.number_input("Agua e Saneamento Residencial [EUR]:", value=50.00, step=5.0)
        fx_deco_unicef = st.number_input("Deco Proteste (16,74 EUR) + UNICEF (25,00 EUR) [EUR]:", value=41.74, step=5.0, help="Deco mantida por opcao familiar + donativo dedutivel no IRS.")
        fx_lazer_digital = st.number_input("Spotify Familiar (16,99 EUR) + Amazon Prime (4,99 EUR) [EUR]:", value=21.98, step=1.0)
        fx_bpi_pessoal = st.number_input("Comissao Conta Valor BPI + Imposto Selo [EUR]:", value=5.19, step=1.0)

    st.markdown("#### Passivos Transitorios do Mes")
    c_tr1, c_tr2 = st.columns(2)
    with c_tr1:
        tranche_empreiteiro_ativa = st.checkbox("Incluir Tranche Mensal Empreiteiro (Obra na Moradia)", value=True)
        val_empreiteiro = 1437.00 if tranche_empreiteiro_ativa else 0.00
        st.caption(f"Valor: {val_empreiteiro:.2f} EUR | Divida remanescente: {db['transitorio']['empreiteiro_saldo']:.2f} EUR (6 parcelas de Out/26 a Mar/27)")

    with c_tr2:
        prestacao_irs_ativa = st.checkbox("Incluir Prestacao Mensal IRS (Financas)", value=True)
        val_irs = 1385.52 if prestacao_irs_ativa else 0.00
        st.caption(f"Valor: {val_irs:.2f} EUR (2.a prestacao de 12) | Divida total: {db['transitorio']['irs_saldo']:.2f} EUR (Doc. Cobranca n. 2026.6193452)")

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
        transf_efetiva_empresa_pessoal = renda_sede + ajuste_gerencia
        saldo_final_empresa = saldo_operacional_empresa - transf_efetiva_empresa_pessoal
    else:
        transf_efetiva_empresa_pessoal = max(0.0, saldo_operacional_empresa)
        saldo_final_empresa = 0.0

    liquidez_disponivel_pessoal = rec_ulsaave + transf_efetiva_empresa_pessoal - total_fixo_pessoal

    teto_criancas = 250.00
    teto_supermercado_revolut = 630.00
    teto_combustivel = 150.00
    teto_lazer_livros = 200.00
    teto_livre_casal = 200.00
    teto_restaurantes = 350.00
    teto_takeaway = 100.00

    sobra = max(0.0, liquidez_disponivel_pessoal)

    aloc_criancas = min(sobra, teto_criancas)
    sobra -= aloc_criancas

    aloc_supermercado = min(sobra, teto_supermercado_revolut)
    sobra -= aloc_supermercado

    aloc_combustivel = min(sobra, teto_combustivel)
    sobra -= aloc_combustivel

    aloc_lazer = min(sobra, teto_lazer_livros)
    sobra -= aloc_lazer

    aloc_casal = min(sobra, teto_livre_casal)
    sobra -= aloc_casal

    aloc_restaurantes = min(sobra, teto_restaurantes)
    sobra -= aloc_restaurantes

    aloc_takeaway = min(sobra, teto_takeaway)
    sobra -= aloc_takeaway

    excedente_investimento = sobra

    st.divider()
    st.subheader("3. Balanco Dinamico e Alocacao em Cascata")

    c_res1, c_res2, c_res3, c_res4 = st.columns(4)
    c_res1.metric("Fixos Empresa (com Obra)", f"{total_fixo_empresa:,.2f} EUR")
    c_res2.metric("Fixos Pessoais & IRS", f"{total_fixo_pessoal:,.2f} EUR")
    c_res3.metric("Transf. Empresa -> Pessoal", f"{transf_efetiva_empresa_pessoal:,.2f} EUR", help="850 EUR Renda Sede + Ajuste Gerencia")
    c_res4.metric("Saldo Retido na Empresa", f"{saldo_final_empresa:,.2f} EUR")

    st.markdown("#### Tabela Exaustiva de Despesas Variaveis Familiares")
    st.caption("A cascata aloca primeiro as necessidades dos filhos e da casa. Restaurantes e takeaway sao preteridos se a liquidez diminuir.")

    df_var = pd.DataFrame([
        {"Ordem": "1. Essencial", "Categoria": "Criancas (Vestuario, Farmacia, Extras)", "Teto Max": f"{teto_criancas:.2f} EUR", "Aprovado": f"{aloc_criancas:.2f} EUR", "Canal": "Revolut", "Regra de Execucao": "Fundo de maneio para necessidades correntes dos 3 filhos"},
        {"Ordem": "2. Essencial", "Categoria": "Alimentacao em Casa (Supermercado / Frescos)", "Teto Max": f"{teto_supermercado_revolut:.2f} EUR", "Aprovado": f"{aloc_supermercado:.2f} EUR", "Canal": "Revolut (+220 EUR Cartao Refeicao)", "Regra de Execucao": "Produtos frescos, biologicos, peixe/carne para 5 pessoas"},
        {"Ordem": "3. Essencial", "Categoria": "Combustivel Particular / Fins de Semana", "Teto Max": f"{teto_combustivel:.2f} EUR", "Aprovado": f"{aloc_combustivel:.2f} EUR", "Canal": "Revolut", "Regra de Execucao": "Deslocacoes familiares de fim de semana (servico vai pela empresa)"},
        {"Ordem": "4. Qualidade", "Categoria": "Lazer Familiar, Livros e Garrafeira", "Teto Max": f"{teto_lazer_livros:.2f} EUR", "Aprovado": f"{aloc_lazer:.2f} EUR", "Canal": "Revolut", "Regra de Execucao": "Cinema, literatura classica e vinhos de qualidade intencionais"},
        {"Ordem": "5. Qualidade", "Categoria": "Margem Livre do Casal (100 EUR cada)", "Teto Max": f"{teto_livre_casal:.2f} EUR", "Aprovado": f"{aloc_casal:.2f} EUR", "Canal": "Revolut / Numerario", "Regra de Execucao": "Autonomia individual de 100 EUR cada sem necessidade de registo"},
        {"Ordem": "6. Preterivel", "Categoria": "Restaurantes em Familia (Convivio)", "Teto Max": f"{teto_restaurantes:.2f} EUR", "Aprovado": f"{aloc_restaurantes:.2f} EUR", "Canal": "Revolut", "Regra de Execucao": "2 a 3 almocos/jantares de convivio planeados de fim de semana"},
        {"Ordem": "7. A Cortar", "Categoria": "Takeaway & Uber Eats (Conveniencia)", "Teto Max": f"{teto_takeaway:.2f} EUR", "Aprovado": f"{aloc_takeaway:.2f} EUR", "Canal": "Revolut", "Regra de Execucao": "Teto rigido de 2 a 3 pedidos de recurso por mes (cortou ~400 EUR)"}
    ])

    st.dataframe(df_var, use_container_width=True, hide_index=True)

    total_aprovado_revolut = (aloc_criancas + aloc_supermercado + aloc_combustivel + 
                              aloc_lazer + aloc_casal + aloc_restaurantes + aloc_takeaway)

    st.info(f"Valor Exato a Transferir a Dia 01 para o Cartao Revolut Familiar: **{total_aprovado_revolut:,.2f} EUR**")

    if aloc_takeaway < teto_takeaway or aloc_restaurantes < teto_restaurantes:
        st.warning("Aviso de Restricao: As refeicoes fora ou o takeaway foram automaticamente reduzidos para proteger os compromissos fixos e os filhos.")

    if excedente_investimento > 0:
        st.success(f"Excedente Disponivel para Reforma / ETFs (Best Trading Pro): **{excedente_investimento:,.2f} EUR**")
    else:
        st.info("Investimento em Pausa: Neste mes a liquidez foi totalmente absorvida pelas despesas prioritarias. O plano de reforco em ETFs deve manter-se em pausa.")

    if st.button("Fechar e Registar Valores Deste Mes no Historico"):
        novo_registo = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "receita_pessoal": rec_ulsaave,
            "receita_empresa": rec_empresa,
            "transferencia_empresa_pessoal": transf_efetiva_empresa_pessoal,
            "teto_revolut": total_aprovado_revolut,
            "saldo_empresa": saldo_final_empresa
        }
        db["historico"].append(novo_registo)
        if tranche_empreiteiro_ativa and db["transitorio"]["empreiteiro_saldo"] > 0:
            db["transitorio"]["empreiteiro_saldo"] = max(0.0, db["transitorio"]["empreiteiro_saldo"] - val_empreiteiro)
        if prestacao_irs_ativa and db["transitorio"]["irs_saldo"] > 0:
            db["transitorio"]["irs_saldo"] = max(0.0, db["transitorio"]["irs_saldo"] - val_irs)
            db["transitorio"]["irs_prestacao_atual"] += 1
        save_data(db)
        st.success("Mes registado com sucesso! Saldos decrescentes do Empreiteiro e da Autoridade Tributaria foram atualizados.")

# ========================================================
# ABA 3: CRONOGRAMA MENSAL POR DATAS (DESCRITIVO COMPLETO)
# ========================================================
with tab_cronograma:
    st.subheader("Cronograma Mensal Sincronizado de Tesouraria")
    st.markdown("Consulte a sequencia de movimentos financeiros sincronizados com as entradas de dinheiro:")

    df_crono = pd.DataFrame([
        {"Dia": "Dia 01", "Entidade": "BPI Pessoal -> Revolut", "Movimento / Descricao": "Transferencia do Teto Variavel Familiar para o Cartao do Mes", "Valor": "-1.880,00 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 01", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Seguranca Social (TSU Gerencia: 620,29 EUR) + Aida Esteves (963,78 EUR)", "Valor": "-1.584,07 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 01", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Carregamento do Cartao Refeicao do Gerente (Isento de TSU/IRS)", "Valor": "-220,00 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 04", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Apoio Domestico Familiar (Transferencia SEPA Empregada)", "Valor": "-430,00 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 05", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Financiamento Carro (DD Volkswagen Bank GMBH)", "Valor": "-618,79 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 05", "Entidade": "Empresa -> Pessoal", "Movimento / Descricao": "Transferencia da Renda da Sede / Gabinete Medico na Moradia", "Valor": "+850,00 EUR", "Origem / Destino": "Transf. entre contas"},
        {"Dia": "Dia 08", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Emissao / Pagamento dos Cheques-Creche dos 2 Filhos", "Valor": "-1.050,56 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 10", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Credito Equipamento Medico BPI (...830-004)", "Valor": "-1.120,00 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 11 a 15", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "ENTRADA DE FATURACAO CLINICA / CIRURGICA PRIVADA", "Valor": "+7.500 a 8.500 EUR", "Origem / Destino": "Hosp. Luz, Espirito Santo, Guimadent"},
        {"Dia": "Dia 12", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Eletricidade Moradia Liquida (DD Gold Energy)", "Valor": "-277,03 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 15", "Entidade": "ElementarPrivilege", "Movimento / Descricao": "Pagamento da Tranche Mensal da Obra ao Empreiteiro (6x)", "Valor": "-1.437,00 EUR", "Origem / Destino": "BPI Negocios"},
        {"Dia": "Dia 15", "Entidade": "Empresa -> Pessoal", "Movimento / Descricao": "Transferencia do Ajuste de Tesouraria de Gerencia", "Valor": "+1.100 a 1.500 EUR", "Origem / Destino": "Transf. entre contas"},
        {"Dia": "Dia 20", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Consumos de Agua e Saneamento da Moradia", "Valor": "-50,00 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 20 a 23", "Entidade": "BPI Pessoal", "Movimento / Descricao": "ENTRADA VENCIMENTO HOSPITALAR ULSAAVE (Apenas Titular)", "Valor": "+3.500,00 EUR", "Origem / Destino": "ULS do Alto Ave"},
        {"Dia": "Dia 30", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Credito Habitacao Tranche 003 BPI (Taxa Fixa 2,7%)", "Valor": "-2.856,81 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 30", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Credito Habitacao Tranche 004 BPI (Taxa Fixa 2,7%)", "Valor": "-722,31 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 30", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Seguros CH em Vigor no BPI (Vida + Multirriscos)", "Valor": "-110,00 EUR", "Origem / Destino": "BPI Particular"},
        {"Dia": "Dia 31", "Entidade": "BPI Pessoal", "Movimento / Descricao": "Prestacao Mensal IRS (Doc. Cobranca n. 2026.6193452)", "Valor": "-1.385,52 EUR", "Origem / Destino": "Portal das Financas / D.D."}
    ])

    st.dataframe(df_crono, use_container_width=True, hide_index=True)

# ========================================================
# ABA 4: HISTORICO & PASSIVOS TRANSITORIOS
# ========================================================
with tab_historico:
    st.subheader("Estado dos Passivos de Curto Prazo")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.markdown("#### Empreiteiro (Obra na Moradia)")
        st.write(f"Saldo total em divida: **{db['transitorio']['empreiteiro_saldo']:.2f} EUR**")
        st.write("Plano acordado: 6 parcelas de 1.437,00 EUR (Outubro/2026 a Marco/2027)")
        st.caption("Ficara 100% liquidado no final do 1.o trimestre de 2027.")
    with c_p2:
        st.markdown("#### Autoridade Tributaria (Plano IRS)")
        st.write(f"Saldo total em divida: **{db['transitorio']['irs_saldo']:.2f} EUR**")
        st.write(f"Prestacao atual: **{db['transitorio']['irs_prestacao_atual']} de 12** (~1.390 EUR/mes ate 31 de Agosto de 2027)")
        st.caption("Extincao definitiva a 31 de agosto de 2027.")

    st.divider()
    st.subheader("Roteiro para Retoma da Poupanca em ETFs (Best Trading Pro)")
    st.markdown("""
    * **Ate Marco/2027 (Fase de Defesa):** Empreiteiro e IRS em curso. Aporte regular em pausa (ou aportes pontuais de 300 EUR a 500 EUR em meses com faturacao extraordinaria).
    * **Abril a Agosto/2027 (Fase de Alivio):** Empreiteiro pago. Libertam-se **+1.437,00 EUR/mes**. Retoma dos reforcos regulares de **750 EUR a 1.000 EUR/mes**.
    * **Setembro/2027 em diante (Velocidade de Cruzeiro):** IRS 100% extinto. Libertam-se adicionais **~1.400 EUR/mes**. Reforcos consistentes de **1.500 EUR a 2.200 EUR/mes** (50% MSCI World, 35% Nasdaq 100, 15% Semicondutores) rumo a meta dos 400.000 EUR a 15 anos.
    """)
    
    if db["historico"]:
        st.divider()
        st.subheader("Historico dos Meses Registados")
        st.dataframe(pd.DataFrame(db["historico"]), use_container_width=True)
