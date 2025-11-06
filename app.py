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
# Inicializa estado da página usando query parameters
query_params = st.query_params

# Define a página atual baseada nos query parameters
if "page" in query_params:
    st.session_state.page = query_params["page"][0]
else:
    st.session_state.page = "home"

if "tab" in query_params:
    st.session_state.active_tab = query_params["tab"][0]
else:
    st.session_state.active_tab = "home"

# Configura sidebar baseado na página atual
sidebar_state = "collapsed" if st.session_state.page == 'home' else "expanded"

st.set_page_config(
    page_title="ATLAS • Milhã",
    layout="wide",
    initial_sidebar_state=sidebar_state,
    menu_items={
        'Get Help': 'https://www.milha.ce.gov.br',
        'Report a bug': None,
        'About': "ATLAS Geoespacial - Plataforma de dados territoriais de Milhã"
    }
)

# Paleta de cores moderna e sofisticada
COLORS = {
    "primary": "#1E3A8A",      # Azul escuro principal
    "secondary": "#059669",    # Verde esmeralda
    "accent": "#EA580C",       # Laranja vibrante
    "light_bg": "#F0F9FF",     # Azul claro de fundo
    "card_bg": "#FFFFFF",      # Branco para cards
    "text_dark": "#1E293B",    # Texto escuro
    "text_light": "#64748B",   # Texto claro
    "border": "#E2E8F0",       # Borda suave
    "success": "#10B981",      # Verde sucesso
    "warning": "#F59E0B",      # Amarelo alerta
    "error": "#EF4444",        # Vermelho erro
    "sidebar_bg": "#0F172A",   # Fundo escuro sidebar
    "sidebar_text": "#E2E8F0"  # Texto claro sidebar
}

