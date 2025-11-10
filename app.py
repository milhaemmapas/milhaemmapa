import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MeasureControl, Fullscreen, Draw, MousePosition
import json
import re
import os
import unicodedata

# =====================================================
# Configuração inicial com tema moderno
# =====================================================
# Estado inicial
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'default_tab' not in st.session_state:
    st.session_state.default_tab = 'home'

# Ler query params para navegação direta (home → abas)
try:
    qp = st.query_params  # Streamlit 1.33+
except Exception:
    qp = st.experimental_get_query_params()  # fallback versões anteriores

def _qp_get(name, default=None):
    v = qp.get(name, default)
    if isinstance(v, list):
        return v[0] if v else default
    return v

qp_page = _qp_get('page')
qp_tab  = _qp_get('tab')
if qp_page:
    st.session_state.page = qp_page
if qp_tab:
    st.session_state.default_tab = qp_tab

# Sidebar aberta/fechada conforme página
sidebar_state_cfg = "collapsed" if st.session_state.page == 'home' else "expanded"

st.set_page_config(
    page_title="ATLAS • Milhã",
    layout="wide",
    initial_sidebar_state=sidebar_state_cfg,
    menu_items={
        'Get Help': 'https://www.milha.ce.gov.br',
        'Report a bug': None,
        'About': "ATLAS Geoespacial - Plataforma de dados territoriais de Milhã"
    }
)

# Paleta de cores
COLORS = {
    "primary": "#1E3A8A",
    "secondary": "#059669",
    "accent": "#EA580C",
    "light_bg": "#F0F9FF",
    "card_bg": "#FFFFFF",
    "text_dark": "#1E293B",
    "text_light": "#64748B",
    "border": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "sidebar_bg": "#0F172A",
    "sidebar_text": "#E2E8F0"
}

