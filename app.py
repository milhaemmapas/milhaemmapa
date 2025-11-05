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
st.set_page_config(
    page_title="ATLAS • Milhã", 
    layout="wide",
    initial_sidebar_state="expanded",
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
            /* Configurações gerais */
            .main {{
                background-color: {COLORS["light_bg"]};
            }}
            .block-container {{
                padding-top: 1rem;
                padding-bottom: 1rem;
            }}
            
            /* Header moderno com gradiente */
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
            
            /* Cards modernos com efeito glassmorphism */
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
            
            /* Abas estilizadas modernas */
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
            
            /* Sidebar moderna */
            .css-1d391kg, .css-1lcbmhc {{
                background: {COLORS["sidebar_bg"]} !important;
            }}
            
            .sidebar-content {{
                padding: 2rem 1rem;
            }}
            
            .sidebar-section {{
                background: rgba(255,255,255,0.05);
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border: 1px solid rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
            }}
            
            .sidebar-title {{
                color: {COLORS["sidebar_text"]};
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}
            
            /* Checkboxes modernos na sidebar */
            .stCheckbox label {{
                color: {COLORS["sidebar_text"]} !important;
                font-weight: 500;
            }}
            
            .stCheckbox [data-baseweb="checkbox"] {{
                background: rgba(255,255,255,0.1);
                border-color: rgba(255,255,255,0.3);
            }}
            
            .stCheckbox [data-baseweb="checkbox"]:checked {{
                background: {COLORS["accent"]};
                border-color: {COLORS["accent"]};
            }}
            
            /* Botões modernos */
            .stButton button {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 0.75rem 2rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
            }}
            
            .stButton button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(30, 58, 138, 0.4);
            }}
            
            /* KPI Cards animados */
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
            
            .stat-card:hover {{
                transform: translateY(-8px) scale(1.02);
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
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
                from {{ 
                    opacity: 0; 
                    transform: translateY(30px); 
                }}
                to {{ 
                    opacity: 1; 
                    transform: translateY(0); 
                }}
            }}
            
            .fade-in {{
                animation: fadeInUp 0.8s ease-out;
            }}
            
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            
            .floating {{
                animation: float 3s ease-in-out infinite;
            }}
            
            /* Scrollbar personalizada */
            ::-webkit-scrollbar {{
                width: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: {COLORS["light_bg"]};
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: linear-gradient(135deg, {COLORS["secondary"]}, {COLORS["primary"]});
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
    # ---------- Estado global das camadas (persistente) ----------
    if "layer_state" not in st.session_state:
        st.session_state.layer_state = {
            # Território
            "show_distritos": True,
            "show_sede": True,
            "show_localidades": False,
            "show_estradas": False,
            # Infraestrutura
            "show_escolas": False,
            "show_unidades_saude": False,
            "show_obras": False,
            # Hídricos
            "show_tecnologias": False,
            "show_pocos_cidade": False,
            "show_pocos_rural": False,
            "show_espelhos": False,
            "show_outorgas": False,
        }

    with st.sidebar:
        # ---------- Cabeçalho visual ----------
        st.markdown(
            f"""
            <div class="sidebar-content">
                <div style="text-align: center; margin-bottom: 1.5rem;">
                    <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png"
                         alt="Brasão de Milhã"
                         style="width: 80px; height: 80px; border-radius: 50%;
                                border: 3px solid rgba(255,255,255,0.3);">
                    <h3 style="color: {COLORS['sidebar_text']}; margin-top: .8rem;">Controle de Camadas</h3>
                    <p style="color: {COLORS['sidebar_text']}; opacity: .8; font-size: .9rem;">
                        Ative/desative o que deseja ver no mapa
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---------- Presets rápidos ----------
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⚡ Presets</div>', unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("Tudo"):
            for k in st.session_state.layer_state:
                st.session_state.layer_state[k] = True
        if c2.button("Limpar"):
            for k in st.session_state.layer_state:
                st.session_state.layer_state[k] = False
        if c3.button("Territ."):
            for k in ["show_distritos", "show_sede", "show_localidades"]:
                st.session_state.layer_state[k] = True
        if c4.button("Infra"):
            for k in ["show_escolas", "show_unidades_saude", "show_estradas"]:
                st.session_state.layer_state[k] = True
        if c5.button("Hídricos"):
            for k in ["show_tecnologias", "show_pocos_cidade", "show_pocos_rural", "show_espelhos", "show_outorgas"]:
                st.session_state.layer_state[k] = True
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Território ----------
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">🗾 Território</div>', unsafe_allow_html=True)
        t1, t2 = st.columns(2)
        with t1:
            st.session_state.layer_state["show_distritos"] = st.checkbox("Distritos", value=st.session_state.layer_state["show_distritos"])
            st.session_state.layer_state["show_sede"] = st.checkbox("Sede Distritos", value=st.session_state.layer_state["show_sede"])
        with t2:
            st.session_state.layer_state["show_localidades"] = st.checkbox("Localidades", value=st.session_state.layer_state["show_localidades"])
            st.session_state.layer_state["show_estradas"] = st.checkbox("Estradas", value=st.session_state.layer_state["show_estradas"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Infraestrutura ----------
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">🏗️ Infraestrutura</div>', unsafe_allow_html=True)
        st.session_state.layer_state["show_escolas"] = st.checkbox("Escolas Públicas", value=st.session_state.layer_state["show_escolas"])
        st.session_state.layer_state["show_unidades_saude"] = st.checkbox("Unidades de Saúde", value=st.session_state.layer_state["show_unidades_saude"])
        st.session_state.layer_state["show_obras"] = st.checkbox("Obras Municipais", value=st.session_state.layer_state["show_obras"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Recursos Hídricos ----------
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">💧 Recursos Hídricos</div>', unsafe_allow_html=True)
        h1, h2 = st.columns(2)
        with h1:
            st.session_state.layer_state["show_tecnologias"] = st.checkbox("Tecnologias Sociais", value=st.session_state.layer_state["show_tecnologias"])
            st.session_state.layer_state["show_pocos_cidade"] = st.checkbox("Poços Cidade", value=st.session_state.layer_state["show_pocos_cidade"])
        with h2:
            st.session_state.layer_state["show_pocos_rural"] = st.checkbox("Poços Rural", value=st.session_state.layer_state["show_pocos_rural"])
            st.session_state.layer_state["show_espelhos"] = st.checkbox("Espelhos d'Água", value=st.session_state.layer_state["show_espelhos"])
        st.session_state.layer_state["show_outorgas"] = st.checkbox("Outorgas Vigentes", value=st.session_state.layer_state["show_outorgas"])
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Ferramentas ----------
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⚙️ Ferramentas</div>', unsafe_allow_html=True)
        tool1, tool2 = st.columns(2)
        with tool1:
            enable_measure = st.checkbox("Medir", value=True, key="sidebar_measure")
            enable_draw = st.checkbox("Desenhar", value=True, key="sidebar_draw")
        with tool2:
            enable_fullscreen = st.checkbox("Tela Cheia", value=True, key="sidebar_fullscreen")
            show_coords = st.checkbox("Coordenadas", value=True, key="sidebar_coords")
        st.markdown('</div>', unsafe_allow_html=True)

        # ---------- Estatísticas ----------
        ativos = sum(1 for v in st.session_state.layer_state.values() if isinstance(v, bool) and v)
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📊 Estatísticas</div>', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            st.metric("Camadas Ativas", f"{ativos}")
        with s2:
            st.metric("Dados Carregados", "—")
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Retorno compatível com o restante do app ----------
    ls = st.session_state.layer_state
    return {
        "show_distritos": ls["show_distritos"],
        "show_sede": ls["show_sede"],
        "show_localidades": ls["show_localidades"],
        "show_estradas": ls["show_estradas"],
        "show_escolas": ls["show_escolas"],
        "show_unidades_saude": ls["show_unidades_saude"],
        "show_obras": ls["show_obras"],
        "show_tecnologias": ls["show_tecnologias"],
        "show_pocos_cidade": ls["show_pocos_cidade"],
        "show_pocos_rural": ls["show_pocos_rural"],
        "show_espelhos": ls["show_espelhos"],
        "show_outorgas": ls["show_outorgas"],
        "enable_measure": enable_measure,
        "enable_draw": enable_draw,
        "enable_fullscreen": enable_fullscreen,
        "show_coords": show_coords,
    }

# =====================================================
# Funções utilitárias (mantidas do código original)
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

def add_base_tiles(m: folium.Map):
    """
    Adiciona TODAS as camadas de mapa base; a escolha fica no LayerControl do mapa.
    """
    tiles = [
        ("CartoDB Positron", "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("CartoDB Dark", "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("Esri Satellite", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Tiles © Esri"),
        ("Open Street Map", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "© OpenStreetMap contributors"),
    ]
    # primeira camada como default (add_to Map), demais com control
    for i, (name, url, attr) in enumerate(tiles):
        folium.TileLayer(tiles=url, name=name, attr=attr, control=True, show=(i == 0)).add_to(m)

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

# =====================================================
# Layout Principal Atualizado
# =====================================================
css_global()
create_header()

# Criar sidebar e obter estados
sidebar_state = create_sidebar()

# Abas principais
aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])

# =====================================================
# 1) Página Inicial - Totalmente Modernizada
# =====================================================
with aba1:
    # KPIs com design moderno
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

    # Conteúdo principal
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
# 2) Painel de Obras - Integrado com Sidebar
# =====================================================
with aba2:
    render_card(
        "<h2>🏗️ Painel de Obras Municipais</h2>",
        "<p>Visualize e acompanhe o andamento das obras públicas em Milhã</p>",
    )

    CSV_OBRAS_CANDIDATES = ["dados/milha_obras.csv", "/mnt/data/milha_obras.csv"]
    CSV_OBRAS = next((p for p in CSV_OBRAS_CANDIDATES if os.path.exists(p)), CSV_OBRAS_CANDIDATES[0])

    df_obras_raw = sniff_read_csv(CSV_OBRAS)

    if not df_obras_raw.empty:
        # Normaliza colunas
        colmap = {c: norm_col(c) for c in df_obras_raw.columns}
        df_obras = df_obras_raw.rename(columns=colmap).copy()

        # Detecta lat/lon
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

        # Heurística para corrigir inversão e sinal
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

        # Campos para popup/tabela
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

        # Carregar dados GeoJSON
        base_dir_candidates = ["dados", "/mnt/data"]
        gj_distritos = load_geojson_any([os.path.join(b, "milha_dist_polig.geojson") for b in base_dir_candidates])
        gj_sede      = load_geojson_any([os.path.join(b, "Distritos_pontos.geojson") for b in base_dir_candidates])

        # Layout do mapa
        col_map, col_info = st.columns([3, 1])

        with col_info:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">📊 Informações</div>', unsafe_allow_html=True)
            
            # Estatísticas rápidas
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
            # Centralização
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

            m2 = folium.Map(location=default_center, zoom_start=12, tiles=None)
            add_base_tiles(m2)  # todas as bases; controle no mapa
            
            # Ferramentas do mapa baseadas na sidebar
            if sidebar_state["enable_fullscreen"]:
                Fullscreen(position='topright').add_to(m2)
            if sidebar_state["enable_measure"]:
                m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
            if sidebar_state["enable_draw"]:
                Draw(export=True).add_to(m2)
            if sidebar_state["show_coords"]:
                MousePosition().add_to(m2)

            # Camadas baseadas na sidebar
            if sidebar_state["show_distritos"] and gj_distritos:
                folium.GeoJson(
                    gj_distritos,
                    name="Distritos",
                    style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.1, "color": "#000000", "weight": 1},
                ).add_to(m2)

            if sidebar_state["show_sede"] and gj_sede:
                lyr_sede = folium.FeatureGroup(name="Sede Distritos")
                for f in gj_sede.get("features", []):
                    x, y = f["geometry"]["coordinates"]
                    nome = f.get("properties", {}).get("nome_do_distrito", "Sede")
                    folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(lyr_sede)
                lyr_sede.add_to(m2)

            # Obras (sempre visíveis nesta aba)
            if not df_map.empty:
                def status_icon_color(status_val: str):
                    s = (str(status_val) if status_val is not None else "").strip().lower()
                    if any(k in s for k in ["conclu", "finaliz"]):     return "green"
                    if any(k in s for k in ["execu", "andamento"]):    return "orange"
                    if any(k in s for k in ["paralis", "suspens"]):    return "red"
                    if any(k in s for k in ["planej", "licita", "proj"]): return "blue"
                    return "gray"

                lyr_obras = folium.FeatureGroup(name="Obras")
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
                    ).add_to(lyr_obras)

                lyr_obras.add_to(m2)

            # Ajustar visão do mapa
            if bounds:
                (min_lat, min_lon), (max_lat, max_lon) = bounds
                m2.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            elif not df_map.empty:
                m2.fit_bounds([[df_map["__LAT__"].min(), df_map["__LON__"].min()],
                               [df_map["__LAT__"].max(), df_map["__LON__"].max()]])

            folium.LayerControl(collapsed=True, position="topleft").add_to(m2)
            folium_static(m2, width=800, height=600)

        # Tabela de obras
        st.markdown("### 📋 Tabela de Obras")
        priority = [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]
        ordered = [c for c in priority if c and c in df_obras.columns]
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)
    else:
        st.error(f"❌ Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")

# =====================================================
# 3) Milhã em Mapas - Totalmente Integrado com Sidebar
# =====================================================
with aba3:
    render_card(
        "<h2>🗺️ Milhã em Mapas</h2>",
        "<p>Explore as camadas territoriais, infraestrutura e recursos hídricos do município</p>",
    )

    if "m3_view" not in st.session_state:
        st.session_state["m3_view"] = {"center": [-5.680, -39.200], "zoom": 11}

    # Carregar dados GeoJSON
    base_dir_candidates = ["dados", "/mnt/data"]
    files = {
        "Distritos": "milha_dist_polig.geojson",
        "Sede Distritos": "Distritos_pontos.geojson",
        "Localidades": "Localidades.geojson",
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

    # Criar mapa integrado com sidebar
    center = st.session_state["m3_view"]["center"]
    zoom = st.session_state["m3_view"]["zoom"]

    m3 = folium.Map(
        location=center, 
        zoom_start=zoom, 
        tiles=None,
        control_scale=True
    )
    
    # Adicionar TODAS as camadas base (controle no mapa)
    add_base_tiles(m3)
    
    # Adicionar ferramentas baseadas na sidebar
    if sidebar_state["enable_fullscreen"]:
        Fullscreen(position='topright').add_to(m3)
    
    if sidebar_state["enable_measure"]:
        m3.add_child(MeasureControl(
            primary_length_unit="meters", 
            secondary_length_unit="kilometers", 
            primary_area_unit="hectares"
        ))
    
    if sidebar_state["enable_draw"]:
        Draw(export=True, position='topright').add_to(m3)
    
    if sidebar_state["show_coords"]:
        MousePosition(position='bottomleft').add_to(m3)

    # Ajustar visão inicial
    if data_geo.get("Distritos"):
        b = geojson_bounds(data_geo["Distritos"])
        if b:
            (min_lat, min_lon), (max_lat, max_lon) = b
            m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Adicionar camadas baseadas na sidebar
    # Território
    if sidebar_state["show_distritos"] and data_geo.get("Distritos"):
        folium.GeoJson(
            data_geo["Distritos"],
            name="Distritos",
            style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.2, "color": "#000000", "weight": 1},
            tooltip=folium.GeoJsonTooltip(fields=list(data_geo["Distritos"]["features"][0]["properties"].keys())[:3])
        ).add_to(m3)

    if sidebar_state["show_sede"] and data_geo.get("Sede Distritos"):
        layer_sd = folium.FeatureGroup(name="Sede Distritos")
        for ftr in data_geo["Sede Distritos"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            nome = ftr["properties"].get("nome_do_distrito", "Sede")
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(layer_sd)
        layer_sd.add_to(m3)

    if sidebar_state["show_localidades"] and data_geo.get("Localidades"):
        layer_loc = folium.FeatureGroup(name="Localidades")
        for ftr in data_geo["Localidades"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Localidade", "Localidade")
            distrito = props.get("Distrito", "-")
            popup = f"<b>Localidade:</b> {nome}<br><b>Distrito:</b> {distrito}"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="purple", icon="flag")).add_to(layer_loc)
        layer_loc.add_to(m3)

    # Infraestrutura
    if sidebar_state["show_escolas"] and data_geo.get("Escolas"):
        layer_esc = folium.FeatureGroup(name="Escolas")
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
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="red", icon="education")).add_to(layer_esc)
        layer_esc.add_to(m3)

    if sidebar_state["show_unidades_saude"] and data_geo.get("Unidades de Saúde"):
        layer_saude = folium.FeatureGroup(name="Unidades de Saúde")
        for ftr in data_geo["Unidades de Saúde"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("nome", props.get("Name", "Unidade"))
            popup = (
                "<div style='font-family:Arial;font-size:13px'>"
                f"<b>Unidade:</b> {nome}<br>"
                f"<b>Bairro:</b> {props.get('bairro','-')}<br>"
                f"<b>Município:</b> {props.get('municipio','-')}"
                "</div>"
            )
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="green", icon="plus-sign")).add_to(layer_saude)
        layer_saude.add_to(m3)

    if sidebar_state["show_estradas"] and data_geo.get("Estradas"):
        layer_estradas = folium.FeatureGroup(name="Estradas")
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
        ).add_to(layer_estradas)
        layer_estradas.add_to(m3)

    # Recursos Hídricos
    if sidebar_state["show_tecnologias"] and data_geo.get("Tecnologias Sociais"):
        layer_tec = folium.FeatureGroup(name="Tecnologias Sociais")
        for ftr in data_geo["Tecnologias Sociais"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
            popup = "<div style='font-family:Arial;font-size:13px'><b>Local:</b> {}</div>".format(nome)
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="orange", icon="tint")).add_to(layer_tec)
        layer_tec.add_to(m3)

    if sidebar_state["show_outorgas"] and data_geo.get("Outorgas Vigentes"):
        layer_outorgas = folium.FeatureGroup(name="Outorgas Vigentes")
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
            ).add_to(layer_outorgas)
        layer_outorgas.add_to(m3)

    if sidebar_state["show_espelhos"] and data_geo.get("Espelhos d'Água"):
        layer_espelhos = folium.FeatureGroup(name="Espelhos d'Água")
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
        ).add_to(layer_espelhos)
        layer_espelhos.add_to(m3)

    if sidebar_state["show_pocos_cidade"] and data_geo.get("Poços Cidade"):
        layer_pc = folium.FeatureGroup(name="Poços Cidade")
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
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="blue", icon="tint")).add_to(layer_pc)
        layer_pc.add_to(m3)

    if sidebar_state["show_pocos_rural"] and data_geo.get("Poços Zona Rural"):
        layer_pr = folium.FeatureGroup(name="Poços Zona Rural")
        for ftr in data_geo["Poços Zona Rural"]["features"]:
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
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="cadetblue", icon="tint")).add_to(layer_pr)
        layer_pr.add_to(m3)

    # Controle de camadas (inclui mapas base)
    folium.LayerControl(collapsed=True, position="topleft").add_to(m3)

    # Renderizar mapa
    folium_static(m3, width=1200, height=700)

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
