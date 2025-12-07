import os
import textwrap
from typing import List, Dict

import pandas as pd
import streamlit as st


# =========================================================
# CONFIG STREAMLIT
# =========================================================
st.set_page_config(
    page_title="Zula Board Game Bar",
    page_icon="🍸",
    layout="wide",
)


# =========================================================
# ESTILO GLOBAL – CLEAN GIRL (APENAS MODO CLARO)
# =========================================================
st.markdown(
    """
<style>
html, body, [class*="css"] {
    font-family: system-ui, -apple-system, BlinkMacSystemFont,
                 "SF Pro Text", "Segoe UI", sans-serif !important;
}

/* Fundo neutro bem claro */
body {
    background: #f5f4f2;
}

/* Container central mais estreito */
.block-container {
    max-width: 1000px !important;
    padding-top: 1.5rem !important;
}

/* Títulos */
h1, h2, h3 {
    color: #111827 !important;
    font-weight: 650 !important;
}

/* HEADER ZULA minimalista */
.zula-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    padding: 18px 22px;
    margin-bottom: 18px;
    border-radius: 18px;
    background: #fdfbf8;
    border: 1px solid #e5e7eb;
}

.zula-header-left {
    display: flex;
    align-items: center;
    gap: 14px;
}

.zula-avatar {
    width: 56px;
    height: 56px;
    border-radius: 999px;
   
    display: flex;
    align-items: center;
    justify-content: center;
    color: #7a3f35;
    font-size: 1.8rem;
}

.zula-title-main {
    font-size: 1.35rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #111827;
}

.zula-title-sub {
    font-size: 0.85rem;
    color: #6b7280;
}

/* Filtros no topo */
.top-filter-box {
    padding: 14px 16px 10px;
    margin-bottom: 20px;
    border-radius: 14px;
    background: #fdfbf8;
    border: 1px solid #e5e7eb;
}

/* Cartão base */
.card-base {
    background: #ffffff;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    padding: 16px 18px;
}

/* Cartão em grade */
.cool-card {
}

/* Cartão lista */
.list-card {
    margin-bottom: 6px;
}

/* Título do jogo */
.game-title {
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
}

/* Descrição */
.game-desc {
    font-size: 0.9rem;
    color: #374151;
    margin-top: 8px;
}

/* Chips de tags */
.tag-chip {
    display: inline-block;
    padding: 2px 9px;
    margin: 2px 4px 2px 0;
    font-size: 0.78rem;
    border-radius: 999px;
    background: #f3f4f6;
    color: #4b5563;
    border: 1px solid #e5e7eb;
}

/* Label dos filtros */
.stRadio > label, .stMultiSelect > label,
.stTextInput > label, .stSelectbox > label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #9ca3af;
}

/* Rádio em linha mais discreto */
.stRadio [role="radiogroup"] {
    gap: 0.75rem;
}

/* Contagem de jogos */
.count-text {
    font-size: 0.9rem;
    color: #4b5563;
    margin-bottom: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)


EXCEL_PATH = "collection.xlsx"


# =========================================================
# FUNÇÕES AUXILIARES DE DADOS
# =========================================================
def load_collection(excel_path: str) -> pd.DataFrame:
    # Lê a primeira planilha do Excel
    df = pd.read_excel(excel_path)
    if "own" in df.columns:
        df = df[df["own"] == 1]
    for col in [
        "objectname",
        "objectid",
        "rating",
        "average",
        "numplays",
        "minplayers",
        "maxplayers",
        "playingtime",
        "minplaytime",
        "maxplaytime",
        "itemtype",
        "yearpublished",
        "bggrecagerange",
        "bgglanguagedependence",
        "comentarios",
    ]:
        if col not in df.columns:
            df[col] = None
    return df


def format_players(row: pd.Series) -> str:
    try:
        mn = int(row["minplayers"])
        mx = int(row["maxplayers"])
        if mn == mx:
            return f"{mn}"
        return f"{mn}–{mx}"
    except Exception:
        return "—"


def pick_playtime_value(row: pd.Series) -> int:
    for col in ["playingtime", "minplaytime", "maxplaytime"]:
        try:
            v = int(row[col])
            if v > 0:
                return v
        except Exception:
            pass
    return 0


def format_playtime(row: pd.Series) -> str:
    try:
        mn = int(row["minplaytime"])
        mx = int(row["maxplaytime"])
        if mn > 0 and mx > 0 and mn != mx:
            return f"{mn}–{mx} min"
    except Exception:
        pass
    v = pick_playtime_value(row)
    return f"{v} min" if v > 0 else "—"


def map_item_type(t) -> str:
    if isinstance(t, str):
        t = t.lower().strip().capitalize()
        if t == "standalone":
            return "Jogo base"
        if t == "expansion":
            return "Expansão"
        return t
    return ""


def language_tag(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = t.lower()
    if "no necessary" in t:
        return "independente de idioma"
    if "some " in t:
        return "algum texto"
    if "moderate" in t:
        return "texto moderado"
    if "extensive" in t:
        return "muito texto"
    return ""


def generate_tags(row: pd.Series) -> List[str]:
    """Gera tags a partir de jogadores, tempo, idioma e tipo."""
    tags: List[str] = []

    # Jogadores
    try:
        mx = int(row["maxplayers"])
        if mx == 1:
            tags.append("solo")
        elif mx == 2:
            tags.append("2 jogadores")
        elif mx <= 4:
            tags.append("até 4 jogadores")
        elif mx <= 6:
            tags.append("até 6 jogadores")
        else:
            tags.append("grupos")
    except Exception:
        pass

    # Tempo
    t = pick_playtime_value(row)
    if t > 0:
        if t <= 30:
            tags.append("rápido")
        elif t <= 60:
            tags.append("médio")
        else:
            tags.append("longo")

    # Idioma
    lang = language_tag(row["bgglanguagedependence"])
    if lang:
        tags.append(lang)

    # Tipo como tag
    tipo = map_item_type(row["itemtype"])
    if isinstance(tipo, str) and tipo:
        tags.append(tipo)

    # Remove duplicatas preservando ordem
    return list(dict.fromkeys(tags))


def generate_desc(row: pd.Series) -> str:
    # Se tiver coluna "comment", usa ela como descrição (ajuste se seu Excel usar outro nome)
    if "comment" in row and isinstance(row["comment"], str) and row["comment"].strip():
        return row["comment"].strip()

    nome = row["objectname"]
    players = format_players(row)
    time = format_playtime(row)
    tipo = map_item_type(row["itemtype"]) or "jogo"

    text = f"{nome} é um {tipo.lower()}, para {players} jogadores, com duração média de {time}."
    return textwrap.shorten(text, width=240, placeholder="…")


@st.cache_data
def build_catalog(path: str) -> List[Dict]:
    df = load_collection(path)
    items: List[Dict] = []
    n = 680008
    for _, row in df.iterrows():
        n += 1
        try:
            oid = int(row["objectid"])
        except Exception:
            oid = n

        item_tipo = map_item_type(row["itemtype"])

        item = {
            "id": oid,
            "nome": row["objectname"],
            "tempo": format_playtime(row),
            "jogadores": format_players(row),
            "tipo": item_tipo,
            "tags": generate_tags(row),
            "descricao": generate_desc(row),
        }
        items.append(item)
    return items


# =========================================================
# CARREGAMENTO
# =========================================================
if not os.path.exists(EXCEL_PATH):
    st.error("Coloque o arquivo **collection.xlsx** na mesma pasta do app.")
    st.stop()

catalogo = build_catalog(EXCEL_PATH)


# =========================================================
# HEADER ZULA
# =========================================================
st.markdown(
    """
<div class="zula-header">
  <div class="zula-header-left">
    <div class="zula-avatar">🌸</div>
    <div>
      <div class="zula-title-main">Júlia 25 Anos</div>
      <div class="zula-title-sub">.</div>
    </div>
  </div>
  <div class="zula-header-right" style="font-size:0.85rem; color:#6b7280;">
    catálogo pessoal
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# FILTROS NO TOPO — APENAS POR TIPO
# =========================================================
st.markdown('<div class="top-filter-box">', unsafe_allow_html=True)

c1, c2 = st.columns([3, 2])

with c1:
    termo = st.text_input(
        "Buscar jogo",
        placeholder="ex: nome, rápido, 2 jogadores…",
    )

with c2:
    # pega todos os tipos existentes no catálogo
    tipos_unicos = sorted({i["tipo"] for i in catalogo if i["tipo"]})
    tipo_sel = st.selectbox(
        "Filtrar por tipo",
        ["Todos"] + tipos_unicos,
        index=0,
    )

c3, c4 = st.columns([2, 2])

with c3:
    view_mode = st.radio(
        "Modo de visualização",
        ["Cartões", "Lista"],
        index=0,
        horizontal=True,
    )

with c4:
    ordem = st.selectbox(
        "Ordenar por",
        [
            "Ordem alfabética (A–Z)",
            "Ordem inversa (Z–A)",
        ],
    )

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FILTRAGEM + ORDENAÇÃO (APENAS POR TIPO)
# =========================================================
def match(item: Dict) -> bool:
    # Filtro por tipo (exclusivo)
    if tipo_sel != "Todos" and item["tipo"] != tipo_sel:
        return False

    # Filtro por texto (nome, descrição, tags)
    if termo:
        low = termo.lower()
        nome_ok = low in item["nome"].lower()
        desc_ok = low in item["descricao"].lower()
        tags_ok = any(low in t.lower() for t in item["tags"])
        if not (nome_ok or desc_ok or tags_ok):
            return False

    return True


filtrados = [i for i in catalogo if match(i)]

# Ordenação
if ordem == "Ordem alfabética (A–Z)":
    filtrados = sorted(filtrados, key=lambda x: x["nome"].lower())
else:
    filtrados = sorted(filtrados, key=lambda x: x["nome"].lower(), reverse=True)


st.markdown(
    f'<div class="count-text">{len(filtrados)} jogos encontrados</div>',
    unsafe_allow_html=True,
)


# =========================================================
# EXIBIÇÃO – DOIS MODOS
# =========================================================
if not filtrados:
    st.warning("Nenhum jogo encontrado com essa combinação de filtros.")
else:
    if view_mode == "Cartões":
        # grade de cartões (2 colunas; no mobile empilha)
        cols = st.columns(2)
        for idx, jogo in enumerate(filtrados):
            with cols[idx % 2]:
                st.markdown(
                    f"""
<div class="card-base cool-card">
    <div class="game-title">{jogo['nome']}</div>
    <div style="font-size:0.86rem; color:#6b7280; margin-top:4px;">
        <strong>Tempo:</strong> {jogo['tempo']} · 
        <strong>Jogadores:</strong> {jogo['jogadores']} · 
        <strong>Tipo:</strong> {jogo['tipo']}
    </div>
    <div class="game-desc"><em>{jogo['descricao']}</em></div>
    <div style="margin-top: 6px;">
        {" ".join(f'<span class="tag-chip">{t}</span>' for t in jogo["tags"])}
    </div>
</div>
""",
                    unsafe_allow_html=True,
                )
    else:
        # LISTA: só o nome aparece; resto vai para o expander
        for jogo in filtrados:
            st.markdown(
                f"""
<div class="card-base list-card">
    <div class="game-title">{jogo['nome']}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            with st.expander("Ver descrição", expanded=False):
                st.markdown(
                    f"**Tempo:** {jogo['tempo']} · "
                    f"**Jogadores:** {jogo['jogadores']} · **Tipo:** {jogo['tipo']}"
                )
                st.write(jogo["descricao"])
                if jogo["tags"]:
                    st.markdown("Tags: " + " ".join(f"`{t}`" for t in jogo["tags"]))