# =====================================================
# CSS Global Atualizado com Design Moderno
# =====================================================
def css_global():
    st.markdown(
        f"""
        <style>
            .main {{
                background-color: {COLORS["light_bg"]};
            }}
            .block-container {{
                padding-top: 1rem;
                padding-bottom: 1rem;
            }}

            .main-header {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white;
                padding: 2rem 1rem;
                border-radius: 0 0 20px 20px;
                margin-bottom: 2rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }}
            .header-content {{
                display: flex;
                align-items: center;
                gap: 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header-text h1 {{
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                color: white;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header-text p {{
                font-size: 1.1rem;
                opacity: 0.95;
                margin-bottom: 0;
                font-weight: 400;
            }}
            .header-logo {{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                border: 4px solid rgba(255,255,255,0.3);
                padding: 8px;
                background: rgba(255,255,255,0.15);
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}

            .modern-card {{
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.08);
                border: 1px solid rgba(255,255,255,0.2);
                margin-bottom: 1.5rem;
                transition: all 0.3s ease;
            }}
            .modern-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.15);
                border: 1px solid rgba(255,255,255,0.3);
            }}

            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
                background: transparent;
                border-bottom: 2px solid {COLORS["border"]};
            }}
            .stTabs [data-baseweb="tab"] {{
                background: transparent;
                border: none;
                border-radius: 12px 12px 0 0;
                padding: 1rem 2rem;
                font-weight: 600;
                color: {COLORS["text_light"]};
                transition: all 0.3s ease;
                margin: 0 4px;
            }}
            .stTabs [aria-selected="true"] {{
                background: {COLORS["primary"]} !important;
                color: white !important;
                box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
            }}

            .css-1d391kg, .css-1lcbmhc {{
                background: {COLORS["sidebar_bg"]} !important;
            }}
            .sidebar-content {{ padding: 2rem 1rem; }}
            .stExpander, .st-expander {{
                border: 1px solid rgba(255,255,255,0.15) !important;
                border-radius: 14px !important;
                background: rgba(255,255,255,0.06) !important;
                margin-bottom: 10px !important;
            }}
            div.streamlit-expanderHeader {{
                color: {COLORS["sidebar_text"]} !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, rgba(30,58,138,0.35), rgba(5,150,105,0.25)) !important;
                border-radius: 12px !important;
                padding: 8px 10px !important;
            }}
            .stCheckbox label {{
                color: {COLORS["sidebar_text"]} !important;
                font-weight: 500;
            }}

            .stat-card {{
                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7));
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 2rem;
                text-align: center;
                border: 1px solid rgba(255,255,255,0.3);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }}
            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                transition: left 0.5s;
            }}
            .stat-card:hover::before {{ left: 100%; }}
            .feature-icon {{
                font-size: 3rem;
                margin-bottom: 1rem;
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
            }}
            .stat-number {{
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
            }}
            .stat-label {{ color: {COLORS["text_light"]}; font-size: 1rem; font-weight: 600; }}

            @keyframes fadeInUp {{ from {{opacity:0;transform:translateY(30px);}} to {{opacity:1;transform:translateY(0);}} }}
            .fade-in {{ animation: fadeInUp 0.8s ease-out; }}
            @keyframes float {{ 0%,100% {{transform:translateY(0);}} 50% {{transform:translateY(-10px);}} }}
            .floating {{ animation: float 3s ease-in-out infinite; }}

            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: {COLORS["light_bg"]}; }}
            ::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: linear-gradient(135deg, {COLORS["secondary"]}, {COLORS["primary"]});
            }}

            /* ===== Estilo dos botões de navegação da HOME ===== */
            #home-nav {{ margin-top: .5rem; }}
            #home-nav .row {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 14px;
            }}
            #home-nav div[data-testid="stButton"] > button {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                color: #fff; border: 0; border-radius: 14px;
                font-weight: 800; font-size: 1.05rem;
                padding: 16px 18px; height: 64px; width: 100%;
                box-shadow: 0 6px 18px rgba(0,0,0,.12);
                transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
                position: relative;
            }}
            #home-nav div[data-testid="stButton"] > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 28px rgba(0,0,0,.20);
                filter: brightness(1.03);
            }}
            #home-nav div[data-testid="stButton"] > button:focus {{
                outline: 3px solid {COLORS["accent"]}55;
                outline-offset: 2px;
            }}
            #home-nav div[data-testid="stButton"] > button::before {{
                content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 6px;
                border-radius: 14px 0 0 14px;
                background: linear-gradient(180deg, {COLORS["accent"]}, {COLORS["secondary"]});
                opacity: .9;
            }}
            #home-nav div[data-testid="stButton"] {{ position: relative; }}

            /* ===== Estilo do botão de VOLTAR na SIDEBAR ===== */
            #sidebar-back div[data-testid="stButton"] > button {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                color: #fff; border: 0; border-radius: 12px;
                font-weight: 800; font-size: 1.0rem;
                padding: 12px 14px; width: 100%;
                box-shadow: 0 6px 16px rgba(0,0,0,.14);
                transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
                position: relative;
            }}
            #sidebar-back div[data-testid="stButton"] > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 12px 26px rgba(0,0,0,.22);
                filter: brightness(1.03);
            }}
            #sidebar-back div[data-testid="stButton"] > button::before {{
                content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
                border-radius: 12px 0 0 12px;
                background: linear-gradient(180deg, {COLORS["accent"]}, {COLORS["secondary"]});
                opacity: .9;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def create_header():
    st.markdown(
        f"""
        <div class="main-header fade-in">
            <div class="header-content">
                <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã" class="header-logo floating">
                <div class="header-text">
                    <h1>ATLAS Geoespacial de Milhã</h1>
                    <p>Visualize dados territoriais, obras públicas e infraestrutura municipal de forma interativa e moderna</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Botões da HOME
    if st.session_state.page == 'home':
        st.markdown("<div id='home-nav'><div class='row'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗺️ Explorar Mapas", key="btn_mapas", use_container_width=True):
                st.session_state.page = "maps"
                st.session_state.default_tab = "maps"
                st.rerun()
        with col2:
            if st.button("🏗️ Ver Obras", key="btn_obras", use_container_width=True):
                st.session_state.page = "works"
                st.session_state.default_tab = "works"
                st.rerun()
        with col3:
            if st.button("📊 Todos os Dados", key="btn_dados", use_container_width=True):
                st.session_state.page = "data"
                st.session_state.default_tab = "home"
                st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.markdown("---")


# =====================================================
# Componentes Modernos
# =====================================================
def render_card(title_html: str, body_html: str):
    st.markdown(
        f"""
        <div class="modern-card fade-in">
            {title_html}
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def create_sidebar():
    if st.session_state.page == 'home':
        return {
            "show_distritos": False,
            "show_sede": False,
            "show_localidades": False,
            "show_estradas": False,
            "show_urbanas": False,
            "show_escolas": False,
            "show_unidades_saude": False,
            "show_obras": False,
            "show_tecnologias": False,
            "show_pocos_cidade": False,
            "show_pocos_rural": False,
            "show_espelhos": False,
            "show_outorgas": False,
            "enable_measure": False,
            "enable_draw": False,
            "enable_fullscreen": False,
            "show_coords": False
        }

    with st.sidebar:
        st.markdown(
        f"""
        <div class="sidebar-content">
            <div style="text-align: center; margin-bottom: 2rem;">
                <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã"
                     style="width: 80px; height: 80px; border-radius: 50%; border: 3px solid #1E3A8A55;">
                <h3 style="color: #1E3A8A; margin-top: 1rem; font-weight: 700;">Camadas do Mapa</h3>
                <p style="color: #059669; font-size: 0.9rem; font-weight: 500;">
                    As camadas estão separadas por categorias.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

        with st.expander("🗾 Território", expanded=True):
            show_distritos   = st.checkbox("Distritos", True, key="sidebar_distritos")
            show_sede        = st.checkbox("Sede Distritos", True, key="sidebar_sede")
            show_localidades = st.checkbox("Localidades", False, key="sidebar_localidades")
            show_estradas    = st.checkbox("Estradas", False, key="sidebar_estradas")
            show_urbanas     = st.checkbox("Áreas Urbanas", False, key="sidebar_urbanas")

        with st.expander("🏗️ Infraestrutura", expanded=True):
            show_escolas          = st.checkbox("Escolas Públicas", False, key="sidebar_escolas")
            show_unidades_saude   = st.checkbox("Unidades de Saúde", False, key="sidebar_unidades_saude")
            show_obras            = st.checkbox("Obras Municipais", True, key="sidebar_obras")

        with st.expander("💧 Recursos Hídricos", expanded=False):
            show_tecnologias   = st.checkbox("Tecnologias Sociais", False, key="sidebar_tecnologias")
            show_pocos_cidade  = st.checkbox("Poços Cidade", False, key="sidebar_pocos_cidade")
            show_pocos_rural   = st.checkbox("Poços Rural", False, key="sidebar_pocos_rural")
            show_espelhos      = st.checkbox("Espelhos d'Água", False, key="sidebar_espelhos")
            show_outorgas      = st.checkbox("Outorgas Vigentes", False, key="sidebar_outorgas")

        with st.expander("⚙️ Ferramentas", expanded=False):
            enable_measure     = st.checkbox("Medir", True, key="sidebar_measure")
            enable_draw        = st.checkbox("Desenhar", True, key="sidebar_draw")
            enable_fullscreen  = st.checkbox("Tela Cheia", True, key="sidebar_fullscreen")
            show_coords        = st.checkbox("Coordenadas", True, key="sidebar_coords")

        # Espaço flexível para empurrar o botão para baixo
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        
        # Botão na parte inferior
        st.markdown("<div id='sidebar-back'>", unsafe_allow_html=True)
        if st.button("🏠 Voltar à Página Inicial", use_container_width=True, key="btn_voltar_home"):
            st.session_state.page = "home"
            try:
                st.query_params.clear()
            except Exception:
                st.experimental_set_query_params()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    return {
        "show_distritos": show_distritos,
        "show_sede": show_sede,
        "show_localidades": show_localidades,
        "show_estradas": show_estradas,
        "show_urbanas": show_urbanas,
        "show_escolas": show_escolas,
        "show_unidades_saude": show_unidades_saude,
        "show_obras": show_obras,
        "show_tecnologias": show_tecnologias,
        "show_pocos_cidade": show_pocos_cidade,
        "show_pocos_rural": show_pocos_rural,
        "show_espelhos": show_espelhos,
        "show_outorgas": show_outorgas,
        "enable_measure": enable_measure,
        "enable_draw": enable_draw,
        "enable_fullscreen": enable_fullscreen,
        "show_coords": show_coords
    }
# =====================================================
# Funções utilitárias
# =====================================================
def autodetect_coords(df: pd.DataFrame):
    candidates_lat = [c for c in df.columns if re.search(r"(?:^|\b)(lat|latitude|y)(?:\b|$)", c, re.I)]
    candidates_lon = [c for c in df.columns if re.search(r"(?:^|\b)(lon|long|longitude|x)(?:\b|$)", c, re.I)]
    if candidates_lat and candidates_lon:
        return candidates_lat[0], candidates_lon[0]
    for c in df.columns:
        if re.search(r"coord|coordenad", c, re.I):
            try:
                tmp = df[c].astype(str).str.extract(r"(-?\d+[\.,]?\d*)\s*[,;]\s*(-?\d+[\.,]?\d*)")
                tmp.columns = ["LATITUDE", "LONGITUDE"]
                tmp["LATITUDE"] = tmp["LATITUDE"].str.replace(",", ".", regex=False).astype(float)
                tmp["LONGITUDE"] = tmp["LONGITUDE"].str.replace(",", ".", regex=False).astype(float)
                df["__LAT__"], df["__LON__"] = tmp["LATITUDE"], tmp["LONGITUDE"]
                return "__LAT__", "__LON__"
            except Exception:
                return None
    return None

def load_geojson_any(path_candidates):
    for p in path_candidates:
        if p and os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                st.warning(f"Erro ao ler {p}: {e}")
    return None

def br_money(x):
    try:
        s = str(x).replace("R$", "").strip()
        if "," in s and s.count(".") >= 1:
            s = s.replace(".", "")
        v = float(s.replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    except Exception:
        return str(x)

def sniff_read_csv(path: str) -> pd.DataFrame:
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            sample = f.read(4096); f.seek(0)
            sep = ";" if sample.count(";") > sample.count(",") else ","
            return pd.read_csv(f, sep=sep)
    except Exception as e:
        st.error(f"Falha ao ler CSV em '{path}': {e}")
        return pd.DataFrame()

def to_float_series(s: pd.Series) -> pd.Series:
    def _conv(v):
        if pd.isna(v): return None
        txt = str(v)
        m = re.search(r"-?\d+[.,]?\d*", txt)
        if not m: return None
        try: return float(m.group(0).replace(",", "."))
        except Exception: return None
    return s.apply(_conv)

def norm_col(c: str) -> str:
    s = unicodedata.normalize("NFKD", str(c))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")

def geojson_bounds(gj: dict):
    if not gj:
        return None
    lats, lons = [], []

    def _ingest_coords(coords):
        if isinstance(coords, (list, tuple)):
            if len(coords) == 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float)):
                lon, lat = coords[0], coords[1]
                lons.append(lon); lats.append(lat)
            else:
                for c in coords:
                    _ingest_coords(c)

    def _walk_feature(f):
        geom = f.get("geometry", {})
        coords = geom.get("coordinates", [])
        _ingest_coords(coords)

    t = gj.get("type")
    if t == "FeatureCollection":
        for f in gj.get("features", []):
            _walk_feature(f)
    elif t == "Feature":
        _walk_feature(gj)
    else:
        _ingest_coords(gj.get("coordinates", []))

    if not lats or not lons:
        return None
    return (min(lats), min(lons)), (max(lats), max(lons))

# ==== CORREÇÃO 1: garantir uma base padrão visível e as demais no controle ====
def add_all_base_tiles(m: folium.Map):
    # Base padrão (ativa)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OpenStreetMap",
        attr="© OpenStreetMap contributors",
        control=True,
        show=True
    ).add_to(m)

    # Outras bases (disponíveis no controle)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        name="CartoDB Positron",
        attr="© OpenStreetMap, © CARTO",
        control=True,
        show=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        name="CartoDB Dark",
        attr="© OpenStreetMap, © CARTO",
        control=True,
        show=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri Satellite",
        attr="Tiles © Esri",
        control=True,
        show=False
    ).add_to(m)

