import time
from datetime import date
import pandas as pd
import requests
import streamlit as st

# ==============================================================================
# CONFIGURAÇÃO DA LIGAÇÃO AO GOOGLE SHEETS & APPS SCRIPT
# ==============================================================================
SHEET_ID = "1Vb2N6bwiU3XTCGTNGXgocYgnTBePxnsoUOfjrPy7RsU"
SHEET_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
)

# Cola aqui o teu URL /exec (Extensões -> Apps Script -> Implementar -> Gerir implementações)
WEBHOOK_URL = "COLE_AQUI_O_SEU_URL_EXEC_DO_APPS_SCRIPT"

st.set_page_config(
    page_title="Gestão Financeira — Dia a Dia & Planeamento",
    page_icon="💶",
    layout="wide",
)

st.title("💶 Gestão Financeira — Pessoal Familiar & ElementarPrivilege")

# ==============================================================================
# FUNÇÕES DE LEITURA E ESCRITA (GOOGLE SHEETS)
# ==============================================================================
def carregar_movimentos() -> pd.DataFrame:
    """Lê os movimentos diretamente do Google Sheets forçando atualização sem cache."""
    url_sem_cache = f"{SHEET_CSV_URL}&t={int(time.time())}"
    try:
        df = pd.read_csv(url_sem_cache, decimal=",")
        df.columns = [c.strip().lower() for c in df.columns]
        if "valor" in df.columns:
            df["valor"] = (
                df["valor"]
                .astype(str)
                .str.replace("€", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0.0)
        return df
    except Exception as e:
        st.warning(f"Não foi possível ler a folha em tempo real ({e}). Verifica se a partilha está ativa.")
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])


def enviar_movimento_webhook(payload: dict) -> tuple[bool, str]:
    """Envia novo registo para o Google Apps Script (doPost)."""
    if "COLE_AQUI" in WEBHOOK_URL or not WEBHOOK_URL.startswith("http"):
        return False, "Falta colar o URL /exec do Apps Script na variável WEBHOOK_URL no topo do app.py."
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=12)
        if resp.status_code == 200:
            return True, "Movimento registado com sucesso no Google Sheets!"
        return False, f"Erro HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Falha de ligação ao webhook: {e}"


# ==============================================================================
# NAVEGAÇÃO PRINCIPAL (3 SEPARADORES)
# ==============================================================================
tab_registo, tab_movimentos, tab_planeamento = st.tabs(
    [
        "📝 Registo Rápido (Dia a Dia)",
        "📒 Movimentos & Totais (Sheets)",
        "🛡️ Planeamento & Blindagem",
    ]
)

