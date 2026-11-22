import time
from datetime import date
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Gestão Financeira — Pessoal & ElementarPrivilege",
    page_icon="💶",
    layout="wide",
)

# ==============================================================================
# LIGAÇÃO AUTOMÁTICA VIA SECRETS (OU BARRA LATERAL SE NECESSÁRIO)
# ==============================================================================
secret_url = ""
try:
    secret_url = st.secrets.get("WEBHOOK_URL", "")
except Exception:
    secret_url = ""

with st.sidebar:
    st.header("⚙️ Ligação Google Sheets")
    webhook_url = st.text_input(
        "Link /exec do Apps Script:",
        value=secret_url,
        placeholder="https://script.google.com/macros/s/AKfycb.../exec",
    ).strip()

st.title("💶 Gestão Financeira — Pessoal & Empresa")

ORIGENS_GANHOS_EMPRESA = [
    "Luz Guimarães",
    "Luz Vila Real",
    "IPG",
    "Consultório Fafe",
    "Consultório Chaves",
    "Açores",
    "Outros",
]


def parse_valor_pt(texto: str) -> float:
    """Converte '125,50' ou '125.50' ou '1 250,00 €' para float sem bloquear no teclado do telemóvel."""
    if not texto:
        return 0.0
    limpo = (
        texto.strip()
        .replace("€", "")
        .replace(" ", "")
        .replace(",", ".")
    )
    try:
        return round(float(limpo), 2)
    except ValueError:
        return -1.0


def carregar_movimentos(url: str) -> pd.DataFrame:
    """Lê os movimentos diretamente via Apps Script (doGet)."""
    if not url or not url.startswith("http"):
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])
    try:
        resp = requests.get(url, params={"t": int(time.time())}, timeout=12)
        resp.raise_for_status()
        df = pd.DataFrame(resp.json())
        if df.empty:
            return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])
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
        st.warning(f"Erro ao ler a folha ({e}). Confirma o link /exec nos Secrets.")
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])


def enviar_movimento(url: str, payload: dict) -> tuple[bool, str]:
    """Grava um novo registo no Google Sheets via Apps Script (doPost)."""
    if not url or not url.startswith("http"):
        return False, "Falta configurar o link /exec nos Secrets do Streamlit."
    try:
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            return True, "Gravado com sucesso!"
        return False, f"Erro HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Erro de ligação: {e}"


# ==============================================================================
# SEPARADORES DA APLICAÇÃO
# ==============================================================================
tab_registo, tab_movimentos, tab_planeamento = st.tabs(
    [
        "📝 Registo Rápido",
        "📒 Movimentos & Totais",
        "🛡️ Planeamento",
    ]
)