# ==== CORREÇÃO 2: overlays aparecem no botão de camadas ====
def FG(name: str, show: bool) -> folium.FeatureGroup:
    # overlay=True e control=True fazem a camada aparecer no LayerControl
    return folium.FeatureGroup(name=name, show=show, overlay=True, control=True)

# =====================================================
# Layout Principal
# =====================================================
css_global()
create_header()
sidebar_state = create_sidebar()

# =====================================================
# Abas principais (ordem dinâmica para abrir direto na desejada)
# =====================================================
if st.session_state.page != 'home':
    label_home  = "🏠 Página Inicial"
    label_works = "🏗️ Painel de Obras"
    label_maps  = "🗺️ Milhã em Mapas"

    desired = st.session_state.default_tab
    order = [label_home, label_works, label_maps]

    if desired == 'works':
        order = [label_works, label_maps, label_home]
    elif desired == 'maps':
        order = [label_maps, label_works, label_home]
    elif desired == 'data':
        order = [label_home, label_works, label_maps]

    tabs = st.tabs(order)
    tab_map = {order[i]: tabs[i] for i in range(len(order))}
else:
    # HOME — mostra conteúdo e encerra
    def render_home_content():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(
                """
                <div class="stat-card fade-in">
                    <div class="feature-icon">📊</div>
                    <div class="stat-number">156</div>
                    <div class="stat-label">Dados Geoespaciais</div>
                </div>
                """, unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                """
                <div class="stat-card fade-in">
                    <div class="feature-icon">🏗️</div>
                    <div class="stat-number">42</div>
                    <div class="stat-label">Obras Monitoradas</div>
                </div>
                """, unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                """
                <div class="stat-card fade-in">
                    <div class="feature-icon">💧</div>
                    <div class="stat-number">67</div>
                    <div class="stat-label">Recursos Hídricos</div>
                </div>
                """, unsafe_allow_html=True
            )
        with col4:
            st.markdown(
                """
                <div class="stat-card fade-in">
                    <div class="feature-icon">🏥</div>
                    <div class="stat-number">23</div>
                    <div class="stat-label">Unidades de Saúde</div>
                </div>
                """, unsafe_allow_html=True
            )

        colA, colB = st.columns(2)
        def render_card(title_html: str, body_html: str):
            st.markdown(
                f"""
                <div class="modern-card fade-in">
                    {title_html}
                    {body_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with colA:
            render_card(
                "<h2 style='background: linear-gradient(135deg, #1E3A8A, #059669); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>🌟 Bem-vindo ao ATLAS Geoespacial</h2>",
                """
                <p style='font-size: 1.1rem; line-height: 1.6;'>
                    Esta plataforma integra <strong>dados geoespaciais</strong> do município para apoiar a tomada de decisões públicas,
                    qualificar projetos urbanos e aproximar a gestão municipal dos cidadãos.
                </p>
                <div style='background: linear-gradient(135deg, rgba(30, 58, 138, 0.1), rgba(5, 150, 105, 0.1)); padding: 1.5rem; border-radius: 12px; margin: 1.5rem 0;'>
                    <h4 style='color: #1E3A8A; margin-bottom: 1rem;'>🎯 Objetivos Principais:</h4>
                    <ul style='color: #64748B;'>
                        <li><strong>Transparência</strong>: Informações públicas acessíveis</li>
                        <li><strong>Planejamento</strong>: Suporte ao desenvolvimento urbano</li>
                        <li><strong>Monitoramento</strong>: Acompanhamento em tempo real</li>
                        <li><strong>Participação</strong>: Engajamento comunitário</li>
                    </ul>
                </div>
                """
            )
        with colB:
            render_card(
                "<h3>🚀 Comece a Explorar</h3>",
                """
                <p style='font-size: 1.1rem; line-height: 1.6;'>
                    Esta plataforma integra <strong>dados geoespaciais</strong> do município para apoiar a tomada de decisões públicas,
                    qualificar projetos urbanos e aproximar a gestão municipal dos cidadãos.
                </p>
                <div style='display: grid; gap: 1rem;'>
                    <div style='display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(30, 58, 138, 0.05); border-radius: 12px;'>
                        <div style='font-size: 2rem;'>🗺️</div>
                        <div>
                            <strong>Milhã em Mapas</strong><br>
                            <small>Explore camadas territoriais interativas</small>
                        </div>
                    </div>
                    <div style='display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(5, 150, 105, 0.05); border-radius: 12px;'>
                        <div style='font-size: 2rem;'>🏗️</div>
                        <div>
                            <strong>Painel de Obras</strong><br>
                            <small>Monitore projetos municipais</small>
                        </div>
                    </div>
                    <div style='display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(234, 88, 12, 0.05); border-radius: 12px;'>
                        <div style='font-size: 2rem;'>💧</div>
                        <div>
                            <strong>Recursos Hídricos</strong><br>
                            <small>Visualize poços e tecnologias sociais</small>
                        </div>
                    </div>
                </div>
                """
            )

    render_home_content()
    st.stop()

# =====================================================
# 2) Painel de Obras
# =====================================================
with tab_map["🏗️ Painel de Obras"]:
    def render_card(title_html: str, body_html: str):
        st.markdown(
            f"""
            <div class="modern-card fade-in">
                {title_html}
                {body_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_card(
        "<h2>🏗️ Painel de Obras Municipais</h2>",
        "<p>Visualize e acompanhe o andamento das obras públicas em Milhã</p>",
    )

    CSV_OBRAS_CANDIDATES = ["dados/milha_obras.csv", "/mnt/data/milha_obras.csv"]
    CSV_OBRAS = next((p for p in CSV_OBRAS_CANDIDATES if os.path.exists(p)), CSV_OBRAS_CANDIDATES[0])

    df_obras_raw = sniff_read_csv(CSV_OBRAS)

    if not df_obras_raw.empty:
        colmap = {c: norm_col(c) for c in df_obras_raw.columns}
        df_obras = df_obras_raw.rename(columns=colmap).copy()

        lat_col = next((c for c in df_obras.columns if c in {"latitude","lat"}), None)
        lon_col = next((c for c in df_obras.columns if c in {"longitude","long","lon"}), None)
        if not lat_col or not lon_col:
            coords = autodetect_coords(df_obras_raw.copy())
            if coords:
                lat_col, lon_col = coords

        if not lat_col or not lon_col:
            st.error("Não foi possível localizar colunas de latitude/longitude.")
            st.stop()

        df_obras["__LAT__"] = to_float_series(df_obras[lat_col])
        df_obras["__LON__"] = to_float_series(df_obras[lon_col])

        lat_s = pd.to_numeric(df_obras["__LAT__"], errors="coerce")
        lon_s = pd.to_numeric(df_obras["__LON__"], errors="coerce")

        def _pct_inside(a, b):
            try:
                m = (a.between(-6.5, -4.5)) & (b.between(-40.5, -38.0))
                return float(m.mean())
            except Exception:
                return 0.0

        cands = [
            ("orig", lat_s, lon_s, _pct_inside(lat_s, lon_s)),
            ("swap", lon_s, lat_s, _pct_inside(lon_s, lat_s)),
            ("neg_lon", lat_s, lon_s.mul(-1.0), _pct_inside(lat_s, lon_s.mul(-1.0))),
            ("swap_neg", lon_s, lat_s.mul(-1.0), _pct_inside(lon_s, lat_s.mul(-1.0))),
        ]
        best = max(cands, key=lambda x: x[3])
        if best[0] != "orig" and best[3] >= cands[0][3]:
            df_obras["__LAT__"], df_obras["__LON__"] = best[1], best[2]

        df_map = df_obras.dropna(subset=["__LAT__", "__LON__"]).copy()

        cols = list(df_obras.columns)
        def pick_norm(*options):
            return next((c for c in cols if c in [norm_col(o) for o in options]), None)

        c_obra    = pick_norm("Obra", "Nome", "Projeto", "Descrição")
        c_status  = pick_norm("Status", "Situação")
        c_empresa = pick_norm("Empresa", "Contratada")
        c_valor   = pick_norm("Valor", "Valor Total", "Custo")
        c_bairro  = pick_norm("Bairro", "Localidade")
        c_dtini   = pick_norm("Início", "Data Início", "Inicio")
        c_dtfim   = pick_norm("Término", "Data Fim", "Termino")

        st.success(f"✅ **{len(df_map)} obra(s)** com coordenadas válidas encontradas")

        base_dir_candidates = ["dados", "/mnt/data"]
        gj_distritos = load_geojson_any([os.path.join(b, "milha_dist_polig.geojson") for b in base_dir_candidates])
        gj_sede      = load_geojson_any([os.path.join(b, "Distritos_pontos.geojson") for b in base_dir_candidates])

        col_map, col_info = st.columns([3, 1])

        with col_info:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📊 Informações</div>', unsafe_allow_html=True)

            total_obras = len(df_obras)
            obras_com_coords = len(df_map)
            status_counts = df_obras[c_status].value_counts() if c_status else pd.Series()

            st.metric("Total de Obras", total_obras)
            st.metric("Com Coordenadas", obras_com_coords)

            if not status_counts.empty:
                st.markdown("**Status das Obras:**")
                for status, count in status_counts.head(5).items():
                    st.write(f"• {status}: {count}")

            st.markdown('</div>', unsafe_allow_html=True)

        with col_map:
            bounds = None
            if gj_distritos:
                b = geojson_bounds(gj_distritos)
                if b:
                    bounds = b
                    (min_lat, min_lon), (max_lat, max_lon) = b
                    center_lat = (min_lat + max_lat) / 2.0
                    center_lon = (min_lon + max_lon) / 2.0
                    default_center = [center_lat, center_lon]
                else:
                    default_center = [-5.680, -39.200]
            else:
                default_center = [-5.680, -39.200]

            m2 = folium.Map(location=default_center, zoom_start=12, tiles=None, control_scale=True)
            add_all_base_tiles(m2)

            if sidebar_state["enable_fullscreen"]:
                Fullscreen(position='topleft').add_to(m2)
            if sidebar_state["enable_measure"]:
                MeasureControl(
                    primary_length_unit="meters",
                    secondary_length_unit="kilometers", 
                    primary_area_unit="hectares",
                    position='topleft'
                ).add_to(m2)
            if sidebar_state["enable_draw"]:
                Draw(export=True, position='topright').add_to(m2)
            if sidebar_state["show_coords"]:
                MousePosition(position='bottomleft').add_to(m2)

            if sidebar_state["show_distritos"] and gj_distritos:
                fg_dist = FG("Distritos", True)
                folium.GeoJson(
                    gj_distritos,
                    name="Distritos",
                    style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.1, "color": "#000000", "weight": 1},
                ).add_to(fg_dist)
                fg_dist.add_to(m2)

            if sidebar_state["show_sede"] and gj_sede:
                fg_sede = FG("Sede Distritos", True)
                for f in gj_sede.get("features", []):
                    x, y = f["geometry"]["coordinates"]
                    nome = f.get("properties", {}).get("nome_do_distrito", "Sede")
                    folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(fg_sede)
                fg_sede.add_to(m2)

            if sidebar_state["show_obras"] and not df_map.empty:
                def status_icon_color(status_val: str):
                    s = (str(status_val) if status_val is not None else "").strip().lower()
                    if any(k in s for k in ["conclu", "finaliz"]):     return "green"
                    if any(k in s for k in ["execu", "andamento"]):    return "orange"
                    if any(k in s for k in ["paralis", "suspens"]):    return "red"
                    if any(k in s for k in ["planej", "licita", "proj"]): return "blue"
                    return "gray"

                fg_obras = FG("Obras Municipais", True)
                ignore_cols = {"__LAT__", "__LON__"}
                for _, r in df_map.iterrows():
                    nome   = str(r.get(c_obra, "Obra")) if c_obra else "Obra"
                    status = str(r.get(c_status, "-")) if c_status else "-"
                    empresa= str(r.get(c_empresa, "-")) if c_empresa else "-"
                    valor  = br_money(r.get(c_valor)) if c_valor else "-"
                    bairro = str(r.get(c_bairro, "-")) if c_bairro else "-"
                    dtini  = str(r.get(c_dtini, "-")) if c_dtini else "-"
                    dtfim  = str(r.get(c_dtfim, "-")) if c_dtfim else "-"

                    extra_rows = []
                    for c in df_obras.columns:
                        if c in ignore_cols or c in {c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim}:
                            continue
                        val = r.get(c, "")
                        if pd.notna(val) and str(val).strip() != "":
                            extra_rows.append(f"<tr><td><b>{c}</b></td><td>{val}</td></tr>")
                    extra_html = "".join(extra_rows)

                    popup_html = (
                        "<div style='font-family:Arial; font-size:13px'>"
                        f"<h4 style='margin:4px 0 8px 0'>🧱 {nome}</h4>"
                        f"<p style='margin:0 0 6px'><b>Status:</b> {status}</p>"
                        f"<p style='margin:0 0 6px'><b>Empresa:</b> {empresa}</p>"
                        f"<p style='margin:0 0 6px'><b>Valor:</b> {valor}</p>"
                        f"<p style='margin:0 0 6px'><b>Bairro/Localidade:</b> {bairro}</p>"
                        f"<p style='margin:0 0 6px'><b>Início:</b> {dtini} &nbsp; <b>Término:</b> {dtfim}</p>"
                        + (f"<table border='1' cellpadding='4' cellspacing='0' style='border-collapse:collapse; margin-top:6px'>{extra_html}</table>" if extra_html else "")
                        + "</div>"
                    )

                    folium.Marker(
                        location=[r["__LAT__"], r["__LON__"]],
                        tooltip=nome,
                        popup=folium.Popup(popup_html, max_width=420),
                        icon=folium.Icon(color=status_icon_color(status), icon="info-sign")
                    ).add_to(fg_obras)

                fg_obras.add_to(m2)

            if bounds:
                (min_lat, min_lon), (max_lat, max_lon) = bounds
                m2.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            elif not df_map.empty:
                m2.fit_bounds([[df_map["__LAT__"].min(), df_map["__LON__"].min()],
                               [df_map["__LAT__"].max(), df_map["__LON__"].max()]])

            # Layer control com basemaps e overlays visíveis
            folium.LayerControl(collapsed=True, position='topleft').add_to(m2)
            folium_static(m2, width=800, height=600)

        st.markdown("### 📋 Tabela de Obras")
        priority = [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]
        ordered = [c for c in priority if c and c in df_obras.columns]
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)
    else:
        st.error(f"❌ Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")

