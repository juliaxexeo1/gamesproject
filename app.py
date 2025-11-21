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
# ESTILO GLOBAL – CLEAN GIRL
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
    background: radial-gradient(circle at 30% 20%, #ffffff 0%, #f9d5c5 55%, #e6a28f 100%);
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
.stRadio > label, .stMultiSelect > label, .stTextInput > label, .stSelectbox > label {
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


CSV_PATH = "collection.csv"


# =========================================================
# FUNÇÕES AUXILIARES DE DADOS
# =========================================================
def load_collection(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
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
        t = t.lower().strip()
        if t == "standalone":
            return "Jogo base"
        if t == "expansion":
            return "Expansão"
    return "Desconhecido"


def compute_rating_display(row: pd.Series) -> str:
    try:
        r = float(row["rating"])
        if r > 0:
            return f"{r:.1f}"
    except Exception:
        pass
    try:
        a = float(row["average"])
        if a > 0:
            return f"{a:.2f}"
    except Exception:
        pass
    return "—"


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


def rating_emoji(rating_str: str) -> str:
    """Emojis dinâmicos para rating."""
    try:
        r = float(rating_str)
    except Exception:
        return ""
    if r >= 9.0:
        return "🌟"
    if r >= 8.0:
        return "⭐"
    if r >= 7.0:
        return "✨"
    if r > 0:
        return "💗"
    return ""


def generate_tags(row: pd.Series, rating_str: str) -> List[str]:
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

    # Rating
    try:
        rv = float(rating_str)
        if rv >= 8.0:
            tags.append("favorito")
        elif rv >= 7.0:
            tags.append("bem avaliado")
    except Exception:
        pass

    return list(dict.fromkeys(tags))


def generate_desc(row: pd.Series, rating_str: str) -> str:
    nome = row["objectname"]
    players = format_players(row)
    time = format_playtime(row)
    tipo = map_item_type(row["itemtype"])

    text = f"{nome} é um {tipo.lower()}, para {players} jogadores, com duração média de {time}."
    if rating_str != "—":
        text += f" Avaliação atual: {rating_str}."
    return textwrap.shorten(text, width=240, placeholder="…")


@st.cache_data
def build_catalog(path: str) -> List[Dict]:
    df = load_collection(path)
    items: List[Dict] = []
    for _, row in df.iterrows():
        try:
            oid = int(row["objectid"])
        except Exception:
            continue

        rating_str = compute_rating_display(row)
        emoji = rating_emoji(rating_str)

        item = {
            "id": oid,
            "nome": row["objectname"],
            "rating": rating_str,
            "emoji": emoji,
            "tempo": format_playtime(row),
            "jogadores": format_players(row),
            "tipo": map_item_type(row["itemtype"]),
            "tags": generate_tags(row, rating_str),
            "descricao": generate_desc(row, rating_str),
        }
        items.append(item)
    return items


# =========================================================
# CARREGAMENTO
# =========================================================
if not os.path.exists(CSV_PATH):
    st.error("Coloque o arquivo collection.csv na mesma pasta do app.")
    st.stop()

catalogo = build_catalog(CSV_PATH)


# =========================================================
# HEADER ZULA
# =========================================================
st.markdown(
    """
<div class="zula-header">
  <div class="zula-header-left">
    <div class="zula-avatar">☺︎</div>
    <div>
      <div class="zula-title-main">Zula Board Game Bar</div>
      <div class="zula-title-sub">Jogos de tabuleiro, drinks e boas conversas.</div>
    </div>
  </div>
  <div class="zula-header-right" style="font-size:0.85rem; color:#6b7280;">
    catálogo pessoal · bgg collection
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# FILTROS NO TOPO
# =========================================================
st.markdown('<div class="top-filter-box">', unsafe_allow_html=True)

c1, c2 = st.columns([3, 2])

with c1:
    termo = st.text_input(
        "Buscar jogo",
        placeholder="ex: rápido, favorito, 2 jogadores…",
    )

with c2:
    todas_tags = sorted({t for i in catalogo for t in i["tags"]})
    tags_sel = st.multiselect("Filtrar por tags", todas_tags)

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
            "Rating (maior → menor)",
            "Rating (menor → maior)",
        ],
    )

st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FILTRAGEM + ORDENAÇÃO
# =========================================================
def match(item: Dict) -> bool:
    if tags_sel:
        if not all(t in item["tags"] for t in tags_sel):
            return False
    if termo:
        low = termo.lower()
        if low not in item["nome"].lower() and low not in item["descricao"].lower():
            if not any(low in tg.lower() for tg in item["tags"]):
                return False
    return True


filtrados = [i for i in catalogo if match(i)]


def parse_rating(r):
    try:
        return float(r)
    except Exception:
        return -1.0


if ordem == "Ordem alfabética (A–Z)":
    filtrados = sorted(filtrados, key=lambda x: x["nome"].lower())
elif ordem == "Ordem inversa (Z–A)":
    filtrados = sorted(filtrados, key=lambda x: x["nome"].lower(), reverse=True)
elif ordem == "Rating (maior → menor)":
    filtrados = sorted(filtrados, key=lambda x: parse_rating(x["rating"]), reverse=True)
elif ordem == "Rating (menor → maior)":
    filtrados = sorted(filtrados, key=lambda x: parse_rating(x["rating"]))


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
                emoji_prefix = f"{jogo['emoji']} " if jogo["emoji"] else ""
                st.markdown(
                    f"""
<div class="card-base cool-card">
    <div class="game-title">{emoji_prefix}{jogo['nome']}</div>
    <div class="game-meta" style="font-size:0.86rem; color:#6b7280; margin-top:4px;">
        <strong>Rating:</strong> {jogo['rating']} · 
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
        # LISTA: só o nome aparece; todo o resto vai para o expander
        for jogo in filtrados:
            emoji_prefix = f"{jogo['emoji']} " if jogo["emoji"] else ""

            # cartão minimal com apenas o nome
            st.markdown(
                f"""
<div class="card-base list-card">
    <div class="game-title">{emoji_prefix}{jogo['nome']}</div>
</div>
""",
                unsafe_allow_html=True,
            )

            # tudo o resto dentro da descrição
            with st.expander("Ver descrição", expanded=False):
                st.markdown(
                    f"**Rating:** {jogo['rating']} · **Tempo:** {jogo['tempo']} · "
                    f"**Jogadores:** {jogo['jogadores']} · **Tipo:** {jogo['tipo']}"
                )
                st.write(jogo["descricao"])
                if jogo["tags"]:
                    st.markdown(
                        "Tags: " + " ".join(f"`{t}`" for t in jogo["tags"])
                    )
