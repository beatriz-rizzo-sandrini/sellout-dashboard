import streamlit as st
import pandas as pd
import numpy as np
import re

ACESSOS_MARCA = {
    "fornecedor1@email.com": "Puma",
    "fornecedor2@email.com": "New Balance",
    "fornecedor3@email.com": "Adidas",
}

try:
    SENHA_INTERNA = st.secrets["SENHA_INTERNA"]
except:
    SENHA_INTERNA = "RenanLobo123*"

st.set_page_config(page_title="Sellout", layout="wide")
if "email_valido" in st.session_state:
    if st.button("Trocar acesso"):
        del st.session_state["email_valido"]
        st.rerun()

st.markdown("""
<style>
    /* layout */
    .block-container {
        max-width: 1250px;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    /* cards - dark mode */
    .card {
        background: linear-gradient(145deg, #1a1a1d, #17171a);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        min-height: 120px;
    }
    .card-title { font-size: 14px; color: #f2f2f2; margin-bottom: 18px; }
    .card-value { font-size: 28px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }
    .card-sub   { font-size: 12px; color: #bbbbbb; }

    /* cards - light mode */
    [data-theme="light"] .card,
    .st-emotion-cache-1wmy9hl .card {
        background: linear-gradient(145deg, #ffffff, #f4f5f7);
        border: 1px solid rgba(0,0,0,0.08);
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }
    [data-theme="light"] .card-title { color: #555555; }
    [data-theme="light"] .card-value { color: #111111; }
    [data-theme="light"] .card-sub   { color: #888888; }

    /* select border-radius */
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
    }

    /* tags multiselect */
    [data-baseweb="tag"] {
        border-radius: 8px !important;
    }

    /* input texto */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
    }

    /* dataframe */
    .stDataFrame { border-radius: 14px; overflow: hidden; }

    /* botao */
    .stDownloadButton button, .stButton button {
        border-radius: 10px !important;
    }

    .row-gap  { margin-top: 22px; }
    .small-gap{ margin-top: 14px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────────

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

# ── EXTRAÇÃO DE MODELO / GÊNERO / TAMANHO ─────────────────────────────────────

STOPWORDS_GENERO = {"MASCULINO", "FEMININO", "UNISEX", "INFANTIL", "JUVENIL"}
STOPWORDS_FIM    = {"TAM", "TAM.", "TAM:", "TAMANHO"}
TIPOS = [
    "TENIS", "TÊNIS", "CHUTEIRA", "CHINELO", "SANDALIA", "BOTA",
    "SAPATILHA", "MOCHILA", "BOLSA", "CAMISA", "CAMISETA",
    "RELOGIO", "RELÓGIO", "BRINDE", "SUNGA", "MAILLOT",
    "SHORTS", "BERMUDA", "REGATA", "JAQUETA", "CASACO",
    "MEIAS", "MEIA", "BLUSÃO", "BLUSAO",
]
MARCAS_NOMES = {
    "Fila":        ["FILA"],
    "Adidas":      ["ADIDAS"],
    "Nike":        ["NIKE"],
    "Asics":       ["ASICS"],
    "New Balance": ["NEW BALANCE", "NB"],
    "Actvitta":    ["ACTVITTA"],
    "Penalty":     ["PENALTY"],
    "Puma":        ["PUMA"],
    "Mizuno":      ["MIZUNO"],
    "Speedo":      ["SPEEDO"],
    "Umbro":       ["UMBRO"],
}

def extrair_campos(descricao: str, marca: str):
    """Retorna (modelo, genero, tamanho) a partir da descrição."""
    desc = str(descricao).upper().strip()

    # ── tamanho ──────────────────────────────────────────────────────────────
    # Numérico:  Tam:42 | TAM. 42 | TAM 42 | TAM:42/43
    # Vestuário: TAM G | TAM:GG | TAM XG | TAM PP | TAM M | TAM P etc.
    #            ou token solto no fim: "...POLO GG" / "...CAMISA XG"
    _TAM_NUM = r"\d{1,3}(?:[/\-]\d{1,3})?"
    _TAM_VES = r"X{0,2}G{1,2}|PP?|MM?"   # XXG XG GG G PP P M MM
    tam_match = re.search(
        rf"TAM[:.\s]+({_TAM_NUM}|{_TAM_VES})\b",
        desc
    )
    if not tam_match:
        # tenta pegar sufixo de vestuário solto no final da string
        tam_match = re.search(
            rf"\b({_TAM_VES})\s*$",
            desc
        )
    tamanho = tam_match.group(1) if tam_match else "SEM TAM"

    # ── gênero ───────────────────────────────────────────────────────────────
    genero = "SEM GÊNERO"
    for g in ["MASCULINO", "FEMININO", "UNISEX", "INFANTIL", "JUVENIL"]:
        if g in desc:
            genero = g.title()
            break

    # ── modelo ───────────────────────────────────────────────────────────────
    tokens = desc.split()

    # remover tipo
    if tokens and tokens[0] in TIPOS:
        tokens = tokens[1:]

    # remover marca
    marca_norm = str(marca).strip()
    nomes = MARCAS_NOMES.get(marca_norm, [marca_norm.upper()])
    for nome in nomes:
        nome_tks = nome.split()
        if tokens[:len(nome_tks)] == nome_tks:
            tokens = tokens[len(nome_tks):]
            break

    # remover gênero se vier antes do modelo
    if tokens and tokens[0] in STOPWORDS_GENERO:
        tokens = tokens[1:]

    modelo_tks = []
    for t in tokens:
        if t in STOPWORDS_GENERO or t in STOPWORDS_FIM:
            break
        if re.match(r"^[A-Z]{1,3}\d{2,}", t):   # código tipo F01TR00108
            break
        if re.match(r"^\d{4,}", t):              # número longo
            break
        if t == "-":
            break
        modelo_tks.append(t)

    modelo = " ".join(modelo_tks) if modelo_tks else "SEM MODELO"
    return modelo, genero, tamanho


# ── CARREGAMENTO ───────────────────────────────────────────────────────────────

@st.cache_data
def load_sellout_csv(uploaded_file):
    raw = pd.read_csv(uploaded_file, header=None, sep=",", encoding="utf-8", low_memory=False)

    headers = raw.iloc[:3].fillna("")
    data    = raw.iloc[3:].reset_index(drop=True).copy()

    flat_cols = []
    for c in raw.columns:
        parts = [str(headers.iloc[r, c]).strip() for r in range(3)]
        parts = [p for p in parts if p and p.lower() != "nan"]
        flat_cols.append(" | ".join(parts))

    seen, unique_cols = {}, []
    for col in flat_cols:
        name = col if col else "coluna_vazia"
        if name in seen:
            seen[name] += 1
            name = f"{name}__{seen[name]}"
        else:
            seen[name] = 0
        unique_cols.append(name)

    data.columns = unique_cols

    sku_plataforma_col    = "SKU DA PLATAFORMA | SKU DA BLING | SKU COMUM"
    sku_senior_col        = "SKU SÊNIOR | SKU SÊNIOR"
    plataforma_col        = "PLATAFORMA"
    estoque_apto_final_col = "FECHAMENTO DE ESTOQUE E VENDA | FINAL | ESTOQUE APTO"
    vendas_geral_col      = "VENDAS GERAL"

    matching_eg = [c for c in data.columns if c == "ESTOQUE GERAL" or c.startswith("ESTOQUE GERAL__")]
    if not matching_eg:
        raise ValueError("Não encontrei a coluna de ESTOQUE GERAL final.")
    estoque_geral_final_col = matching_eg[-1]

    df = pd.DataFrame({
        "SKU_PLATAFORMA": data[sku_plataforma_col].map(normalize_text),
        "SKU_SENIOR":     data[sku_senior_col].map(normalize_text),
        "PLATAFORMA":     data[plataforma_col].map(normalize_text),
        "ESTOQUE_APTO":   to_number(data[estoque_apto_final_col]),
        "ESTOQUE_GERAL":  to_number(data[estoque_geral_final_col]),
        "VENDAS_GERAL":   to_number(data[vendas_geral_col]),
    })

    df = df[
        (df["SKU_PLATAFORMA"] != "") |
        (df["SKU_SENIOR"]     != "") |
        (df["PLATAFORMA"]     != "")
    ].copy()

    df["MARCA"]         = df["PLATAFORMA"].apply(derive_brand)
    df["SKU_SENIOR"]    = df["SKU_SENIOR"].replace("", "-")
    df["SKU_PLATAFORMA"]= df["SKU_PLATAFORMA"].replace("", "-")
    df["PLATAFORMA"]    = df["PLATAFORMA"].replace("", "-")

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


# ── HEADER ────────────────────────────────────────────────────────────────────

c1, c2 = st.columns([6, 2], vertical_alignment="center")
with c1:
    st.markdown("""
    <h1 style="margin:0;padding:0;font-size:clamp(22px,4vw,38px);">Sellout</h1>
    """, unsafe_allow_html=True)
with c2:
    st.image("Logo.png", width=160)


# ── LOGIN ─────────────────────────────────────────────────────────────────────

if "email_valido" not in st.session_state:
    email = st.text_input("Digite seu email para acessar")
    if not email:
        st.stop()
    email = email.strip().lower()
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


# ── DADOS ─────────────────────────────────────────────────────────────────────

try:
    df = load_sellout_csv("dados.csv")
except Exception as e:
    st.error(f"Erro ao ler a planilha: {e}")
    st.stop()

df = df[~df["PLATAFORMA"].str.contains("BUYCLOCK", case=False, na=False)]

produtos = pd.read_csv("produtos.csv")
produtos.columns = produtos.columns.str.strip()
df["SKU_SENIOR"]      = df["SKU_SENIOR"].astype(str).str.strip()
produtos["sku_senior"] = produtos["sku_senior"].astype(str).str.strip()

df = df.merge(
    produtos[["sku_senior", "descricao", "marca"]],
    left_on="SKU_SENIOR", right_on="sku_senior", how="left"
).drop(columns=["sku_senior"])

df["marca"]     = df["marca"].fillna("SEM MARCA").astype(str).str.strip().str.title()
df["descricao"] = df["descricao"].fillna("").astype(str).str.strip()
df["PLATAFORMA"]= df["PLATAFORMA"].fillna("").astype(str).str.strip().str.title()

# ── EXTRAIR MODELO / GÊNERO / TAMANHO ─────────────────────────────────────────

campos = df.apply(lambda r: extrair_campos(r["descricao"], r["marca"]), axis=1)
df["MODELO"]  = [c[0] for c in campos]
df["GENERO"]  = [c[1] for c in campos]
df["TAMANHO"] = [c[2] for c in campos]


# ── CONTROLE DE ACESSO ────────────────────────────────────────────────────────

usuario_interno = (
    email.endswith("@gruposandrini.com.br") or
    email.endswith("@gruposandrini.com")
)

if not usuario_interno:
    marca_permitida = ACESSOS_MARCA.get(email)
    if not marca_permitida:
        st.error("Seu email não tem permissão para acessar este dashboard.")
        st.stop()
    df = df[df["marca"].str.lower() == marca_permitida.lower()]


# ── FILTROS ───────────────────────────────────────────────────────────────────

if usuario_interno:
    f1, f2, f3, f4, f5 = st.columns(5)
else:
    f1, f3, f4, f5 = st.columns(4)

marcas = sorted(df["marca"].dropna().unique())
with f1:
    marca_sel = st.multiselect("Marca", marcas)

df_temp = df.copy()
if marca_sel:
    df_temp = df_temp[df_temp["marca"].isin(marca_sel)]

if usuario_interno:
    plataformas = sorted(df_temp["PLATAFORMA"].dropna().unique())
    with f2:
        plataforma_sel = st.multiselect("Plataforma", plataformas)
    if plataforma_sel:
        df_temp = df_temp[df_temp["PLATAFORMA"].isin(plataforma_sel)]
else:
    plataforma_sel = []

modelos = sorted(df_temp["MODELO"].dropna().unique())
with f3:
    modelo_sel = st.multiselect("Modelo", modelos)
if modelo_sel:
    df_temp = df_temp[df_temp["MODELO"].isin(modelo_sel)]

generos = sorted(df_temp["GENERO"].dropna().unique())
with f4:
    genero_sel = st.multiselect("Gênero", generos)
if genero_sel:
    df_temp = df_temp[df_temp["GENERO"].isin(genero_sel)]

tamanhos = sorted(
    df_temp["TAMANHO"].dropna().unique(),
    key=lambda x: (float(x.split("/")[0]) if x.replace("/", "").replace(".", "").isdigit() else 9999)
)
with f5:
    tamanho_sel = st.multiselect("Tamanho", tamanhos)


# ── FILTRAGEM FINAL ───────────────────────────────────────────────────────────

df_filtrado = df.copy()
if marca_sel:       df_filtrado = df_filtrado[df_filtrado["marca"].isin(marca_sel)]
if plataforma_sel:  df_filtrado = df_filtrado[df_filtrado["PLATAFORMA"].isin(plataforma_sel)]
if modelo_sel:      df_filtrado = df_filtrado[df_filtrado["MODELO"].isin(modelo_sel)]
if genero_sel:      df_filtrado = df_filtrado[df_filtrado["GENERO"].isin(genero_sel)]
if tamanho_sel:     df_filtrado = df_filtrado[df_filtrado["TAMANHO"].isin(tamanho_sel)]


# ── KPIs TOPO ─────────────────────────────────────────────────────────────────

v30      = df_filtrado["VENDAS_GERAL"].sum()
media_dia = v30 / 30 if v30 > 0 else 0

k1, k2, k3 = st.columns(3)
with k1: metric_card("Sellout 30 dias",          f"{int(v30):,}".replace(",","."),           "Total da planilha")
with k2: metric_card("Sellout 15 dias (estimado)",f"{int(media_dia*15):,}".replace(",","."), "Proporção da venda de 30 dias")
with k3: metric_card("Sellout 7 dias (estimado)", f"{int(media_dia*7):,}".replace(",","."),  "Proporção da venda de 30 dias")

st.markdown("<br>", unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
with k1: metric_card("Vendas Geral",  f"{df_filtrado['VENDAS_GERAL'].sum():,.0f}".replace(",","."), "Total de vendas da planilha")
with k2: metric_card("Estoque Apto",  f"{df_filtrado['ESTOQUE_APTO'].sum():,.0f}".replace(",","."), "Fechamento final")
with k3: metric_card("Estoque Geral", f"{df_filtrado['ESTOQUE_GERAL'].sum():,.0f}".replace(",","."), "Fechamento final")
with k4: metric_card("SKUs",          f"{df_filtrado['SKU_SENIOR'].nunique():,.0f}".replace(",","."), "Quantidade de SKU sênior")

st.markdown('<div class="row-gap"></div>', unsafe_allow_html=True)


# ── GRÁFICOS ──────────────────────────────────────────────────────────────────

if usuario_interno:
    # Linha 1: Plataforma + Modelo
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Vendas por Plataforma")
        graf = (
            df_filtrado.groupby("PLATAFORMA", as_index=False)["VENDAS_GERAL"]
            .sum().sort_values("VENDAS_GERAL", ascending=False)
            .rename(columns={"VENDAS_GERAL": "Vendas", "PLATAFORMA": "Plataforma"})
        )
        if graf.empty:
            st.info("Sem dados para exibir.")
        else:
            st.bar_chart(graf.set_index("Plataforma")["Vendas"], use_container_width=True)

    with g2:
        if marca_sel or df_filtrado["marca"].nunique() == 1:
            st.subheader("Top 10 Modelos Mais Vendidos")
            graf = (
                df_filtrado.groupby("MODELO", as_index=False)["VENDAS_GERAL"]
                .sum().sort_values("VENDAS_GERAL", ascending=False).head(10)
                .rename(columns={"MODELO": "Modelo", "VENDAS_GERAL": "Vendas"})
            )
            if graf.empty:
                st.info("Sem dados para exibir.")
            else:
                st.bar_chart(graf.set_index("Modelo")["Vendas"], use_container_width=True)
        else:
            st.subheader("Top Marcas")
            graf = (
                df_filtrado.groupby("marca", as_index=False)["VENDAS_GERAL"]
                .sum().sort_values("VENDAS_GERAL", ascending=False).head(10)
                .rename(columns={"marca": "Marca", "VENDAS_GERAL": "Vendas"})
            )
            if graf.empty:
                st.info("Sem dados para exibir.")
            else:
                st.bar_chart(graf.set_index("Marca")["Vendas"], use_container_width=True)

    st.markdown('<div class="row-gap"></div>', unsafe_allow_html=True)

    # Linha 2: Gênero + Tamanho
    g3, g4 = st.columns(2)

    with g3:
        st.subheader("Vendas por Gênero")
        graf = (
            df_filtrado[df_filtrado["GENERO"] != "Sem Gênero"]
            .groupby("GENERO", as_index=False)["VENDAS_GERAL"]
            .sum().sort_values("VENDAS_GERAL", ascending=False)
            .rename(columns={"GENERO": "Gênero", "VENDAS_GERAL": "Vendas"})
        )
        if graf.empty:
            st.info("Sem dados para exibir.")
        else:
            st.bar_chart(graf.set_index("Gênero")["Vendas"], use_container_width=True)

    with g4:
        st.subheader("Vendas por Tamanho")
        graf = (
            df_filtrado[df_filtrado["TAMANHO"] != "SEM TAM"]
            .groupby("TAMANHO", as_index=False)["VENDAS_GERAL"]
            .sum()
        )
        # ordenar numericamente
        graf["_ord"] = pd.to_numeric(
            graf["TAMANHO"].str.split("/").str[0], errors="coerce"
        )
        graf = graf.sort_values("_ord").drop(columns=["_ord"])
        graf = graf.rename(columns={"TAMANHO": "Tamanho", "VENDAS_GERAL": "Vendas"})
        if graf.empty:
            st.info("Sem dados para exibir.")
        else:
            st.bar_chart(graf.set_index("Tamanho")["Vendas"], use_container_width=True)

else:
    # Usuário externo: só modelo e tamanho
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Top 10 Modelos")
        graf = (
            df_filtrado.groupby("MODELO", as_index=False)["VENDAS_GERAL"]
            .sum().sort_values("VENDAS_GERAL", ascending=False).head(10)
            .rename(columns={"MODELO": "Modelo", "VENDAS_GERAL": "Vendas"})
        )
        if graf.empty:
            st.info("Sem dados.")
        else:
            st.bar_chart(graf.set_index("Modelo")["Vendas"], use_container_width=True)

    with g2:
        st.subheader("Vendas por Tamanho")
        graf = (
            df_filtrado[df_filtrado["TAMANHO"] != "SEM TAM"]
            .groupby("TAMANHO", as_index=False)["VENDAS_GERAL"].sum()
        )
        graf["_ord"] = pd.to_numeric(graf["TAMANHO"].str.split("/").str[0], errors="coerce")
        graf = graf.sort_values("_ord").drop(columns=["_ord"])
        graf = graf.rename(columns={"TAMANHO": "Tamanho", "VENDAS_GERAL": "Vendas"})
        if graf.empty:
            st.info("Sem dados.")
        else:
            st.bar_chart(graf.set_index("Tamanho")["Vendas"], use_container_width=True)


# ── TABELA ────────────────────────────────────────────────────────────────────

st.markdown('<div class="row-gap"></div>', unsafe_allow_html=True)
st.subheader("Análise Geral")

if usuario_interno:
    tabela = df_filtrado[[
        "marca", "PLATAFORMA", "SKU_SENIOR", "descricao",
        "MODELO", "GENERO", "TAMANHO",
        "SKU_PLATAFORMA", "VENDAS_GERAL", "ESTOQUE_APTO", "ESTOQUE_GERAL"
    ]].copy()
else:
    tabela = df_filtrado[[
        "marca", "SKU_SENIOR", "descricao",
        "MODELO", "GENERO", "TAMANHO",
        "VENDAS_GERAL", "ESTOQUE_APTO", "ESTOQUE_GERAL"
    ]].copy()

tabela = tabela.sort_values("VENDAS_GERAL", ascending=False).rename(columns={
    "marca":          "Marca",
    "PLATAFORMA":     "Plataforma",
    "SKU_SENIOR":     "SKU Sênior",
    "descricao":      "Descrição",
    "MODELO":         "Modelo",
    "GENERO":         "Gênero",
    "TAMANHO":        "Tamanho",
    "SKU_PLATAFORMA": "SKU Plataforma",
    "VENDAS_GERAL":   "Vendas 30 Dias",
    "ESTOQUE_APTO":   "Estoque Apto",
    "ESTOQUE_GERAL":  "Estoque Geral",
})

st.dataframe(tabela, use_container_width=True, hide_index=True)

csv = tabela.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Baixar tabela filtrada",
    data=csv,
    file_name="sellout_filtrado.csv",
    mime="text/csv"
)