# =====================================================
# 3) Milhã em Mapas
# =====================================================
with tab_map["🗺️ Milhã em Mapas"]:
    def render_card(title_html: str, body_html: str):
        st.markdown(
            f"""
            <div class="modern-card fade-in">
                {title_html}
                {body_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_card(
        "<h2>🗺️ Milhã em Mapas</h2>",
        "<p>Explore as camadas territoriais, infraestrutura e recursos hídricos do município</p>",
    )

    if "m3_view" not in st.session_state:
        st.session_state["m3_view"] = {"center": [-5.680, -39.200], "zoom": 11}

    base_dir_candidates = ["dados", "/mnt/data"]
    files = {
        "Distritos": "milha_dist_polig.geojson",
        "Sede Distritos": "Distritos_pontos.geojson",
        "Localidades": "Localidades.geojson",
        "Áreas Urbanas": "milha_urbanas.geojson",
        "Escolas": "Escolas_publicas.geojson",
        "Unidades de Saúde": "Unidades_saude.geojson",
        "Tecnologias Sociais": "teclogias_sociais.geojson",
        "Poços Cidade": "pocos_cidade_mil.geojson",
        "Poços Zona Rural": "pocos_rural_mil.geojson",
        "Estradas": "estradas_milha.geojson",
        "Outorgas Vigentes": "outorgas_milha.geojson",
        "Espelhos d'Água": "espelhos_dagua.geojson",
    }
    data_geo = {
        name: load_geojson_any([os.path.join(b, fname) for b in base_dir_candidates])
        for name, fname in files.items()
    }

    center = st.session_state["m3_view"]["center"]
    zoom = st.session_state["m3_view"]["zoom"]

    m3 = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        control_scale=True
    )

    add_all_base_tiles(m3)

    if sidebar_state["enable_fullscreen"]:
        Fullscreen(position='topleft').add_to(m3)
    if sidebar_state["enable_measure"]:
        MeasureControl(
            primary_length_unit="meters",
            secondary_length_unit="kilometers",
            primary_area_unit="hectares",
            position='topleft'
        ).add_to(m3)
    if sidebar_state["enable_draw"]:
        Draw(export=True, position='topright').add_to(m3)
    if sidebar_state["show_coords"]:
        MousePosition(position='bottomleft').add_to(m3)

    if data_geo.get("Distritos"):
        b = geojson_bounds(data_geo["Distritos"])
        if b:
            (min_lat, min_lon), (max_lat, max_lon) = b
            m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Overlays no controle
    if sidebar_state["show_distritos"] and data_geo.get("Distritos"):
        fg_d = FG("Distritos", True)
        folium.GeoJson(
            data_geo["Distritos"],
            name="Distritos",
            style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.2, "color": "#000000", "weight": 1},
            tooltip=folium.GeoJsonTooltip(fields=list(data_geo["Distritos"]["features"][0]["properties"].keys())[:3])
        ).add_to(fg_d)
        fg_d.add_to(m3)

    if sidebar_state["show_sede"] and data_geo.get("Sede Distritos"):
        fg_sd = FG("Sede Distritos", True)
        for ftr in data_geo["Sede Distritos"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            nome = ftr["properties"].get("nome_do_distrito", "Sede")
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(fg_sd)
        fg_sd.add_to(m3)

    if sidebar_state["show_localidades"] and data_geo.get("Localidades"):
        fg_loc = FG("Localidades", True)
        for ftr in data_geo["Localidades"]["features"]:
            coords = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Localidade", "Localidade")
            distrito = props.get("Distrito", "Não informado")
            
            popup_info = f"""
            <div style='font-family: Arial, sans-serif; border: 2px solid #4CAF50; border-radius: 8px; padding: 8px; background-color: #f0fff0;'>
            <h4 style='margin-top: 0; margin-bottom: 8px; color: #2E7D32;'>🏘️ Localidade</h4>
            <p style='margin: 4px 0;'><strong>📛 Nome:</strong> {nome}</p>
            <p style='margin: 4px 0;'><strong>📍 Distrito:</strong> {distrito}</p>
            </div>
            """
            
            folium.Marker(
                location=[coords[1], coords[0]],
                tooltip=nome,
                popup=folium.Popup(popup_info, max_width=300),
                icon=folium.CustomIcon("https://i.ibb.co/kgbmmjWc/location-icon-242304.png", icon_size=(18, 18))
            ).add_to(fg_loc)
        fg_loc.add_to(m3)

    if sidebar_state["show_urbanas"] and data_geo.get("Áreas Urbanas"):
        fg_urbanas = FG("Áreas Urbanas", True)
        folium.GeoJson(
            data_geo["Áreas Urbanas"],
            name="Áreas Urbanas",
            style_function=lambda x: {
                "fillColor": "#FF69B4",
                "fillOpacity": 0.3,
                "color": "#8B008B",
                "weight": 2,
                "opacity": 0.8
            },
            tooltip=folium.GeoJsonTooltip(
                fields=list(data_geo["Áreas Urbanas"]["features"][0]["properties"].keys())[:3],
                aliases=["Propriedade:"] * 3,
                style=("font-family: Arial; font-size: 12px;")
            )
        ).add_to(fg_urbanas)
        fg_urbanas.add_to(m3)

    if sidebar_state["show_estradas"] and data_geo.get("Estradas"):
        fg_estr = FG("Estradas", True)
        folium.GeoJson(
            data_geo["Estradas"],
            name="Estradas",
            style_function=lambda x: {
                "color": "#8B4513",
                "weight": 2,
                "opacity": 0.8
            },
            tooltip=folium.GeoJsonTooltip(
                fields=list(data_geo["Estradas"]["features"][0]["properties"].keys())[:3],
                aliases=["Propriedade:"] * 3
            )
        ).add_to(fg_estr)
        fg_estr.add_to(m3)

    if sidebar_state["show_escolas"] and data_geo.get("Escolas"):
        fg_esc = FG("Escolas Públicas", True)
        for ftr in data_geo["Escolas"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("no_entidad", props.get("Name", "Escola"))
            popup = (
                "<div style='font-family:Arial;font-size:13px'>"
                f"<b>Escola:</b> {nome}<br>"
                f"<b>Endereço:</b> {props.get('endereco','-')}"
                "</div>"
            )
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="red", icon="education")).add_to(fg_esc)
        fg_esc.add_to(m3)

    if sidebar_state["show_unidades_saude"] and data_geo.get("Unidades de Saúde"):
        fg_saude = FG("Unidades de Saúde", True)
        for ftr in data_geo["Unidades de Saúde"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("nome", props.get("Name", "Unidade"))
            
            popup = (
                "<div style='font-family: Arial, sans-serif; border: 2px solid #2A4D9B; border-radius: 8px; padding: 8px; background-color: #f9f9f9;'>"
                "<h4 style='margin-top: 0; margin-bottom: 8px; color: #2A4D9B; border-bottom: 1px solid #ccc;'>🏥 Unidades de Saúde</h4>"
                "<p style='margin: 4px 0;'><span style='color: #2A4D9B; font-weight: bold;'>📛 Unidade:</span> " + props.get("unidade", "Não informado") + "</p>"
                "<p style='margin: 4px 0;'><span style='color: #2A4D9B; font-weight: bold;'>📍 Endereço:</span> " + props.get("endereeo", "Não informado") + "</p>"
                "<p style='margin: 4px 0;'><span style='color: #2A4D9B; font-weight: bold;'>📞 Bairro:</span> " + str(props.get("bairro", "Não informado")) + "</p>"
                "<p style='margin: 4px 0;'><span style='color: #2A4D9B; font-weight: bold;'>🧭 Município:</span> " + props.get("municipio", "Não informado") + "</p>"
                "</div>"
            )
            
            folium.Marker(
                location=[y, x],
                popup=folium.Popup(popup, max_width=300),
                tooltip=nome,
                icon=folium.CustomIcon(
                    "https://i.ibb.co/rGdw6d71/hospital.png",
                    icon_size=(25, 25)
                )
            ).add_to(fg_saude)
        fg_saude.add_to(m3)

    if sidebar_state["show_tecnologias"] and data_geo.get("Tecnologias Sociais"):
        fg_tec = FG("Tecnologias Sociais", True)
        for ftr in data_geo["Tecnologias Sociais"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
            popup = "<div style='font-family:Arial;font-size:13px'><b>Local:</b> {}</div>".format(nome)
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="orange", icon="tint")).add_to(fg_tec)
        fg_tec.add_to(m3)

    if sidebar_state["show_outorgas"] and data_geo.get("Outorgas Vigentes"):
        fg_out = FG("Outorgas Vigentes", True)
        for ftr in data_geo["Outorgas Vigentes"]["features"]:
            props = ftr["properties"]
            coords = ftr["geometry"]["coordinates"]
            lng, lat = coords[0], coords[1]

            popup_content = f"""
            <div style='font-family:Arial;font-size:12px;max-width:300px'>
                <b>Requerente:</b> {props.get('REQUERENTE', 'N/A')}<br>
                <b>Tipo Manancial:</b> {props.get('TIPO MANANCIAL', 'N/A')}<br>
                <b>Tipo de Uso:</b> {props.get('TIPO DE USO', 'N/A')}<br>
                <b>Manancial:</b> {props.get('MANANCIAL', 'N/A')}<br>
                <b>Fim da Vigência:</b> {props.get('FIM DA VIGÊNCIA', 'N/A')}<br>
                <b>Volume Outorgado:</b> {props.get('VOLUME OUTORGADO (m³)', 'N/A')} m³
            </div>
            """

            tipo_uso = props.get('TIPO DE USO', '').upper()
            if 'IRRIGACAO' in tipo_uso:
                icon_color = 'green'
            elif 'ABASTECIMENTO_HUMANO' in tipo_uso:
                icon_color = 'blue'
            elif 'INDUSTRIA' in tipo_uso:
                icon_color = 'red'
            elif 'SERVICO_E_COMERCIO' in tipo_uso:
                icon_color = 'purple'
            else:
                icon_color = 'gray'

            folium.Marker(
                [lat, lng],
                tooltip=props.get('REQUERENTE', 'Outorga'),
                popup=folium.Popup(popup_content, max_width=300),
                icon=folium.Icon(color=icon_color, icon='file-text', prefix='fa')
            ).add_to(fg_out)
        fg_out.add_to(m3)

    if sidebar_state["show_espelhos"] and data_geo.get("Espelhos d'Água"):
        fg_esp = FG("Espelhos d'Água", True)
        folium.GeoJson(
            data_geo["Espelhos d'Água"],
            name="Espelhos d'Água",
            style_function=lambda x: {
                "fillColor": "#1E90FF",
                "fillOpacity": 0.7,
                "color": "#000080",
                "weight": 2,
                "opacity": 0.8
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["CODIGOES0", "AREA1"],
                aliases=["Código:", "Área (ha):"],
                style=("font-family: Arial; font-size: 12px;")
            )
        ).add_to(fg_esp)
        fg_esp.add_to(m3)

    if sidebar_state["show_pocos_cidade"] and data_geo.get("Poços Cidade"):
        fg_pc = FG("Poços Cidade", True)
        for ftr in data_geo["Poços Cidade"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Localidade", props.get("Name", "Poço"))
            popup = (
                "<div style='font-family:Arial;font-size:13px'>"
                f"<b>Localidade:</b> {nome}<br>"
                f"<b>Profundidade:</b> {props.get('Profundida','-')}<br>"
                f"<b>Vazão (L/h):</b> {props.get('Vazão_LH_2','-')}"
                "</div>"
            )
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="blue", icon="tint")).add_to(fg_pc)
        fg_pc.add_to(m3)

    if sidebar_state["show_pocos_rural"] and data_geo.get("Poços Zona Rural"):
        fg_pr = FG("Poços Zona Rural", True)
        for ftr in data_geo["Poços Zona Rural"]["features"]:
            coords = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
    
            popup_info = (
                "<div style='font-family: Arial, sans-serif; border: 2px solid #0059b3; border-radius: 8px; padding: 8px; background-color: #f0f8ff;'>"
                "<h4 style='margin-top: 0; margin-bottom: 8px; color: #0059b3; border-bottom: 1px solid #ccc;'>💧 Poço Rural</h4>"
                "<p style='margin: 4px 0;'><strong>📍 Localidade:</strong> " + str(props.get("Localidade", "Não informado")) + "</p>"
                "<p style='margin: 4px 0;'><strong>📏 Profundidade:</strong> " + str(props.get("Profundida_m", "Não informado")) + "</p>"
                "<p style='margin: 4px 0;'><strong>💦 Vazão (L/h):</strong> " + str(props.get("Vazão_LH", "Não informado")) + "</p>"
                "<p style='margin: 4px 0;'><strong>⚡ Energia:</strong> " + str(props.get("Energia", "Não informado")) + "</p>"
                "</div>"
            )
    
            folium.Marker(
                location=[coords[1], coords[0]],
                popup=folium.Popup(popup_info, max_width=300),
                tooltip=props.get("Localidade", "Poço Rural"),
                icon=folium.CustomIcon("https://i.ibb.co/6JrpxXMT/water.png", icon_size=(23, 23))
            ).add_to(fg_pr)
        fg_pr.add_to(m3)

    # Controle de camadas com basemaps e overlays
    folium.LayerControl(collapsed=True, position='topleft').add_to(m3)
    folium_static(m3, width=1200, height=700)

# =====================================================
# 1) Página Inicial (como aba) — mesmo conteúdo da HOME
# =====================================================
with tab_map["🏠 Página Inicial"]:
    st.write("")  # placeholder minimal, mantém consistência visual
    # você pode repetir o conteúdo da home aqui, se quiser

# =====================================================
# Rodapé
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: {COLORS["text_light"]}; padding: 3rem;'>
        <div style='font-size: 2rem; margin-bottom: 1rem;'>
            <span style='color: {COLORS["primary"]};'>ATLAS</span>
            <span style='color: {COLORS["secondary"]};'>Geoespacial</span>
        </div>
        <p style='font-size: 1.1rem; margin-bottom: 1rem;'><strong>Milhã - Ceará</strong></p>
        <p style='font-size: 0.9rem; opacity: 0.7;'>Desenvolvido para transparência e gestão pública eficiente • © 2024 Prefeitura Municipal de Milhã</p>
    </div>
    """,
    unsafe_allow_html=True
)