# ------------------------------------------------------------------------------
# ABA 1: REGISTO RÁPIDO (OTIMIZADO PARA TELEMÓVEL)
# ------------------------------------------------------------------------------
with tab_registo:
    entidade = st.radio(
        "Entidade",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    if entidade == "Pessoal Familiar":
        tipo_movimento = "Despesa"
        categorias = [
            "Supermercado & Alimentacao",
            "Habitacao / Energia / Casa",
            "Filhos & Educacao",
            "Saude & Suplementos",
            "Lazer/Livros/Garrafeira",
            "Outro",
        ]
    else:
        tipo_movimento = st.radio(
            "Tipo de Movimento",
            ["Entrada / Ganho Clínica", "Despesa / Encargo Empresa"],
            horizontal=True,
        )
        if tipo_movimento == "Entrada / Ganho Clínica":
            categorias = [f"Ganho - {origem}" for origem in ORIGENS_GANHOS_EMPRESA]
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
        data_mov = st.date_input("Data", value=date.today())
        label_cat = (
            "Origem / Clínica"
            if tipo_movimento == "Entrada / Ganho Clínica"
            else "Categoria"
        )
        categoria = st.selectbox(label_cat, categorias)

        valor_str = st.text_input(
            "Valor (€)",
            placeholder="Ex.: 45,50 ou 1250",
        )

        placeholder_desc = (
            "Ex.: Honorários Outubro, Aquablation..."
            if tipo_movimento == "Entrada / Ganho Clínica"
            else "Ex.: Celeiro, Lidl, Via Verde..."
        )
        descricao = st.text_input("Descrição / Referência", placeholder=placeholder_desc)

        if st.form_submit_button("✅ Gravar Movimento", use_container_width=True):
            valor_num = parse_valor_pt(valor_str)
            if valor_num <= 0:
                st.error("Introduz um valor válido maior que zero (ex.: 25,50).")
            else:
                desc_final = descricao.strip() if descricao.strip() else categoria
                payload = {
                    "data": data_mov.strftime("%Y-%m-%d"),
                    "entidade": entidade,
                    "categoria": categoria,
                    "descricao": desc_final,
                    "valor": valor_num,
                }
                ok, msg = enviar_movimento(webhook_url, payload)
                if ok:
                    st.success(f"{msg} ({payload['data']} | {categoria} — {desc_final}: {valor_num:,.2f} €)")
                else:
                    st.error(msg)

# ------------------------------------------------------------------------------
# ABA 2: MOVIMENTOS, ENTRADAS POR CLÍNICA & TOTAIS
# ------------------------------------------------------------------------------
with tab_movimentos:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.rerun()

    df = carregar_movimentos(webhook_url)

    if not df.empty:
        df["categoria_str"] = df["categoria"].astype(str)
        mask_ganhos_emp = (df["entidade"] == "Empresa (ElementarPrivilege)") & (
            df["categoria_str"].str.startswith("Ganho - ")
        )
        mask_desp_emp = (df["entidade"] == "Empresa (ElementarPrivilege)") & (~mask_ganhos_emp)
        mask_desp_pessoal = df["entidade"] == "Pessoal Familiar"

        total_ganhos_emp = df.loc[mask_ganhos_emp, "valor"].sum()
        total_desp_emp = df.loc[mask_desp_emp, "valor"].sum()
        total_desp_pessoal = df.loc[mask_desp_pessoal, "valor"].sum()

        m1, m2 = st.columns(2)
        m1.metric("Entradas Empresa", f"{total_ganhos_emp:,.2f} €")
        m2.metric("Saídas Empresa", f"{total_desp_emp:,.2f} €")

        m3, m4 = st.columns(2)
        m3.metric("Saldo Líquido Empresa", f"{(total_ganhos_emp - total_desp_emp):,.2f} €")
        m4.metric("Despesas Pessoal", f"{total_desp_pessoal:,.2f} €")

        st.markdown("#### 🏥 Entradas por Clínica / Origem")
        resumo_clinicas = []
        for origem in ORIGENS_GANHOS_EMPRESA:
            cat_alvo = f"Ganho - {origem}"
            val_origem = df.loc[mask_ganhos_emp & (df["categoria_str"] == cat_alvo), "valor"].sum()
            qtd_origem = int((mask_ganhos_emp & (df["categoria_str"] == cat_alvo)).sum())
            resumo_clinicas.append(
                {
                    "Origem": origem,
                    "Registos": qtd_origem,
                    "Total (€)": val_origem,
                }
            )
        df_clinicas = pd.DataFrame(resumo_clinicas)
        st.dataframe(
            df_clinicas,
            use_container_width=True,
            hide_index=True,
            column_config={"Total (€)": st.column_config.NumberColumn(format="%.2f €")},
        )

        st.divider()
        st.markdown("#### 📋 Histórico Completo")
        filtro_entidade = st.multiselect(
            "Filtrar por Entidade:",
            options=df["entidade"].dropna().unique().tolist(),
            default=df["entidade"].dropna().unique().tolist(),
        )
        df_filtrado = df[df["entidade"].isin(filtro_entidade)].drop(columns=["categoria_str"])
        st.dataframe(df_filtrado.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Sem movimentos carregados. Verifica o link /exec nos Secrets.")

# ------------------------------------------------------------------------------
# ABA 3: PLANEAMENTO & BLINDAGEM FISCAL
# ------------------------------------------------------------------------------
with tab_planeamento:
    hoje = date.today()
    esfera_plan = st.radio(
        "Esfera:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    if esfera_plan == "Pessoal Familiar":
        liquido_sns = st.number_input("Vencimento Líquido SNS (€)", value=5600.0, step=100.0)
        despesas_casa = st.number_input("Despesas Fixas & Casa (€)", value=3400.0, step=50.0)

        provisao_irs_mes = 500.0
        dca_etf_mes = 450.0
        margem_livre = liquido_sns - despesas_casa - provisao_irs_mes - dca_etf_mes

        c1, c2, c3 = st.columns(3)
        c1.metric("Pocket IRS 2027", f"{provisao_irs_mes:,.2f} €/mês")
        c2.metric("DCA iShares MSCI World", f"{dca_etf_mes:,.2f} €/mês")
        c3.metric("Margem Líquida Livre", f"{margem_livre:,.2f} €")

    else:
        entradas_mes_atual = 0.0
        if not df.empty and "data" in df.columns:
            prefixo_mes = hoje.strftime("%Y-%m")
            mask_mes = (
                (df["entidade"] == "Empresa (ElementarPrivilege)")
                & (df["categoria"].astype(str).str.startswith("Ganho - "))
                & (df["data"].astype(str).str.startswith(prefixo_mes))
            )
            entradas_mes_atual = float(df.loc[mask_mes, "valor"].sum())

        valor_default_fat = entradas_mes_atual if entradas_mes_atual > 0 else 11750.0
        faturacao_emp = st.number_input(
            f"Entradas Mensais (€) [Registado este mês: {entradas_mes_atual:,.2f} €]",
            value=valor_default_fat,
            step=250.0,
        )
        fixos_emp = st.number_input("Encargos Fixos & Contabilidade (€)", value=3200.0, step=100.0)

        iva_extra = 2672.26 if (hoje.year == 2026 and hoje.month in [11, 12]) else 0.0
        provisao_hotel = 1000.0 if (hoje < date(2027, 4, 1)) else 0.0
        reserva_irc = round(max(0.0, faturacao_emp - fixos_emp) * 0.17, 2)
        credito_socio = 1300.0
        excedente_emp = faturacao_emp - fixos_emp - reserva_irc - iva_extra - provisao_hotel

        c1, c2 = st.columns(2)
        c1.metric("Reserva IRC (17%)", f"{reserva_irc:,.2f} €/mês")
        c2.metric("IVA Extraordinário", f"{iva_extra:,.2f} €/mês")

        c3, c4 = st.columns(2)
        c3.metric("Crédito Sócio (Conta 268)", f"{credito_socio:,.2f} €")
        c4.metric("Excedente Livre Empresa", f"{excedente_emp:,.2f} €")