# =====================================================
# CSS Global Atualizado com Design Moderno
# =====================================================
def css_global():
    st.markdown(
        f"""
        <style>
            /* Fundo e espaçamentos globais */
            .main {{
                background-color: {COLORS["light_bg"]};
            }}
            .block-container {{
                padding-top: 1rem;
                padding-bottom: 1rem;
            }}

            /* Header com gradiente */
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

            /* Cards */
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

            /* Abas */
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

            /* Sidebar */
            .css-1d391kg, .css-1lcbmhc {{
                background: {COLORS["sidebar_bg"]} !important;
            }}
            .sidebar-content {{
                padding: 2rem 1rem;
            }}
            .stExpander, .st-expander {{
                border: 1px solid rgba(255,255,255,0.15) !important;
                border-radius: 14px !important;
                background: rgba(255,255,255,0.06) !important;
                margin-bottom: 10px !important;
            }}
            .stExpander:hover, .st-expander:hover {{
                border-color: rgba(255,255,255,0.25) !important;
            }}
            /* Título do expander em cor forte da paleta */
            div.streamlit-expanderHeader {{
                color: {COLORS["sidebar_text"]} !important;
                font-weight: 700 !important;
                background: linear-gradient(135deg, rgba(30,58,138,0.35), rgba(5,150,105,0.25)) !important;
                border-radius: 12px !important;
                padding: 8px 10px !important;
            }}

            /* Checkboxes na sidebar */
            .stCheckbox label {{
                color: {COLORS["sidebar_text"]} !important;
                font-weight: 500;
            }}

            /* KPIs */
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
            .stat-card:hover::before {{
                left: 100%;
            }}
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
            .stat-label {{
                color: {COLORS["text_light"]};
                font-size: 1rem;
                font-weight: 600;
            }}

            /* Animações */
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(30px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .fade-in {{ animation: fadeInUp 0.8s ease-out; }}
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            .floating {{ animation: float 3s ease-in-out infinite; }}

            /* Scrollbar */
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: {COLORS["light_bg"]}; }}
            ::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                border-radius: 4px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: linear-gradient(135deg, {COLORS["secondary"]}, {COLORS["primary"]});
            }}

            /* Botões de navegação na paleta de cores */
            .nav-button {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                color: white;
                border: none;
                padding: 1.5rem 1rem;
                border-radius: 16px;
                font-weight: 700;
                font-size: 1.2rem;
                transition: all 0.3s ease;
                cursor: pointer;
                margin: 0.5rem 0;
                width: 100%;
                box-shadow: 0 4px 15px rgba(30, 58, 138, 0.3);
            }}
            .nav-button:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.2);
            }}
            .nav-button-map {{
                background: linear-gradient(135deg, {COLORS["primary"]}, #1E40AF);
            }}
            .nav-button-works {{
                background: linear-gradient(135deg, {COLORS["secondary"]}, #059669);
            }}
            .nav-button-data {{
                background: linear-gradient(135deg, {COLORS["accent"]}, #EA580C);
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
    
    # Botões de navegação apenas na home
    if st.session_state.page == 'home':
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🗺️ Explorar Mapas", use_container_width=True, type="primary", 
                        key="nav_maps"):
                st.query_params.clear()
                st.query_params["page"] = "app"
                st.query_params["tab"] = "maps"
                st.rerun()
        with col2:
            if st.button("🏗️ Ver Obras", use_container_width=True, type="primary",
                        key="nav_works"):
                st.query_params.clear()
                st.query_params["page"] = "app"
                st.query_params["tab"] = "works"
                st.rerun()
        with col3:
            if st.button("📊 Todos os Dados", use_container_width=True, type="primary",
                        key="nav_data"):
                st.query_params.clear()
                st.query_params["page"] = "app"
                st.query_params["tab"] = "home"
                st.rerun()
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
    # Só mostra sidebar se não for a página inicial
    if st.session_state.page == 'home':
        return {
            "show_distritos": False,
            "show_sede": False,
            "show_localidades": False,
            "show_estradas": False,
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
        # Botão para voltar à home
        if st.button("🏠 Voltar à Página Inicial", use_container_width=True):
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.rerun()
            
        st.markdown(
            f"""
            <div class="sidebar-content">
                <div style="text-align: center; margin-bottom: 2rem;">
                    <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã"
                         style="width: 80px; height: 80px; border-radius: 50%; border: 3px solid rgba(255,255,255,0.3);">
                    <h3 style="color: {COLORS['sidebar_text']}; margin-top: 1rem;">Camadas do Mapa</h3>
                    <p style="color: {COLORS['sidebar_text']}; opacity: 0.8; font-size: 0.9rem;">
                        Ative/desative as camadas por grupo. As bases ficam no botão do mapa.
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -------- Território --------
        with st.expander("🗾 Território", expanded=True):
            show_distritos   = st.checkbox("Distritos", True, key="sidebar_distritos")
            show_sede        = st.checkbox("Sede Distritos", True, key="sidebar_sede")
            show_localidades = st.checkbox("Localidades", False, key="sidebar_localidades")
            show_estradas    = st.checkbox("Estradas", False, key="sidebar_estradas")

        # -------- Infraestrutura --------
        with st.expander("🏗️ Infraestrutura", expanded=True):
            show_escolas          = st.checkbox("Escolas Públicas", False, key="sidebar_escolas")
            show_unidades_saude   = st.checkbox("Unidades de Saúde", False, key="sidebar_unidades_saude")
            show_obras            = st.checkbox("Obras Municipais", False, key="sidebar_obras")

        # -------- Recursos Hídricos --------
        with st.expander("💧 Recursos Hídricos", expanded=False):
            show_tecnologias   = st.checkbox("Tecnologias Sociais", False, key="sidebar_tecnologias")
            show_pocos_cidade  = st.checkbox("Poços Cidade", False, key="sidebar_pocos_cidade")
            show_pocos_rural   = st.checkbox("Poços Rural", False, key="sidebar_pocos_rural")
            show_espelhos      = st.checkbox("Espelhos d'Água", False, key="sidebar_espelhos")
            show_outorgas      = st.checkbox("Outorgas Vigentes", False, key="sidebar_outorgas")

        # -------- Ferramentas --------
        with st.expander("⚙️ Ferramentas", expanded=False):
            enable_measure     = st.checkbox("Medir", True, key="sidebar_measure")
            enable_draw        = st.checkbox("Desenhar", True, key="sidebar_draw")
            enable_fullscreen  = st.checkbox("Tela Cheia", True, key="sidebar_fullscreen")
            show_coords        = st.checkbox("Coordenadas", True, key="sidebar_coords")

    return {
        "show_distritos": show_distritos,
        "show_sede": show_sede,
        "show_localidades": show_localidades,
        "show_estradas": show_estradas,
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

# ===== Helpers para bases no botão do mapa e overlays fora do botão =====
def add_all_base_tiles(m: folium.Map):
    """Adiciona todas as bases no botão do mapa (LayerControl)."""
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        name="CartoDB Positron",
        attr="© OpenStreetMap, © CARTO",
        control=True
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        name="CartoDB Dark",
        attr="© OpenStreetMap, © CARTO",
        control=True
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        name="Esri Satellite",
        attr="Tiles © Esri",
        control=True
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="OpenStreetMap",
        attr="© OpenStreetMap contributors",
        control=True
    ).add_to(m)

def FG(name: str, show: bool) -> folium.FeatureGroup:
    """FeatureGroup overlay que fica fora do botão do mapa (control=False)."""
    return folium.FeatureGroup(name=name, show=show, overlay=True, control=False)

# =====================================================
# Conteúdo da Página Inicial
# =====================================================
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

# =====================================================
# Layout Principal Atualizado
# =====================================================
css_global()
create_header()

# Criar sidebar e obter estados
sidebar_state = create_sidebar()

# Lógica principal de navegação
if st.session_state.page == 'home':
    # Página inicial standalone
    render_home_content()
else:
    # Aplicação com abas
    aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])
    
    # Determina qual aba mostrar baseado nos query parameters
    if st.session_state.active_tab == "home":
        with aba1:
            render_home_content()
    elif st.session_state.active_tab == "works":
        with aba2:
            # =====================================================
            # 2) Painel de Obras
            # =====================================================
            render_card(
                "<h2>🏗️ Painel de Obras Municipais</h2>",
                "<p>Visualize e acompanhe o andamento das obras públicas em Milhã</p>",
            )

            CSV_OBRAS_CANDIDATES = ["dados/milha_obras.csv", "/mnt/data/milha_obras.csv"]
            CSV_OBRAS = next((p for p in CSV_OBRAS_CANDIDATES if os.path.exists(p)), CSV_OBRAS_CANDIDATES[0])

            df_obras_raw = sniff_read_csv(CSV_OBRAS)

            if not df_obras_raw.empty:
                # [TODO: Restante do código do painel de obras...]
                st.info("🚧 Funcionalidade de Obras em desenvolvimento...")
                st.write("Aqui será carregado o painel completo de obras municipais")
            else:
                st.error(f"❌ Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")
    
    elif st.session_state.active_tab == "maps":
        with aba3:
            # =====================================================
            # 3) Milhã em Mapas
            # =====================================================
            render_card(
                "<h2>🗺️ Milhã em Mapas</h2>",
                "<p>Explore as camadas territoriais, infraestrutura e recursos hídricos do município</p>",
            )
            
            # [TODO: Restante do código dos mapas...]
            st.info("🗺️ Funcionalidade de Mapas em desenvolvimento...")
            st.write("Aqui será carregado o mapa interativo completo")

# =====================================================
# Rodapé Moderno
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
