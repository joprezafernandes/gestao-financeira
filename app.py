from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestão Financeira — Pessoal & Elementarprivilege Lda.",
    page_icon="💶",
    layout="wide",
)

st.title("💶 Gestão Financeira — Pessoal & Elementarprivilege Urologia Lda.")

# Seletor principal de esfera
esfera = st.radio(
    "Seleciona a esfera de gestão:",
    ["Pessoal", "Elementarprivilege Urologia Lda."],
    horizontal=True,
)

st.divider()

hoje = date.today()

# ==============================================================================
# 1. ESFERA PESSOAL FAMILIAR
# ==============================================================================
if esfera == "Pessoal":
    st.subheader("🏠 Esfera Pessoal Familiar — Planeamento & Blindagem")

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        liquido_sns = st.number_input(
            "Vencimento Líquido SNS (mês atual, €)",
            min_value=0.0,
            value=5600.0,
            step=100.0,
        )
    with col_in2:
        despesas_casa = st.number_input(
            "Despesas Fixas & Casa (incl. 620€ Sara + teto 840€, €)",
            min_value=0.0,
            value=3400.0,
            step=50.0,
        )

    # Cálculo automático do Empréstimo Mãe (8x 500€: Dez/2026 a Jul/2027)
    inicio_mae = date(2026, 12, 1)
    if hoje < inicio_mae:
        prestacao_atual = 0
    else:
        meses_decorridos = (hoje.year - inicio_mae.year) * 12 + (
            hoje.month - inicio_mae.month
        ) + 1
        prestacao_atual = min(max(meses_decorridos, 0), 8)

    valor_mae_mes = 500.0 if prestacao_atual < 8 or (hoje.year == 2027 and hoje.month <= 7) else 0.0
    saldo_mae = max(0.0, 4000.0 - (prestacao_atual * 500.0))

    # Cativações calibradas
    provisao_irs_mes = 500.0
    dca_etf_mes = 450.0

    total_cativado = valor_mae_mes + provisao_irs_mes + dca_etf_mes
    margem_livre = liquido_sns - despesas_casa - total_cativado

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Empréstimo Mãe (500€/mês)",
        f"{saldo_mae:,.2f} € em dívida",
        f"Prestação {prestacao_atual}/8 (Termina Jul/2027)",
    )
    c2.metric(
        "Pocket IRS 2027 (À Cabeça)",
        f"{provisao_irs_mes:,.2f} €/mês",
        "Reforçar no Sub. Férias Jun/2027",
    )
    c3.metric(
        "DCA ETF (iShares MSCI World)",
        f"{dca_etf_mes:,.2f} €/mês",
        "100% IE00B4L5Y983 (Dia 20–22)",
    )
    c4.metric(
        "Margem Líquida Livre",
        f"{margem_livre:,.2f} €",
        "Após casa + cativações",
        delta_color="normal" if margem_livre >= 0 else "inverse",
    )

    st.markdown("#### Ordem de Execução no Arranque do Ciclo (Dia 20–22)")
    df_pessoal = pd.DataFrame(
        [
            {
                "Prioridade": "1. Fixos Casa & Sara",
                "Destino": "BPI Pessoal + Cartão Sara (620€)",
                "Valor (€)": despesas_casa,
                "Regra": "Cobertura base familiar + 3 dependentes",
            },
            {
                "Prioridade": "2. Amortização Mãe (0% juro)",
                "Destino": "Transferência Permanente (Dia 23)",
                "Valor (€)": valor_mae_mes,
                "Regra": f"Prestação {prestacao_atual}/8 — Empreiteiro liquidado a 0€",
            },
            {
                "Prioridade": "3. Reserva IRS 2027",
                "Destino": "Revolut Pocket 'IRS 2027'",
                "Valor (€)": provisao_irs_mes,
                "Regra": "Cobre diferencial retenção SIGIC/Urgências",
            },
            {
                "Prioridade": "4. Investimento Longo Prazo",
                "Destino": "Best Trading Pro → iShares MSCI World",
                "Valor (€)": dca_etf_mes,
                "Regra": "1 ordem única/mês (IE00B4L5Y983)",
            },
        ]
    )
    st.dataframe(df_pessoal, use_container_width=True, hide_index=True)

# ==============================================================================
# 2. ESFERA ELEMENTARPRIVILEGE UROLOGIA LDA.
# ==============================================================================
else:
    st.subheader("🏥 Elementarprivilege Urologia Lda. — Tesouraria & Fiscalidade")

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        faturacao_emp = st.number_input(
            "Faturação Bruta Mensal (€)",
            min_value=0.0,
            value=11750.0,
            step=250.0,
        )
    with col_e2:
        fixos_emp = st.number_input(
            "Encargos Fixos & Contabilidade (€)",
            min_value=0.0,
            value=3200.0,
            step=100.0,
        )

    iva_extra = 2672.26 if (hoje.year == 2026 and hoje.month in [11, 12]) else 0.0
    provisao_hotel = 1000.0 if (hoje < date(2027, 4, 1)) else 0.0
    lucro_estimado = max(0.0, faturacao_emp - fixos_emp)
    reserva_irc = round(lucro_estimado * 0.17, 2)
    credito_socio = 1300.0

    excedente_empresa = faturacao_emp - fixos_emp - reserva_irc - iva_extra - provisao_hotel

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Reserva IRC (Revolut Pocket)",
        f"{reserva_irc:,.2f} €/mês",
        "Intocável (IRC PME 16%–20%)",
    )
    c2.metric(
        "Plano IVA Extraordinário",
        f"{iva_extra:,.2f} €/mês",
        "Ativo Nov–Dez 2026" if iva_extra > 0 else "Liquidado",
    )
    c3.metric(
        "Crédito Sócio (Conta 268)",
        f"{credito_socio:,.2f} €",
        "Mac mini M4 + Ecrã AOC (Isento IRS)",
    )
    c4.metric(
        "Excedente Livre Empresa",
        f"{excedente_empresa:,.2f} €",
        "0€ para ETFs em Nov/Dez" if iva_extra > 0 else "Livre após impostos",
        delta_color="normal" if excedente_empresa >= 0 else "inverse",
    )

    st.markdown("#### Regras de Blindagem Societária")
    df_empresa = pd.DataFrame(
        [
            {
                "Rubrica": "Reserva Fiscal IRC",
                "Valor Mensal (€)": reserva_irc,
                "Estado / Ação": "Transferir imediatamente para Pocket IRC",
            },
            {
                "Rubrica": "Prestação IVA (Nov/Dez 2026)",
                "Valor Mensal (€)": iva_extra,
                "Estado / Ação": "Exclusivo da empresa — nunca misturar com BPI Pessoal",
            },
            {
                "Rubrica": "Provisão Hotel (até Mar/2027)",
                "Valor Mensal (€)": provisao_hotel,
                "Estado / Ação": "Cativar até perfazer 6.500 €",
            },
            {
                "Rubrica": "Reembolso Sócio (PC + Ecrã)",
                "Valor Mensal (€)": credito_socio,
                "Estado / Ação": "Transferir 1.300 € exatos p/ BPI Pessoal (enviar faturas a geral@amige.pt)",
            },
        ]
    )
    st.dataframe(df_empresa, use_container_width=True, hide_index=True)