# ------------------------------------------------------------------------------
# SEPARADOR 1: REGISTO RÁPIDO DO DIA A DIA (SUBSTITUI A APP PERDIDA)
# ------------------------------------------------------------------------------
with tab_registo:
    st.subheader("Registar Nova Despesa / Movimento")

    entidade = st.radio(
        "Entidade",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    # Categorias exatas da tua folha Gestao_Financeira_Movimentos
    if entidade == "Pessoal Familiar":
        categorias = [
            "Supermercado & Alimentacao",
            "Habitacao / Energia / Casa",
            "Filhos & Educacao",
            "Saude & Suplementos",
            "Lazer/Livros/Garrafeira",
            "Emprestimo Mae (1/8 a 8/8)",
            "Outro",
        ]
    else:
        categorias = [
            "Refeicao Servico",
            "Via Verde / Combustivel (Empresa)",
            "Equipamento / Informatica",
            "Formacao / Congressos",
            "Contabilidade / Impostos",
            "Reembolso Socio (Conta 268)",
            "Outro",
        ]

    with st.form("form_registo_diario", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            data_mov = st.date_input("Data", value=date.today())
            categoria = st.selectbox("Categoria", categorias)
        with c2:
            valor = st.number_input("Valor (€)", min_value=0.01, step=1.0, format="%.2f")
            descricao = st.text_input(
                "Descrição / Estabelecimento",
                placeholder="Ex.: Celeiro, Lidl, Via Verde Guimarães-Chaves, Almoço Luz...",
            )

        submetido = st.form_submit_button("✅ Gravar no Google Sheets", use_container_width=True)

        if submetido:
            desc_final = descricao.strip() if descricao.strip() else categoria
            payload = {
                "data": data_mov.strftime("%Y-%m-%d"),
                "entidade": entidade,
                "categoria": categoria,
                "descricao": desc_final,
                "valor": round(float(valor), 2),
            }
            ok, msg = enviar_movimento_webhook(payload)
            if ok:
                st.success(f"{msg} ({payload['data']} | {entidade} | {desc_final}: {valor:.2f} €)")
            else:
                st.error(msg)

# ------------------------------------------------------------------------------
# SEPARADOR 2: CONSULTA E RESUMO DA FOLHA GOOGLE SHEETS
# ------------------------------------------------------------------------------
with tab_movimentos:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader("Histórico Sincronizado (`Gestao_Financeira_Movimentos`)")
    with col_t2:
        if st.button("🔄 Atualizar Dados", use_container_width=True):
            st.rerun()

    df = carregar_movimentos()

    if not df.empty:
        filtro_entidade = st.multiselect(
            "Filtrar por Entidade:",
            options=df["entidade"].dropna().unique().tolist(),
            default=df["entidade"].dropna().unique().tolist(),
        )
        df_filtrado = df[df["entidade"].isin(filtro_entidade)].copy()

        total_pessoal = df[df["entidade"] == "Pessoal Familiar"]["valor"].sum()
        total_empresa = df[df["entidade"] == "Empresa (ElementarPrivilege)"]["valor"].sum()

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Pessoal Familiar (Registos)", f"{total_pessoal:,.2f} €")
        m2.metric("Total Empresa (Registos)", f"{total_empresa:,.2f} €")
        m3.metric("Total Geral Registado", f"{(total_pessoal + total_empresa):,.2f} €")

        st.dataframe(
            df_filtrado.iloc[::-1],  # Mais recentes primeiro
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sem registos carregados ou folha inacessível no momento.")

# ------------------------------------------------------------------------------
# SEPARADOR 3: PLANEAMENTO DE CICLO & BLINDAGEM FISCAL
# ------------------------------------------------------------------------------
with tab_planeamento:
    hoje = date.today()
    esfera_plan = st.radio(
        "Esfera de Planeamento:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    if esfera_plan == "Pessoal Familiar":
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            liquido_sns = st.number_input("Vencimento Líquido SNS (€)", value=5600.0, step=100.0)
        with col_in2:
            despesas_casa = st.number_input("Despesas Fixas & Casa (€)", value=3400.0, step=50.0)

        inicio_mae = date(2026, 12, 1)
        if hoje < inicio_mae:
            prestacao_atual = 0
        else:
            meses_decorridos = (hoje.year - inicio_mae.year) * 12 + (hoje.month - inicio_mae.month) + 1
            prestacao_atual = min(max(meses_decorridos, 0), 8)

        valor_mae_mes = 500.0 if prestacao_atual < 8 or (hoje.year == 2027 and hoje.month <= 7) else 0.0
        saldo_mae = max(0.0, 4000.0 - (prestacao_atual * 500.0))
        provisao_irs_mes = 500.0
        dca_etf_mes = 450.0
        margem_livre = liquido_sns - despesas_casa - (valor_mae_mes + provisao_irs_mes + dca_etf_mes)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Empréstimo Mãe (500€/mês)", f"{saldo_mae:,.2f} €", f"Prestação {prestacao_atual}/8")
        c2.metric("Pocket IRS 2027", f"{provisao_irs_mes:,.2f} €/mês", "Reforçar Sub. Férias Jun/27")
        c3.metric("DCA iShares MSCI World", f"{dca_etf_mes:,.2f} €/mês", "IE00B4L5Y983 (Dia 20-22)")
        c4.metric("Margem Líquida Livre", f"{margem_livre:,.2f} €")

    else:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            faturacao_emp = st.number_input("Faturação Bruta Mensal (€)", value=11750.0, step=250.0)
        with col_e2:
            fixos_emp = st.number_input("Encargos Fixos & Contabilidade (€)", value=3200.0, step=100.0)

        iva_extra = 2672.26 if (hoje.year == 2026 and hoje.month in [11, 12]) else 0.0
        provisao_hotel = 1000.0 if (hoje < date(2027, 4, 1)) else 0.0
        reserva_irc = round(max(0.0, faturacao_emp - fixos_emp) * 0.17, 2)
        credito_socio = 1300.0
        excedente_emp = faturacao_emp - fixos_emp - reserva_irc - iva_extra - provisao_hotel

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Reserva IRC (Pocket)", f"{reserva_irc:,.2f} €/mês", "Intocável")
        c2.metric("IVA Extraordinário", f"{iva_extra:,.2f} €/mês", "Nov–Dez 2026")
        c3.metric("Crédito Sócio (Conta 268)", f"{credito_socio:,.2f} €", "Mac mini + Ecrã (Isento IRS)")
        c4.metric("Excedente Livre Empresa", f"{excedente_emp:,.2f} €")
