from datetime import date
import pandas as pd
import streamlit as st


def render_planeamento_e_blindagem(
    esfera: str,
    liquido_sns_mes: float = 5600.0,
    despesas_casa_mes: float = 3400.0,
    faturacao_empresa_mes: float = 11750.0,
    fixos_empresa_mes: float = 3200.0,
    data_referencia: date | None = None,
) -> None:
    """
    Módulo de fecho de ciclo, cativação à cabeça (DCA + IRS + Passivos)
    e reconciliação da Conta Corrente de Sócio (Elementarprivilege Lda.).
    """
    hoje = data_referencia or date.today()

    st.subheader("📊 Planeamento de Ciclo & Blindagem Automática")

    # =========================================================================
    # 1. ESFERA PESSOAL FAMILIAR
    # =========================================================================
    if esfera.lower() == "pessoal":
        # Cálculo automático da prestação Empréstimo Mãe (8x 500€: Dez/2026 a Jul/2027)
        inicio_mae = date(2026, 12, 1)
        if hoje < inicio_mae:
            prestacao_atual = 0
        else:
            meses_decorridos = (hoje.year - inicio_mae.year) * 12 + (
                hoje.month - inicio_mae.month
            ) + 1
            prestacao_atual = min(max(meses_decorridos, 0), 8)

        valor_mae_mes = 500.0 if prestacao_atual < 8 or hoje.month <= 7 and hoje.year == 2027 else 0.0
        saldo_remanescente_mae = max(0.0, 4000.0 - (prestacao_atual * 500.0))

        # Cativações mensais fixas (valores realistas calibrados)
        provisao_irs_mes = 500.0
        dca_msci_world_mes = 450.0  # Intervalo recomendado: 400€ - 500€/mês

        total_cativado_cabeca = valor_mae_mes + provisao_irs_mes + dca_msci_world_mes
        margem_livre_final = liquido_sns_mes - despesas_casa_mes - total_cativado_cabeca

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Empréstimo Mãe (500€/mês)",
            f"{saldo_remanescente_mae:,.2f} € em dívida",
            f"Prestação {prestacao_atual}/8 (Termina Jul/2027)",
        )
        c2.metric(
            "Pocket IRS 2027 (À Cabeça)",
            f"{provisao_irs_mes:,.2f} €/mês",
            "Reforçar no Sub. Férias Jun/2027",
        )
        c3.metric(
            "DCA ETF (MSCI World)",
            f"{dca_msci_world_mes:,.2f} €/mês",
            "100% IE00B4L5Y983 (Dia 20-22)",
        )
        c4.metric(
            "Margem Líquida Livre",
            f"{margem_livre_final:,.2f} €",
            "Após casa + cativações",
            delta_color="normal" if margem_livre_final >= 0 else "inverse",
        )

        st.markdown("#### Ordem de Execução no Arranque do Ciclo (Dia 20–22)")
        df_pessoal = pd.DataFrame(
            [
                {
                    "Prioridade": "1. Fixos Casa & Sara",
                    "Destino": "BPI Pessoal + Cartão Sara (620€)",
                    "Valor (€)": despesas_casa_mes,
                    "Regra": "Cobertura base familiar + 3 dependentes",
                },
                {
                    "Prioridade": "2. Amortização Mãe (0% juro)",
                    "Destino": "Transferência Permanente (Dia 23)",
                    "Valor (€)": valor_mae_mes,
                    "Regra": f"Prestação {prestacao_atual}/8 — Dívida empreiteiro liquidada",
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
                    "Valor (€)": dca_msci_world_mes,
                    "Regra": "1 ordem única/mês; não reforçar Nasdaq/Semicond.",
                },
            ]
        )
        st.dataframe(df_pessoal, use_container_width=True, hide_index=True)

    # =========================================================================
    # 2. ESFERA ELEMENTARPRIVILEGE UROLOGIA LDA.
    # =========================================================================
    else:
        # Prestação extraordinária IVA (apenas Nov e Dez 2026)
        iva_extra_mes = 2672.26 if (hoje.year == 2026 and hoje.month in [11, 12]) else 0.0
        provisao_hotel_mes = 1000.0 if (hoje < date(2027, 4, 1)) else 0.0

        # Estimativa de lucro tributável e Reserva IRC (16% PME até 50k€)
        lucro_estimado = max(0.0, faturacao_empresa_mes - fixos_empresa_mes)
        reserva_irc_mes = round(lucro_estimado * 0.17, 2)  # Margem prudencial 17%

        # Crédito Conta Corrente Sócio (268): Mac mini M4 + Ecrã AOC OLED
        credito_socio_equipamento = 1300.0

        excedente_tesouraria = (
            faturacao_empresa_mes
            - fixos_empresa_mes
            - reserva_irc_mes
            - iva_extra_mes
            - provisao_hotel_mes
        )

        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Reserva IRC (Revolut Pocket)",
            f"{reserva_irc_mes:,.2f} €/mês",
            "Intocável (IRC PME 16%-20%)",
        )
        c2.metric(
            "Plano IVA Extraordinário",
            f"{iva_extra_mes:,.2f} €/mês",
            "Ativo Nov–Dez 2026" if iva_extra_mes > 0 else "Liquidado",
        )
        c3.metric(
            "Crédito Sócio (Conta 268)",
            f"{credito_socio_equipamento:,.2f} €",
            "Mac mini M4 + Ecrã AOC (Isento IRS)",
        )
        c4.metric(
            "Excedente Livre Empresa",
            f"{excedente_tesouraria:,.2f} €",
            "0€ para ETFs em Nov/Dez" if iva_extra_mes > 0 else "Disponível p/ reserva/invest.",
            delta_color="normal" if excedente_tesouraria >= 0 else "inverse",
        )

        st.markdown("#### Regras de Blindagem Societária (`Elementarprivilege Lda.`)")
        df_empresa = pd.DataFrame(
            [
                {
                    "Rubrica": "Reserva Fiscal IRC",
                    "Valor Mensal (€)": reserva_irc_mes,
                    "Estado / Ação": "Transferir imediatamente para Pocket IRC",
                },
                {
                    "Rubrica": "Prestação IVA (Nov/Dez 2026)",
                    "Valor Mensal (€)": iva_extra_mes,
                    "Estado / Ação": "Exclusivo da empresa — nunca misturar com BPI Pessoal",
                },
                {
                    "Rubrica": "Provisão Hotel (até Mar/2027)",
                    "Valor Mensal (€)": provisao_hotel_mes,
                    "Estado / Ação": "Cativar até perfazer 6.500 €",
                },
                {
                    "Rubrica": "Reembolso Sócio (PC + Ecrã)",
                    "Valor Mensal (€)": credito_socio_equipamento,
                    "Estado / Ação": "Transferir 1.300 € exatos p/ BPI Pessoal (enviar faturas a geral@amige.pt)",
                },
            ]
        )
        st.dataframe(df_empresa, use_container_width=True, hide_index=True)
