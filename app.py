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

st.title("💶 Gestão Financeira")

ORIGENS_GANHOS_EMPRESA = [
    "Luz Guimarães",
    "Luz Vila Real",
    "IPG",
    "Consultório Fafe",
    "Consultório Chaves",
    "Açores",
    "Outros",
]

ORIGENS_GANHOS_PESSOAL = [
    "Vencimento SNS",
    "Subsídio Férias / Natal",
    "Reembolso IRS / Outros Pessoais",
]


def parse_valor_pt(texto: str, default: float = 0.0) -> float:
    if not texto or not str(texto).strip():
        return default
    limpo = str(texto).strip().replace("€", "").replace(" ", "").replace(",", ".")
    try:
        return round(float(limpo), 2)
    except ValueError:
        return -1.0


def obter_intervalo_ciclo(ref: date) -> tuple[date, date]:
    """Devolve (inicio, fim) do ciclo financeiro de dia 21 a dia 20."""
    if ref.day >= 21:
        inicio = date(ref.year, ref.month, 21)
        if ref.month == 12:
            fim = date(ref.year + 1, 1, 20)
        else:
            fim = date(ref.year, ref.month + 1, 20)
    else:
        fim = date(ref.year, ref.month, 20)
        if ref.month == 1:
            inicio = date(ref.year - 1, 12, 21)
        else:
            inicio = date(ref.year, ref.month - 1, 21)
    return inicio, fim


def carregar_movimentos(url: str) -> pd.DataFrame:
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
        st.warning(f"Erro ao ler a folha ({e}).")
        return pd.DataFrame(columns=["data", "entidade", "categoria", "descricao", "valor"])


def enviar_movimento(url: str, payload: dict) -> tuple[bool, str]:
    if not url or not url.startswith("http"):
        return False, "Falta o link /exec nos Secrets do Streamlit Cloud."
    try:
        resp = requests.post(url, json=payload, timeout=12)
        if resp.status_code == 200:
            return True, "Gravado com sucesso!"
        return False, f"Erro HTTP {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Erro de ligação: {e}"


tab_registo, tab_movimentos, tab_planeamento = st.tabs(
    ["📝 Registo", "📒 Movimentos & Totais", "🛡️ Planeamento"]
)

