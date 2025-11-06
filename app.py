import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MeasureControl, Fullscreen, Draw, MousePosition
# Plugins para agrupamento (com fallback elegante)
try:
    from folium.plugins import GroupedLayerControl
    HAS_GROUPED = True
except Exception:
    HAS_GROUPED = False
try:
    from folium.plugins import FeatureGroupSubGroup
    HAS_SUBGROUP = True
except Exception:
    HAS_SUBGROUP = False

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

# Paleta de cores
COLORS = {
    "primary": "#1E3A8A",      # Azul escuro principal
    "secondary": "#059669",    # Verde esmeralda
    "accent": "#EA580C",       # Laranja vibrante
    "light_bg": "#F0F9FF",     # Azul claro de fundo
    "card_bg": "#FFFFFF",
    "text_dark": "#1E293B",
    "text_light": "#E2E8F0",
    "border": "#E2E8F0",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "sidebar_bg": "#0F172A",
    "sidebar_text": "#E2E8F0"
}

# =====================================================
# CSS Global + Estilo do botão de camadas (Leaflet)
# =====================================================
def css_global():
    st.markdown(
        f"""
        <style>
            .main {{ background-color: {COLORS["light_bg"]}; }}
            .block-container {{ padding-top: 1rem; padding-bottom: 1rem; }}

            .main-header {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white; padding: 2rem 1rem; border-radius: 0 0 20px 20px;
                margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.1); backdrop-filter: blur(10px);
            }}
            .header-content {{ display: flex; align-items: center; gap: 2rem; max-width: 1200px; margin: 0 auto; }}
            .header-text h1 {{ font-size: 2.5rem; font-weight: 800; margin-bottom: .5rem; color: white; }}
            .header-text p {{ font-size: 1.1rem; opacity: .95; margin-bottom: 0; font-weight: 400; }}
            .header-logo {{
                width: 120px; height: 120px; border-radius: 50%; border: 4px solid rgba(255,255,255,0.3);
                padding: 8px; background: rgba(255,255,255,0.15); backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }}

            .modern-card {{
                background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px);
                border-radius: 20px; padding: 2rem; box-shadow: 0 8px 32px rgba(0,0,0,0.08);
                border: 1px solid rgba(255,255,255,0.2); margin-bottom: 1.5rem; transition: all .3s;
            }}
            .modern-card:hover {{ transform: translateY(-5px); box-shadow: 0 12px 40px rgba(0,0,0,0.15); }}

            .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; border-bottom: 2px solid {COLORS["border"]}; }}
            .stTabs [data-baseweb="tab"] {{
                background: transparent; border: none; border-radius: 12px 12px 0 0; padding: 1rem 2rem;
                font-weight: 600; color: #64748B; transition: all .3s; margin: 0 4px;
            }}
            .stTabs [aria-selected="true"] {{
                background: {COLORS["primary"]} !important; color: white !important; box-shadow: 0 4px 12px rgba(30,58,138,.3);
            }}

            .css-1d391kg, .css-1lcbmhc {{ background: {COLORS["sidebar_bg"]} !important; }}
            .sidebar-content {{ padding: 2rem 1rem; }}
            .sidebar-section {{
                background: rgba(255,255,255,0.05); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;
                border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            }}
            .sidebar-title {{
                color: {COLORS['sidebar_text']}; font-size: 1.1rem; font-weight: 700; margin-bottom: 1rem; display: flex; gap: .5rem; align-items: center;
            }}
            .stCheckbox label {{ color: {COLORS['sidebar_text']} !important; font-weight: 500; }}
            .stButton button {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white; border: none; border-radius: 12px; padding: .75rem 2rem; font-weight: 600;
                transition: all .3s; box-shadow: 0 4px 12px rgba(30,58,138,.3);
            }}
            .stat-card {{
                background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7)); backdrop-filter: blur(10px);
                border-radius: 20px; padding: 2rem; text-align: center; border: 1px solid rgba(255,255,255,0.3);
                transition: all .3s; position: relative; overflow: hidden;
            }}
            .feature-icon {{ font-size: 3rem; margin-bottom: 1rem; background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}

            /* ===== Estilo forte para o botão/menu de camadas do Leaflet ===== */
            .leaflet-control-layers {
                border: 0 !important;
                box-shadow: 0 6px 18px rgba(0,0,0,.25) !important;
                border-radius: 14px !important;
                overflow: hidden;
            }
            .leaflet-control-layers-toggle {{
                background: {COLORS["primary"]} url(https://unpkg.com/leaflet@1.9.4/dist/images/layers.png) no-repeat center !important;
                border: 2px solid {COLORS["primary"]} !important;
                width: 36px !important; height: 36px !important;
                box-shadow: 0 2px 10px rgba(0,0,0,.25);
            }}
            .leaflet-control-layers-expanded {{
                background: {COLORS["primary"]} !important;
                color: {COLORS["text_light"]} !important;
                border: 2px solid {COLORS["primary"]} !important;
            }}
            .leaflet-control-layers-list label,
            .leaflet-control-layers-list span {{
                color: {COLORS["text_light"]} !important;
            }}
            .leaflet-control-layers-separator {{
                border-top: 1px solid rgba(255,255,255,.25) !important;
                margin: 8px 0 !important;
            }}
            .leaflet-control-layers-overlays > label > span,
            .leaflet-control-layers-base > label > span {{
                font-weight: 600 !important;
            }}
            /* Título dos grupos (GroupedLayerControl gera elementos <label>) */
            .leaflet-control-layers-group-label {
                color: #FFF !important;
                font-weight: 800 !important;
                margin-top: 6px;
                padding-top: 6px;
                border-top: 1px solid rgba(255,255,255,.25);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

def create_header():
    st.markdown(
        f"""
        <div class="main-header">
            <div class="header-content">
                <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã" class="header-logo">
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
# Componentes
# =====================================================
def render_card(title_html: str, body_html: str):
    st.markdown(
        f"""<div class="modern-card">{title_html}{body_html}</div>""",
        unsafe_allow_html=True,
    )

def create_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-content">
                <div style="text-align:center; margin-bottom: 2rem;">
                    <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã"
                         style="width:80px;height:80px;border-radius:50%;border:3px solid rgba(255,255,255,0.3);">
                    <h3 style="color:{COLORS['sidebar_text']}; margin-top:1rem;">Controle de Camadas</h3>
                    <p style="color:{COLORS['sidebar_text']}; opacity:.8; font-size:.9rem;">Gerencie as visualizações no mapa</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Território
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">🗾 Território</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            show_distritos = st.checkbox("Distritos", value=True, key="sidebar_distritos")
            show_sede = st.checkbox("Sede Distritos", value=True, key="sidebar_sede")
        with col2:
            show_localidades = st.checkbox("Localidades", value=False, key="sidebar_localidades")
            show_estradas = st.checkbox("Estradas", value=False, key="sidebar_estradas")
        st.markdown('</div>', unsafe_allow_html=True)

        # Infraestrutura
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">🏗️ Infraestrutura</div>', unsafe_allow_html=True)
        show_escolas = st.checkbox("Escolas Públicas", value=False, key="sidebar_escolas")
        show_unidades_saude = st.checkbox("Unidades de Saúde", value=False, key="sidebar_unidades_saude")
        show_obras = st.checkbox("Obras Municipais", value=False, key="sidebar_obras")
        st.markdown('</div>', unsafe_allow_html=True)

        # Recursos Hídricos
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markown = st.markdown
        st.markown('<div class="sidebar-title">💧 Recursos Hídricos</div>', unsafe_allow_html=True)
        col3, col4 = st.columns(2)
        with col3:
            show_tecnologias = st.checkbox("Tecnologias Sociais", value=False, key="sidebar_tecnologias")
            show_pocos_cidade = st.checkbox("Poços Cidade", value=False, key="sidebar_pocos_cidade")
        with col4:
            show_pocos_rural = st.checkbox("Poços Rural", value=False, key="sidebar_pocos_rural")
            show_espelhos = st.checkbox("Espelhos d'Água", value=False, key="sidebar_espelhos")
        show_outorgas = st.checkbox("Outorgas Vigentes", value=False, key="sidebar_outorgas")
        st.markdown('</div>', unsafe_allow_html=True)

        # Ferramentas
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⚙️ Ferramentas</div>', unsafe_allow_html=True)
        tool_col1, tool_col2 = st.columns(2)
        with tool_col1:
            enable_measure = st.checkbox("Medir", value=True, key="sidebar_measure")
            enable_draw = st.checkbox("Desenhar", value=True, key="sidebar_draw")
        with tool_col2:
            enable_fullscreen = st.checkbox("Tela Cheia", value=True, key="sidebar_fullscreen")
            show_coords = st.checkbox("Coordenadas", value=True, key="sidebar_coords")
        st.markdown('</div>', unsafe_allow_html=True)

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
# Utilidades
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

def add_base_tiles_all(m: folium.Map):
    """Adiciona TODAS as bases; a escolha fica no botão do mapa (LayerControl)."""
    bases = [
        ("CartoDB Positron", "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("CartoDB Dark", "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("Esri Satellite", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Tiles © Esri"),
        ("Open Street Map", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "© OpenStreetMap contributors"),
    ]
    for i, (name, url, attr) in enumerate(bases):
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
        txt = str(v); m = re.search(r"-?\d+[.,]?\d*", txt)
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
    if not gj: return None
    lats, lons = [], []
    def _ingest_coords(coords):
        if isinstance(coords, (list, tuple)):
            if len(coords) == 2 and all(isinstance(v, (int, float)) for v in coords):
                lon, lat = coords[0], coords[1]
                lons.append(lon); lats.append(lat)
            else:
                for c in coords: _ingest_coords(c)
    def _walk_feature(f):
        geom = f.get("geometry", {}); coords = geom.get("coordinates", [])
        _ingest_coords(coords)
    t = gj.get("type")
    if t == "FeatureCollection":
        for f in gj.get("features", []): _walk_feature(f)
    elif t == "Feature": _walk_feature(gj)
    else: _ingest_coords(gj.get("coordinates", []))
    if not lats or not lons: return None
    return (min(lats), min(lons)), (max(lats), max(lons))

# =====================================================
# Layout Principal
# =====================================================
css_global()
create_header()
sidebar_state = create_sidebar()

aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])

# =====================================================
# 1) Página Inicial
# =====================================================
with aba1:
    col1, col2, col3, col4 = st.columns(4)
    for icon, num, label in [("📊", "156", "Dados Geoespaciais"),
                             ("🏗️", "42", "Obras Monitoradas"),
                             ("💧", "67", "Recursos Hídricos"),
                             ("🏥", "23", "Unidades de Saúde")]:
        with (col1, col2, col3, col4)[["📊","🏗️","💧","🏥"].index(icon)]:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="feature-icon">{icon}</div>
                    <div style="font-size:2.5rem;font-weight:800;
                        background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["secondary"]});
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;">{num}</div>
                    <div style="color:#64748B;font-size:1rem;font-weight:600;">{label}</div>
                </div>
                """, unsafe_allow_html=True
            )
    colA, colB = st.columns(2)
    with colA:
        render_card(
            "<h2 style='background:linear-gradient(135deg,#1E3A8A,#059669);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>🌟 Bem-vindo ao ATLAS Geoespacial</h2>",
            """
            <p style='font-size:1.1rem;line-height:1.6;'>
                Esta plataforma integra <strong>dados geoespaciais</strong> do município para apoiar a tomada de decisões públicas,
                qualificar projetos urbanos e aproximar a gestão municipal dos cidadãos.
            </p>
            <div style='background:linear-gradient(135deg,rgba(30,58,138,.1),rgba(5,150,105,.1));padding:1.5rem;border-radius:12px;margin:1.5rem 0;'>
                <h4 style='color:#1E3A8A;margin-bottom:1rem;'>🎯 Objetivos Principais</h4>
                <ul style='color:#64748B;'>
                    <li><strong>Transparência</strong>: Informações públicas acessíveis</li>
                    <li><strong>Planejamento</strong>: Suporte ao desenvolvimento urbano</li>
                    <li><strong>Monitoramento</strong>: Acompanhamento contínuo</li>
                    <li><strong>Participação</strong>: Engajamento comunitário</li>
                </ul>
            </div>
            """
        )
    with colB:
        render_card(
            "<h3>🚀 Comece a Explorar</h3>",
            """
            <div style='display:grid;gap:1rem;'>
                <div style='display:flex;gap:1rem;padding:1rem;background:rgba(30,58,138,.05);border-radius:12px;'>
                    <div style='font-size:2rem;'>🗺️</div><div><strong>Milhã em Mapas</strong><br><small>Explore camadas territoriais interativas</small></div>
                </div>
                <div style='display:flex;gap:1rem;padding:1rem;background:rgba(5,150,105,.05);border-radius:12px;'>
                    <div style='font-size:2rem;'>🏗️</div><div><strong>Painel de Obras</strong><br><small>Monitore projetos municipais</small></div>
                </div>
                <div style='display:flex;gap:1rem;padding:1rem;background:rgba(234,88,12,.05);border-radius:12px;'>
                    <div style='font-size:2rem;'>💧</div><div><strong>Recursos Hídricos</strong><br><small>Poços, outorgas e espelhos d’água</small></div>
                </div>
            </div>
            """
        )

# =====================================================
# 2) Painel de Obras
# =====================================================
with aba2:
    render_card("<h2>🏗️ Painel de Obras Municipais</h2>", "<p>Visualize e acompanhe o andamento das obras públicas em Milhã</p>")
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
            if coords: lat_col, lon_col = coords
        if not lat_col or not lon_col:
            st.error("Não foi possível localizar colunas de latitude/longitude."); st.stop()

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
            st.markdown("### 📊 Informações")
            total_obras = len(df_obras)
            obras_com_coords = len(df_map)
            status_counts = df_obras[c_status].value_counts() if c_status else pd.Series()
            st.metric("Total de Obras", total_obras)
            st.metric("Com Coordenadas", obras_com_coords)
            if not status_counts.empty:
                st.markdown("**Status das Obras:**")
                for status, count in status_counts.head(5).items():
                    st.write(f"• {status}: {count}")

        with col_map:
            # Centro (bounds por distritos se houver)
            default_center = [-5.680, -39.200]
            if gj_distritos:
                b = geojson_bounds(gj_distritos)
                if b:
                    (min_lat, min_lon), (max_lat, max_lon) = b
                    default_center = [ (min_lat+max_lat)/2, (min_lon+max_lon)/2 ]

            m2 = folium.Map(location=default_center, zoom_start=12, tiles=None)
            add_base_tiles_all(m2)  # botão do mapa controla as bases

            # Ferramentas
            if sidebar_state["enable_fullscreen"]:
                Fullscreen(position='topright').add_to(m2)
            if sidebar_state["enable_measure"]:
                m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
            if sidebar_state["enable_draw"]:
                Draw(export=True).add_to(m2)
            if sidebar_state["show_coords"]:
                MousePosition().add_to(m2)

            # ===== Grupos =====
            grp_territorio = folium.FeatureGroup(name="🗾 Território", show=True).add_to(m2)
            grp_infra      = folium.FeatureGroup(name="🏗️ Infraestrutura", show=False).add_to(m2)
            grp_hidricos   = folium.FeatureGroup(name="💧 Recursos Hídricos", show=False).add_to(m2)
            grp_obras      = folium.FeatureGroup(name="📍 Obras", show=True).add_to(m2)

            # Território
            if sidebar_state["show_distritos"] and gj_distritos:
                folium.GeoJson(
                    gj_distritos,
                    name="Distritos",
                    style_function=lambda x: {"fillColor":"#9fe2fc","fillOpacity":0.1,"color":"#000000","weight":1},
                ).add_to(grp_territorio)

            if sidebar_state["show_sede"] and gj_sede:
                lyr_sede = folium.FeatureGroup(name="Sede Distritos")
                for f in gj_sede.get("features", []):
                    x, y = f["geometry"]["coordinates"]
                    nome = f.get("properties", {}).get("nome_do_distrito", "Sede")
                    folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(lyr_sede)
                lyr_sede.add_to(grp_territorio)

            # Obras
            if not df_map.empty:
                def status_icon_color(status_val: str):
                    s = (str(status_val) if status_val is not None else "").strip().lower()
                    if any(k in s for k in ["conclu", "finaliz"]): return "green"
                    if any(k in s for k in ["execu", "andamento"]): return "orange"
                    if any(k in s for k in ["paralis", "suspens"]): return "red"
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
                        if c in ignore_cols or c in {c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim}: continue
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
                lyr_obras.add_to(grp_obras)

            # Controle (agrupado se disponível)
            if HAS_GROUPED:
                GroupedLayerControl(
                    groups={
                        "🗾 Território": [grp_territorio],
                        "🏗️ Infraestrutura": [grp_infra],
                        "💧 Recursos Hídricos": [grp_hidricos],
                        "📍 Obras": [grp_obras],
                    },
                    collapsed=True
                ).add_to(m2)
            else:
                folium.LayerControl(collapsed=True).add_to(m2)

            folium_static(m2, width=800, height=600)

        # Tabela
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
with aba3:
    render_card("<h2>🗺️ Milhã em Mapas</h2>", "<p>Explore as camadas territoriais, infraestrutura e recursos hídricos do município</p>")

    if "m3_view" not in st.session_state:
        st.session_state["m3_view"] = {"center": [-5.680, -39.200], "zoom": 11}

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
    data_geo = {name: load_geojson_any([os.path.join(b, fname) for b in base_dir_candidates]) for name, fname in files.items()}

    center = st.session_state["m3_view"]["center"]
    zoom = st.session_state["m3_view"]["zoom"]

    m3 = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    add_base_tiles_all(m3)  # bases no botão do mapa

    # Ferramentas
    if sidebar_state["enable_fullscreen"]:
        Fullscreen(position='topright').add_to(m3)
    if sidebar_state["enable_measure"]:
        m3.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
    if sidebar_state["enable_draw"]:
        Draw(export=True, position='topright').add_to(m3)
    if sidebar_state["show_coords"]:
        MousePosition(position='bottomleft').add_to(m3)

    # Grupos
    grp_territorio = folium.FeatureGroup(name="🗾 Território", show=True).add_to(m3)
    grp_infra      = folium.FeatureGroup(name="🏗️ Infraestrutura", show=False).add_to(m3)
    grp_hidricos   = folium.FeatureGroup(name="💧 Recursos Hídricos", show=False).add_to(m3)

    # Bounds iniciais
    if data_geo.get("Distritos"):
        b = geojson_bounds(data_geo["Distritos"])
        if b:
            (min_lat, min_lon), (max_lat, max_lon) = b
            m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Território
    if sidebar_state["show_distritos"] and data_geo.get("Distritos"):
        folium.GeoJson(
            data_geo["Distritos"],
            name="Distritos",
            style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.2, "color": "#000000", "weight": 1},
            tooltip=folium.GeoJsonTooltip(fields=list(data_geo["Distritos"]["features"][0]["properties"].keys())[:3])
        ).add_to(grp_territorio)

    if sidebar_state["show_sede"] and data_geo.get("Sede Distritos"):
        layer_sd = folium.FeatureGroup(name="Sede Distritos")
        for ftr in data_geo["Sede Distritos"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            nome = ftr["properties"].get("nome_do_distrito", "Sede")
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(layer_sd)
        layer_sd.add_to(grp_territorio)

    if sidebar_state["show_localidades"] and data_geo.get("Localidades"):
        layer_loc = folium.FeatureGroup(name="Localidades")
        for ftr in data_geo["Localidades"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Localidade", "Localidade")
            distrito = props.get("Distrito", "-")
            popup = f"<b>Localidade:</b> {nome}<br><b>Distrito:</b> {distrito}"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="purple", icon="flag")).add_to(layer_loc)
        layer_loc.add_to(grp_territorio)

    # Infraestrutura
    if sidebar_state["show_escolas"] and data_geo.get("Escolas"):
        layer_esc = folium.FeatureGroup(name="Escolas")
        for ftr in data_geo["Escolas"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("no_entidad", props.get("Name", "Escola"))
            popup = "<div style='font-family:Arial;font-size:13px'><b>Escola:</b> {}</div>".format(nome)
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="red", icon="education")).add_to(layer_esc)
        layer_esc.add_to(grp_infra)

    if sidebar_state["show_unidades_saude"] and data_geo.get("Unidades de Saúde"):
        layer_saude = folium.FeatureGroup(name="Unidades de Saúde")
        for ftr in data_geo["Unidades de Saúde"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("nome", props.get("Name", "Unidade"))
            popup = "<div style='font-family:Arial;font-size:13px'><b>Unidade:</b> {}</div>".format(nome)
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="green", icon="plus-sign")).add_to(layer_saude)
        layer_saude.add_to(grp_infra)

    if sidebar_state["show_estradas"] and data_geo.get("Estradas"):
        layer_estradas = folium.FeatureGroup(name="Estradas")
        folium.GeoJson(
            data_geo["Estradas"],
            name="Estradas",
            style_function=lambda x: {"color": "#8B4513", "weight": 2, "opacity": 0.8},
        ).add_to(layer_estradas)
        layer_estradas.add_to(grp_infra)

    # Hídricos
    if sidebar_state["show_tecnologias"] and data_geo.get("Tecnologias Sociais"):
        layer_tec = folium.FeatureGroup(name="Tecnologias Sociais")
        for ftr in data_geo["Tecnologias Sociais"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr["properties"]
            nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
            folium.Marker([y, x], tooltip=nome, popup=f"<b>Local:</b> {nome}", icon=folium.Icon(color="orange", icon="tint")).add_to(layer_tec)
        layer_tec.add_to(grp_hidricos)

    if sidebar_state["show_outorgas"] and data_geo.get("Outorgas Vigentes"):
        layer_out = folium.FeatureGroup(name="Outorgas Vigentes")
        for ftr in data_geo["Outorgas Vigentes"]["features"]:
            props = ftr["properties"]; lng, lat = ftr["geometry"]["coordinates"]
            tipo_uso = (props.get('TIPO DE USO','') or '').upper()
            if 'IRRIGACAO' in tipo_uso: icon_color = 'green'
            elif 'ABASTECIMENTO_HUMANO' in tipo_uso: icon_color = 'blue'
            elif 'INDUSTRIA' in tipo_uso: icon_color = 'red'
            elif 'SERVICO_E_COMERCIO' in tipo_uso: icon_color = 'purple'
            else: icon_color = 'gray'
            popup = f"<div style='font-family:Arial;font-size:12px'><b>Requerente:</b> {props.get('REQUERENTE','N/A')}</div>"
            folium.Marker([lat, lng], tooltip=props.get('REQUERENTE','Outorga'),
                          popup=folium.Popup(popup, max_width=300),
                          icon=folium.Icon(color=icon_color, icon='file-text', prefix='fa')).add_to(layer_out)
        layer_out.add_to(grp_hidricos)

    if sidebar_state["show_espelhos"] and data_geo.get("Espelhos d'Água"):
        layer_espelhos = folium.FeatureGroup(name="Espelhos d'Água")
        folium.GeoJson(
            data_geo["Espelhos d'Água"],
            name="Espelhos d'Água",
            style_function=lambda x: {"fillColor": "#1E90FF","fillOpacity": 0.7,"color": "#000080","weight": 2,"opacity": 0.8}
        ).add_to(layer_espelhos)
        layer_espelhos.add_to(grp_hidricos)

    if sidebar_state["show_pocos_cidade"] and data_geo.get("Poços Cidade"):
        layer_pc = folium.FeatureGroup(name="Poços Cidade")
        for ftr in data_geo["Poços Cidade"]["features"]:
            x, y = ftr["geometry"]["coordinates"]; props = ftr["properties"]
            nome = props.get("Localidade", props.get("Name", "Poço"))
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="blue", icon="tint")).add_to(layer_pc)
        layer_pc.add_to(grp_hidricos)

    if sidebar_state["show_pocos_rural"] and data_geo.get("Poços Zona Rural"):
        layer_pr = folium.FeatureGroup(name="Poços Zona Rural")
        for ftr in data_geo["Poços Zona Rural"]["features"]:
            x, y = ftr["geometry"]["coordinates"]; props = ftr["properties"]
            nome = props.get("Localidade", props.get("Name", "Poço"))
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="cadetblue", icon="tint")).add_to(layer_pr)
        layer_pr.add_to(grp_hidricos)

    # Controle (agrupado se disponível)
    if HAS_GROUPED:
        GroupedLayerControl(
            groups={
                "🗾 Território": [grp_territorio],
                "🏗️ Infraestrutura": [grp_infra],
                "💧 Recursos Hídricos": [grp_hidricos],
            },
            collapsed=True
        ).add_to(m3)
    else:
        folium.LayerControl(collapsed=True).add_to(m3)

    folium_static(m3, width=1200, height=700)

# =====================================================
# Rodapé
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align:center; color:#64748B; padding:3rem;'>
        <div style='font-size:2rem; margin-bottom:1rem;'>
            <span style='color:{COLORS["primary"]};'>ATLAS</span>
            <span style='color:{COLORS["secondary"]};'>Geoespacial</span>
        </div>
        <p style='font-size:1.1rem; margin-bottom:1rem;'><strong>Milhã - Ceará</strong></p>
        <p style='font-size:.9rem; opacity:.7;'>Desenvolvido para transparência e gestão pública eficiente • © 2024 Prefeitura Municipal de Milhã</p>
    </div>
    """,
    unsafe_allow_html=True
)
