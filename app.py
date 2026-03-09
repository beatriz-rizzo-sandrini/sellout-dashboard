import streamlit as st
import pandas as pd
import numpy as np

ACESSOS_MARCA = {
    "fornecedor1@email.com": "Puma",
    "fornecedor2@email.com": "New Balance",
    "fornecedor3@email.com": "Adidas",
}

SENHA_INTERNA = st.secrets["SENHA_INTERNA"]

st.set_page_config(page_title="Sellout", layout="wide")
if "email_valido" in st.session_state:
    if st.button("Trocar acesso"):
        del st.session_state["email_valido"]
        st.rerun()
# CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(90deg, #070707 0%, #0f0f10 50%, #070707 100%);
        color: white;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 1.2rem;
        padding-bottom: 1rem;
    }

    .card {
        background: linear-gradient(145deg, #1a1a1d, #17171a);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        min-height: 120px;
    }

    .card-title {
        font-size: 14px;
        color: #f2f2f2;
        margin-bottom: 18px;
    }

    .card-value {
        font-size: 28px;
        font-weight: 700;
        color: white;
        margin-bottom: 8px;
    }

    .card-sub {
        font-size: 12px;
        color: #bbbbbb;
    }

    .section-card {
        background: linear-gradient(145deg, #1a1a1d, #17171a);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        min-height: 230px;
    }

    div[data-baseweb="select"] > div {
        background-color: #1b1b1f !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .stTextInput > div > div > input {
        background-color: #1b1b1f !important;
        color: white !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
    }

    h1, h2, h3, h4, h5, h6, p, label, div, span {
        color: white !important;
    }
    .row-gap {
    margin-top: 22px;
    }

    .small-gap {
        margin-top: 14px;
    }
</style>
""", unsafe_allow_html=True)

# HELPERS
def to_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
        .replace(["nan", "None", ""], np.nan),
        errors="coerce"
    ).fillna(0)

def normalize_text(x):
    if pd.isna(x):
        return ""
    return str(x).strip()

def derive_brand(platform_value):
    p = normalize_text(platform_value).upper()
    if "SANDRINI" in p:
        return "SANDRINI"
    if "BUYCLOCK" in p:
        return "BUYCLOCK"
    return "OUTROS"

@st.cache_data
def load_sellout_csv(uploaded_file):
    raw = pd.read_csv(uploaded_file, header=None, sep=",", encoding="utf-8", low_memory=False)

    headers = raw.iloc[:3].fillna("")
    data = raw.iloc[3:].reset_index(drop=True).copy()

    flat_cols = []
    for c in raw.columns:
        parts = [str(headers.iloc[r, c]).strip() for r in range(3)]
        parts = [p for p in parts if p and p.lower() != "nan"]
        flat_cols.append(" | ".join(parts))

    seen = {}
    unique_cols = []
    for col in flat_cols:
        name = col if col else "coluna_vazia"
        if name in seen:
            seen[name] += 1
            name = f"{name}__{seen[name]}"
        else:
            seen[name] = 0
        unique_cols.append(name)

    data.columns = unique_cols

    sku_plataforma_col = "SKU DA PLATAFORMA | SKU DA BLING | SKU COMUM"
    sku_senior_col = "SKU SÊNIOR | SKU SÊNIOR"
    plataforma_col = "PLATAFORMA"
    estoque_apto_final_col = "FECHAMENTO DE ESTOQUE E VENDA | FINAL | ESTOQUE APTO"
    estoque_geral_final_col = "ESTOQUE GERAL"
    vendas_geral_col = "VENDAS GERAL"

    matching_estoque_geral = [c for c in data.columns if c == "ESTOQUE GERAL" or c.startswith("ESTOQUE GERAL__")]
    if not matching_estoque_geral:
        raise ValueError("Não encontrei a coluna de ESTOQUE GERAL final.")
    estoque_geral_final_col = matching_estoque_geral[-1]

    df = pd.DataFrame({
        "SKU_PLATAFORMA": data[sku_plataforma_col].map(normalize_text),
        "SKU_SENIOR": data[sku_senior_col].map(normalize_text),
        "PLATAFORMA": data[plataforma_col].map(normalize_text),
        "ESTOQUE_APTO": to_number(data[estoque_apto_final_col]),
        "ESTOQUE_GERAL": to_number(data[estoque_geral_final_col]),
        "VENDAS_GERAL": to_number(data[vendas_geral_col]),
    })

    df = df[
        (df["SKU_PLATAFORMA"] != "") |
        (df["SKU_SENIOR"] != "") |
        (df["PLATAFORMA"] != "")
    ].copy()

    df["MARCA"] = df["PLATAFORMA"].apply(derive_brand)

    df["SKU_SENIOR"] = df["SKU_SENIOR"].replace("", "-")
    df["SKU_PLATAFORMA"] = df["SKU_PLATAFORMA"].replace("", "-")
    df["PLATAFORMA"] = df["PLATAFORMA"].replace("", "-")

    return df

def metric_card(title, value, subtitle=""):
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# HEADER
c1, c2 = st.columns([6,2])

with c1:
    st.title("Sellout")

with c2:
    st.image("Logo.png", width=200)

# LOGIN
# =========================
# =========================
# ACESSO POR EMAIL
# =========================

# =========================
# ACESSO POR EMAIL
# =========================

if "email_valido" not in st.session_state:
    email = st.text_input("Digite seu email para acessar")

    if not email:
        st.stop()

    email = email.strip().lower()

    # se for sandrini, exige senha
    if "@gruposandrini.com.br" in email or "@gruposandrini.com" in email:
        senha = st.text_input("Digite a senha interna", type="password")

        if not senha:
            st.stop()

        if senha != SENHA_INTERNA:
            st.error("Senha incorreta.")
            st.stop()

    st.session_state.email_valido = email

else:
    email = st.session_state.email_valido

try:
    df = load_sellout_csv("dados.csv")
    
except Exception as e:
    st.error(f"Erro ao ler a planilha: {e}")
    st.stop()

df = df[~df["PLATAFORMA"].str.contains("BUYCLOCK", case=False, na=False)]

# CARREGAR TABELA DE PRODUTOS

produtos = pd.read_csv("produtos.csv")

produtos.columns = produtos.columns.str.strip()

df["SKU_SENIOR"] = df["SKU_SENIOR"].astype(str).str.strip()
produtos["sku_senior"] = produtos["sku_senior"].astype(str).str.strip()

# MERGE (JOIN)
df = df.merge(
    produtos[["sku_senior", "descricao", "marca"]],
    left_on="SKU_SENIOR",
    right_on="sku_senior",
    how="left"
)

df = df.drop(columns=["sku_senior"])

df["marca"] = df["marca"].fillna("SEM MARCA").astype(str).str.strip().str.title()
df["descricao"] = df["descricao"].fillna("").astype(str).str.strip()
df["PLATAFORMA"] = df["PLATAFORMA"].fillna("").astype(str).str.strip().str.title()

if email.endswith("@gruposandrini.com.br") or email.endswith("@gruposandrini.com"):
    pass 

else:
    marca_permitida = ACESSOS_MARCA.get(email)

    if not marca_permitida:
        st.error("Seu email não tem permissão para acessar este dashboard.")
        st.stop()

    df = df[df["marca"].str.lower() == marca_permitida.lower()]
# FILTROS
f1, f2, f3 = st.columns(3)

marcas = sorted(df["marca"].dropna().unique())

with f1:
    marca_sel = st.multiselect("Marca", marcas)

df_temp = df.copy()

if marca_sel:
    df_temp = df_temp[df_temp["marca"].isin(marca_sel)]


plataformas = sorted(df_temp["PLATAFORMA"].dropna().unique())

with f2:
    plataforma_sel = st.multiselect("Plataforma", plataformas)

if plataforma_sel:
    df_temp = df_temp[df_temp["PLATAFORMA"].isin(plataforma_sel)]

skus = sorted(df_temp["descricao"].dropna().unique())

with f3:
    sku_sel = st.multiselect("Descrição", skus)

df_filtrado = df.copy()

if marca_sel:
    df_filtrado = df_filtrado[df_filtrado["marca"].isin(marca_sel)]

if plataforma_sel:
    df_filtrado = df_filtrado[df_filtrado["PLATAFORMA"].isin(plataforma_sel)]

if sku_sel:
    df_filtrado = df_filtrado[df_filtrado["SKU_SENIOR"].isin(sku_sel)]

v30 = df_filtrado["VENDAS_GERAL"].sum()

media_dia = v30 / 30 if v30 > 0 else 0

v15 = media_dia * 15
v7 = media_dia * 7

k1, k2, k3 = st.columns(3)

with k1:
    metric_card(
        "Sellout 30 dias",
        f"{int(v30):,}".replace(",", "."),
        "Total da planilha"
    )

with k2:
    metric_card(
        "Sellout 15 dias (estimado)",
        f"{int(v15):,}".replace(",", "."),
        "Proporção da venda de 30 dias"
    )

with k3:
    metric_card(
        "Sellout 7 dias (estimado)",
        f"{int(v7):,}".replace(",", "."),
        "Proporção da venda de 30 dias"
    )

st.markdown("<br>", unsafe_allow_html=True)

# KPIS
k1, k2, k3, k4 = st.columns(4)

with k1:
    metric_card(
        "Vendas Geral",
        f"{df_filtrado['VENDAS_GERAL'].sum():,.0f}".replace(",", "."),
        "Total de vendas da planilha"
    )

with k2:
    metric_card(
        "Estoque Apto",
        f"{df_filtrado['ESTOQUE_APTO'].sum():,.0f}".replace(",", "."),
        "Fechamento final"
    )

with k3:
    metric_card(
        "Estoque Geral",
        f"{df_filtrado['ESTOQUE_GERAL'].sum():,.0f}".replace(",", "."),
        "Fechamento final"
    )

with k4:
    metric_card(
        "SKUs",
        f"{df_filtrado['SKU_SENIOR'].nunique():,.0f}".replace(",", "."),
        "Quantidade de SKU sênior"
    )

st.markdown('<div class="row-gap"></div>', unsafe_allow_html=True)

# GRÁFICOS
g1, g2 = st.columns([2, 2])

with g1:
    st.subheader("Vendas por Plataforma")

    graf_plataforma = (
        df_filtrado.groupby("PLATAFORMA", as_index=False)["VENDAS_GERAL"]
        .sum()
        .sort_values("VENDAS_GERAL", ascending=False)
    )

    if graf_plataforma.empty:
        st.info("Sem dados para exibir.")
    else:
        st.bar_chart(
            graf_plataforma.set_index("PLATAFORMA")["VENDAS_GERAL"],
            use_container_width=True
        )

with g2:
    st.subheader("Top Marcas")

    graf_marca = (
        df_filtrado.groupby("marca", as_index=False)["VENDAS_GERAL"]
        .sum()
        .sort_values("VENDAS_GERAL", ascending=False)
        .head(10)
    )

    if graf_marca.empty:
        st.info("Sem dados para exibir.")
    else:
        st.bar_chart(
            graf_marca.set_index("marca")["VENDAS_GERAL"],
            use_container_width=True
        )
        
st.subheader("Análise Geral")

tabela = df_filtrado[[
    "marca",
    "PLATAFORMA",
    "SKU_SENIOR",
    "descricao",
    "SKU_PLATAFORMA",
    "VENDAS_GERAL",
    "ESTOQUE_APTO",
    "ESTOQUE_GERAL"
]].copy()

tabela = tabela.sort_values(by="VENDAS_GERAL", ascending=False)

tabela = tabela.rename(columns={
    "marca": "Marca",
    "PLATAFORMA": "Plataforma",
    "SKU_SENIOR": "SKU Sênior",
    "descricao": "Descrição",
    "SKU_PLATAFORMA": "SKU Plataforma",
    "VENDAS_GERAL": "Vendas 30 Dias",
    "ESTOQUE_APTO": "Estoque Apto",
    "ESTOQUE_GERAL": "Estoque Geral"
})

st.dataframe(
    tabela,
    use_container_width=True,
    height=650
)

csv = tabela.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "Baixar tabela filtrada",
    data=csv,
    file_name="sellout_filtrado.csv",
    mime="text/csv"
)

st.markdown('</div>', unsafe_allow_html=True)