# ------------------------------------------------------------------------------
# ABA 1: REGISTO DIRETO
# ------------------------------------------------------------------------------
with tab_registo:
    entidade = st.radio(
        "Entidade",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    if entidade == "Pessoal Familiar":
        tipo_movimento = st.radio(
            "Tipo",
            ["Despesa Pessoal", "Entrada / Vencimento Pessoal"],
            horizontal=True,
        )
        if tipo_movimento == "Entrada / Vencimento Pessoal":
            categorias = [f"Ganho Pessoal - {origem}" for origem in ORIGENS_GANHOS_PESSOAL]
        else:
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
            "Tipo",
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

    data_mov = st.date_input("Data", value=date.today())
    is_entrada = tipo_movimento.startswith("Entrada")
    categoria = st.selectbox(
        "Origem" if is_entrada else "Categoria",
        categorias,
    )
    valor_str = st.text_input("Valor (€)", key="input_valor_mov", placeholder="Ex: 5600 ou 25,50")
    descricao = st.text_input("Descrição", key="input_desc_mov", placeholder="Opcional")

    if st.button("✅ Gravar Movimento", type="primary", use_container_width=True):
        valor_num = parse_valor_pt(valor_str, default=0.0)
        if valor_num <= 0:
            st.error("Escreve um valor válido (ex: 5600 ou 25,50).")
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
# ABA 2: MOVIMENTOS E TOTAIS (FILTRADO POR CICLO 21 -> 20 POR DEFEITO)
# ------------------------------------------------------------------------------
with tab_movimentos:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

    df_raw = carregar_movimentos(webhook_url)
    inicio_ciclo, fim_ciclo = obter_intervalo_ciclo(date.today())

    periodo_opcao = st.radio(
        "Período de Análise:",
        [
            f"Ciclo Atual ({inicio_ciclo.strftime('%d/%m')} a {fim_ciclo.strftime('%d/%m')})",
            "Todo o Histórico Acumulado",
        ],
        horizontal=True,
    )

    if not df_raw.empty:
        df_raw["data_dt"] = pd.to_datetime(df_raw["data"], errors="coerce").dt.date
        if periodo_opcao.startswith("Ciclo Atual"):
            df = df_raw[(df_raw["data_dt"] >= inicio_ciclo) & (df_raw["data_dt"] <= fim_ciclo)].copy()
        else:
            df = df_raw.copy()

        df["categoria_str"] = df["categoria"].astype(str)

        # Totais Empresa
        mask_ganhos_emp = (df["entidade"] == "Empresa (ElementarPrivilege)") & (
            df["categoria_str"].str.startswith("Ganho - ")
        )
        mask_desp_emp = (df["entidade"] == "Empresa (ElementarPrivilege)") & (~mask_ganhos_emp)

        # Totais Pessoal Familiar
        mask_ganhos_pessoal = (df["entidade"] == "Pessoal Familiar") & (
            df["categoria_str"].str.startswith("Ganho Pessoal - ")
        )
        mask_desp_pessoal = (df["entidade"] == "Pessoal Familiar") & (~mask_ganhos_pessoal)

        total_ganhos_emp = df.loc[mask_ganhos_emp, "valor"].sum()
        total_desp_emp = df.loc[mask_desp_emp, "valor"].sum()
        total_ganhos_pessoal = df.loc[mask_ganhos_pessoal, "valor"].sum()
        total_desp_pessoal = df.loc[mask_desp_pessoal, "valor"].sum()

        st.markdown("#### 🏢 Resumo Empresa (ElementarPrivilege)")
        e1, e2, e3 = st.columns(3)
        e1.metric("Entradas Empresa", f"{total_ganhos_emp:,.2f} €")
        e2.metric("Saídas Empresa", f"{total_desp_emp:,.2f} €")
        e3.metric("Saldo Líquido Empresa", f"{(total_ganhos_emp - total_desp_emp):,.2f} €")

        st.markdown("#### 🏠 Resumo Pessoal Familiar")
        p1, p2, p3 = st.columns(3)
        p1.metric("Vencimento / Entradas Pessoais", f"{total_ganhos_pessoal:,.2f} €")
        p2.metric("Despesas Pessoais", f"{total_desp_pessoal:,.2f} €")
        p3.metric("Saldo Líquido Pessoal", f"{(total_ganhos_pessoal - total_desp_pessoal):,.2f} €")

        st.divider()
        st.markdown("#### 🏥 Entradas por Clínica (Empresa)")
        resumo_clinicas = []
        for origem in ORIGENS_GANHOS_EMPRESA:
            cat_alvo = f"Ganho - {origem}"
            val_origem = df.loc[mask_ganhos_emp & (df["categoria_str"] == cat_alvo), "valor"].sum()
            qtd_origem = int((mask_ganhos_emp & (df["categoria_str"] == cat_alvo)).sum())
            resumo_clinicas.append({"Origem": origem, "Qtd": qtd_origem, "Total (€)": val_origem})
        st.dataframe(
            pd.DataFrame(resumo_clinicas),
            use_container_width=True,
            hide_index=True,
            column_config={"Total (€)": st.column_config.NumberColumn(format="%.2f €")},
        )

        st.divider()
        st.markdown("#### 📋 Movimentos do Período")
        cols_mostrar = [c for c in ["data", "entidade", "categoria", "descricao", "valor"] if c in df.columns]
        st.dataframe(df[cols_mostrar].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Sem movimentos carregados.")

# ------------------------------------------------------------------------------
# ABA 3: PLANEAMENTO
# ------------------------------------------------------------------------------
with tab_planeamento:
    hoje = date.today()
    inicio_ciclo_p, fim_ciclo_p = obter_intervalo_ciclo(hoje)
    esfera_plan = st.radio(
        "Esfera:",
        ["Pessoal Familiar", "Empresa (ElementarPrivilege)"],
        horizontal=True,
    )

    if esfera_plan == "Pessoal Familiar":
        entradas_pessoal_ciclo = 0.0
        if not df_raw.empty and "data_dt" in df_raw.columns:
            mask_ciclo_p = (
                (df_raw["entidade"] == "Pessoal Familiar")
                & (df_raw["categoria"].astype(str).str.startswith("Ganho Pessoal - "))
                & (df_raw["data_dt"] >= inicio_ciclo_p)
                & (df_raw["data_dt"] <= fim_ciclo_p)
            )
            entradas_pessoal_ciclo = float(df_raw.loc[mask_ciclo_p, "valor"].sum())

        default_sns_str = (
            f"{entradas_pessoal_ciclo:.2f}".replace(".", ",") if entradas_pessoal_ciclo > 0 else "5600"
        )
        sns_str = st.text_input("Vencimento / Entradas Pessoais (€)", value=default_sns_str, key="plan_sns")
        casa_str = st.text_input("Despesas Fixas & Casa (€)", value="3400", key="plan_casa")

        liquido_sns = max(0.0, parse_valor_pt(sns_str, default=5600.0))
        despesas_casa = max(0.0, parse_valor_pt(casa_str, default=3400.0))
        margem_livre = liquido_sns - despesas_casa - 500.0 - 450.0

        c1, c2, c3 = st.columns(3)
        c1.metric("Pocket IRS 2027", "500,00 €/mês")
        c2.metric("DCA MSCI World", "450,00 €/mês")
        c3.metric("Margem Livre", f"{margem_livre:,.2f} €")
    else:
        entradas_ciclo_emp = 0.0
        if not df_raw.empty and "data_dt" in df_raw.columns:
            mask_ciclo_e = (
                (df_raw["entidade"] == "Empresa (ElementarPrivilege)")
                & (df_raw["categoria"].astype(str).str.startswith("Ganho - "))
                & (df_raw["data_dt"] >= inicio_ciclo_p)
                & (df_raw["data_dt"] <= fim_ciclo_p)
            )
            entradas_ciclo_emp = float(df_raw.loc[mask_ciclo_e, "valor"].sum())

        default_fat_str = f"{entradas_ciclo_emp:.2f}".replace(".", ",") if entradas_ciclo_emp > 0 else "11750"
        fat_str = st.text_input("Entradas do Ciclo (€)", value=default_fat_str, key="plan_fat")
        fixos_str = st.text_input("Encargos Fixos (€)", value="3200", key="plan_fixos")

        faturacao_emp = max(0.0, parse_valor_pt(fat_str, default=11750.0))
        fixos_emp = max(0.0, parse_valor_pt(fixos_str, default=3200.0))

        iva_extra = 2672.26 if (hoje.year == 2026 and hoje.month in [11, 12]) else 0.0
        provisao_hotel = 1000.0 if (hoje < date(2027, 4, 1)) else 0.0
        reserva_irc = round(max(0.0, faturacao_emp - fixos_emp) * 0.17, 2)
        excedente_emp = faturacao_emp - fixos_emp - reserva_irc - iva_extra - provisao_hotel

        c1, c2 = st.columns(2)
        c1.metric("Reserva IRC (17%)", f"{reserva_irc:,.2f} €")
        c2.metric("IVA Extraordinário", f"{iva_extra:,.2f} €")
        c3, c4 = st.columns(2)
        c3.metric("Crédito Sócio (268)", "1.300,00 €")
        c4.metric("Excedente Livre", f"{excedente_emp:,.2f} €")
