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
# Configuração inicial com tema personalizado
# =====================================================
st.set_page_config(
    page_title="ATLAS • Milhã", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Paleta de cores baseada na imagem (tons de azul, verde e laranja)
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
    "error": "#EF4444"         # Vermelho erro
}

# =====================================================
# CSS Global Atualizado
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
            
            /* Header moderno */
            .main-header {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white;
                padding: 2rem 1rem;
                border-radius: 0 0 20px 20px;
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
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
                font-weight: 700;
                margin-bottom: 0.5rem;
                color: white;
            }}
            
            .header-text p {{
                font-size: 1.1rem;
                opacity: 0.9;
                margin-bottom: 0;
            }}
            
            .header-logo {{
                width: 120px;
                height: 120px;
                border-radius: 50%;
                border: 4px solid rgba(255,255,255,0.2);
                padding: 8px;
                background: rgba(255,255,255,0.1);
            }}
            
            /* Cards modernos */
            .modern-card {{
                background: {COLORS["card_bg"]};
                border-radius: 16px;
                padding: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                border: 1px solid {COLORS["border"]};
                margin-bottom: 1.5rem;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }}
            
            .modern-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            }}
            
            /* Abas estilizadas */
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
                background: transparent;
            }}
            
            .stTabs [data-baseweb="tab"] {{
                background: {COLORS["card_bg"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 12px 12px 0 0;
                padding: 1rem 2rem;
                font-weight: 600;
                color: {COLORS["text_light"]};
                transition: all 0.3s ease;
            }}
            
            .stTabs [aria-selected="true"] {{
                background: {COLORS["primary"]} !important;
                color: white !important;
                border-color: {COLORS["primary"]} !important;
            }}
            
            /* Botões modernos */
            .stButton button {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0.5rem 1.5rem;
                font-weight: 600;
                transition: all 0.3s ease;
            }}
            
            .stButton button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(30, 58, 138, 0.3);
            }}
            
            /* Painel lateral sticky */
            .sticky-panel {{
                position: sticky;
                top: 20px;
                background: {COLORS["card_bg"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 16px;
                padding: 1.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            
            .panel-title {{
                color: {COLORS["primary"]};
                font-size: 1.25rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }}
            
            .panel-subtitle {{
                color: {COLORS["text_light"]};
                font-size: 0.9rem;
                margin-bottom: 1rem;
                border-bottom: 1px solid {COLORS["border"]};
                padding-bottom: 0.5rem;
            }}
            
            /* Ícones e badges */
            .feature-icon {{
                font-size: 2rem;
                margin-bottom: 1rem;
                color: {COLORS["primary"]};
            }}
            
            .stat-card {{
                background: linear-gradient(135deg, {COLORS["primary"]}15, {COLORS["secondary"]}15);
                border-radius: 12px;
                padding: 1.5rem;
                text-align: center;
                border: 1px solid {COLORS["border"]};
            }}
            
            .stat-number {{
                font-size: 2rem;
                font-weight: 700;
                color: {COLORS["primary"]};
                margin-bottom: 0.5rem;
            }}
            
            .stat-label {{
                color: {COLORS["text_light"]};
                font-size: 0.9rem;
            }}
            
            /* Animações */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .fade-in {{
                animation: fadeIn 0.6s ease-out;
            }}
            
            /* Estilos originais preservados para os mapas */
            .top-banner, .footer-banner {{ 
                width: 100%; 
                height: auto; 
                border-radius: 8px; 
                margin-bottom: 20px; 
            }}
            
            /* Botão de toggle aprimorado */
            #toggle-lyr-obras-pulse button, #toggle-panel-pulse button {{
                 background-color: {COLORS["accent"]} !important;
                 border-color: {COLORS["accent"]} !important;
                 color: white !important;
                 font-weight: 600;
                 border-radius: 6px;
            }}
            #toggle-lyr-obras button, #toggle-panel button {{
                 background-color: #ffffff !important;
                 border-color: {COLORS["border"]} !important;
                 color: {COLORS["text_light"]} !important;
                 font-weight: 500;
                 border-radius: 6px;
            }}
            
            @keyframes pulseObras {{
                0%    {{ transform: scale(1);    box-shadow: 0 0 0 0 {COLORS["accent"]}40; }} 
                70%  {{ transform: scale(1.03); box-shadow: 0 0 0 12px {COLORS["accent"]}00; }}
                100% {{ transform: scale(1);    box-shadow: 0 0 0 0 {COLORS["accent"]}00; }}
            }}
            #toggle-lyr-obras-pulse button {{
                animation: pulseObras 1.1s ease-in-out 0s 2;
                border-color: {COLORS["accent"]} !important;
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
                <img src="https://i.ibb.co/7Nr6N5bm/brasao-milha.png" alt="Brasão de Milhã" class="header-logo">
                <div class="header-text">
                    <h1>ATLAS Geoespacial de Milhã</h1>
                    <p>Visualize dados territoriais, obras públicas e infraestrutura municipal de forma interativa</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =====================================================
# Helpers para cards (1 chamada = 1 card completo)
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

# =====================================================
# Funções utilitárias (mantidas do código original)
# =====================================================
def show_top_banner():
    st.markdown(
        '<img src="https://i.ibb.co/v4d32PvX/banner.jpg" alt="Banner topo" style="width:100%; border-radius:12px; margin-bottom:2rem;" />',
        unsafe_allow_html=True,
    )

def show_footer_banner():
    st.markdown(
        '<img src="https://i.ibb.co/8nQQp8pS/barra-inferrior.png" alt="Banner rodapé" style="width:100%; border-radius:12px; margin-top:2rem;" />',
        unsafe_allow_html=True,
    )

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
    tiles = [
        ("CartoDB Positron", "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("CartoDB Dark", "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("Esri Satellite", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Tiles © Esri"),
        ("Open Street Map", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "© OpenStreetMap contributors"),
    ]
    for name, url, attr in tiles:
        folium.TileLayer(tiles=url, name=name, attr=attr).add_to(m)

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

def pick(colnames, *options):
    cols = list(colnames)
    for o in options:
        if o in cols:
            return o
    lower = {c.lower(): c for c in cols}
    for o in options:
        if o.lower() in lower:
            return lower[o.lower()]
    return None

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
# Layout Principal
# =====================================================
css_global()
create_header()

# Abas principais
aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])

# =====================================================
# 1) Página Inicial - Atualizada (com hover animado nos KPI)
# =====================================================
with aba1:
    # CSS das animações de hover dos KPI
    st.markdown("""
    <style>
      /* cartão base */
      .stat-card{
        position: relative;
        border-radius: 16px;
        transition: transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease, border-color 160ms ease;
        will-change: transform, box-shadow;
        cursor: default;
      }
      /* brilho "sheen" ao passar o mouse */
      .stat-card::after{
        content:"";
        position:absolute;
        top:0; left:-40%;
        width:40%; height:100%;
        background: linear-gradient(120deg, rgba(255,255,255,0) 0%, rgba(255,255,255,.35) 60%, rgba(255,255,255,0) 100%);
        transform: skewX(-20deg) translateX(-120%);
        opacity:0;
        pointer-events:none;
      }
      .stat-card:hover{
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 12px 28px rgba(0,0,0,.15);
      }
      .stat-card:hover::after{
        animation: sheen 900ms ease forwards;
      }
      @keyframes sheen{
        0%   { transform: skewX(-20deg) translateX(-120%); opacity:0; }
        20%  { opacity:1; }
        100% { transform: skewX(-20deg) translateX(260%); opacity:0; }
      }

      /* ícone e número ganham vida no hover */
      .stat-card .feature-icon{
        display:flex; align-items:center; justify-content:center;
        font-size: 28px;
        transition: transform 200ms ease, text-shadow 200ms ease;
        will-change: transform;
      }
      .stat-card:hover .feature-icon{
        transform: translateY(-2px) scale(1.06) rotate(-2deg);
        text-shadow: 0 2px 10px rgba(0,0,0,.15);
      }
      .stat-card .stat-number{
        transition: transform 200ms ease, letter-spacing 200ms ease, text-shadow 200ms ease;
      }
      .stat-card:hover .stat-number{
        transform: translateY(-1px);
        letter-spacing: .4px;
        text-shadow: 0 2px 10px rgba(0,0,0,.12);
      }

      /* acessibilidade: respeita quem prefere menos movimento */
      @media (prefers-reduced-motion: reduce){
        .stat-card, .stat-card * { transition: none !important; animation: none !important; }
      }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="stat-card fade-in">
                <div class="feature-icon">📊</div>
                <div class="stat-number">100+</div>
                <div class="stat-label">Dados Geoespaciais</div>
            </div>
            """, unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div class="stat-card fade-in">
                <div class="feature-icon">🏗️</div>
                <div class="stat-number">50+</div>
                <div class="stat-label">Obras Monitoradas</div>
            </div>
            """, unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div class="stat-card fade-in">
                <div class="feature-icon">💧</div>
                <div class="stat-number">30+</div>
                <div class="stat-label">Recursos Hídricos</div>
            </div>
            """, unsafe_allow_html=True
        )

    # espaçamento entre KPI e painel de boas-vindas (mantido)
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

      
    # 👉 Painel de boas-vindas
    render_card(
        "<h2>🌟 Bem-vindo ao ATLAS Geoespacial de Milhã</h2>",
        """
        <p>
            Esta plataforma integra <strong>dados geoespaciais</strong> do município para apoiar a tomada de decisões públicas, 
            qualificar projetos urbanos e aproximar a gestão municipal dos cidadãos. 
        </p>
        <h3>🎯 Objetivos Principais:</h3>
        <ul>
            <li><strong>Transparência</strong>: Disponibilizar informações públicas de forma acessível</li>
            <li><strong>Planejamento</strong>: Auxiliar no planejamento urbano e territorial</li>
            <li><strong>Monitoramento</strong>: Acompanhar obras e projetos em tempo real</li>
            <li><strong>Participação</strong>: Engajar a comunidade no desenvolvimento municipal</li>
        </ul>
        """
    )
    
    colA, colB = st.columns(2)
    
    with colA:
        render_card(
            "<h3>🗺️ Explore o Território</h3>",
            (
                "<p>Na aba <strong>'Milhã em Mapas'</strong> você encontra:</p>"
                "<ul>"
                "<li>Divisões territoriais (Distritos e Localidades)</li>"
                "<li>Infraestrutura pública (Escolas e Unidades de Saúde)</li>"
                "<li>Recursos hídricos (Poços e Tecnologias Sociais)</li>"
                "<li>Camadas interativas e ferramentas de medição</li>"
                "</ul>"
            )
        )
    
    with colB:
        render_card(
            "<h3>🏗️ Acompanhe as Obras</h3>",
            (
                "<p>No <strong>Painel de Obras</strong> monitore:</p>"
                "<ul>"
                "<li>Status atual de cada projeto municipal</li>"
                "<li>Localização precisa no mapa</li>"
                "<li>Investimentos e prazos</li>"
                "<li>Empresas responsáveis</li>"
                "<li>Histórico de andamento</li>"
                "</ul>"
            )
        )

# =====================================================
# 2) Painel de Obras - COM MAPAS FUNCIONAIS
# =====================================================
with aba2:
    # Cabeçalho em card consolidado (um único bloco)
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

        # Camadas laterais necessárias
        base_dir_candidates = ["dados", "/mnt/data"]
        gj_distritos = load_geojson_any([os.path.join(b, "milha_dist_polig.geojson") for b in base_dir_candidates])
        gj_sede      = load_geojson_any([os.path.join(b, "Distritos_pontos.geojson") for b in base_dir_candidates])

        # Layout fixo: mapa + painel (sem botão de ocultar)
        col_map, col_panel = st.columns([5, 2], gap="large")

        # Painel lateral (checkboxes)
        with col_panel:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">🎛️ Camadas do Mapa</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-subtitle">Controle a visualização</div>', unsafe_allow_html=True)

            with st.expander("🏗️ Obras", expanded=True):
                show_obras = st.checkbox("Obras Municipais", value=True, key="obras_markers")

            with st.expander("🗾 Território", expanded=True):
                show_distritos = st.checkbox("Distritos", value=True, key="obras_distritos")
                show_sede = st.checkbox("Sede Distritos", value=True, key="obras_sede")

            st.markdown('</div>', unsafe_allow_html=True)

        # ---------- MAPA FUNCIONAL ----------
        with col_map:
            st.markdown("### 🗺️ Mapa Interativo")

            # Centralização priorizando os Distritos
            bounds = None
            if gj_distritos:
                b = geojson_bounds(gj_distritos)  # ((min_lat,min_lon),(max_lat,max_lon))
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
            add_base_tiles(m2)
            Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m2)
            m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
            MousePosition().add_to(m2)
            Draw(export=True).add_to(m2)

            # Camada Distritos
            if show_distritos and gj_distritos:
                folium.GeoJson(
                    gj_distritos,
                    name="Distritos",
                    style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.1, "color": "#000000", "weight": 1},
                ).add_to(m2)

            # Sede de Distritos
            if show_sede and gj_sede:
                lyr_sede = folium.FeatureGroup(name="Sede de Distritos")
                for f in gj_sede.get("features", []):
                    x, y = f["geometry"]["coordinates"]
                    nome = f.get("properties", {}).get("nome_do_distrito", "Sede")
                    folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(lyr_sede)
                lyr_sede.add_to(m2)

            # Obras
            if show_obras and not df_map.empty:
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

            # Ajusta a visão para os Distritos (se disponíveis); senão, ajusta às obras
            if bounds:
                (min_lat, min_lon), (max_lat, max_lon) = bounds
                m2.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            elif not df_map.empty:
                m2.fit_bounds([[df_map["__LAT__"].min(), df_map["__LON__"].min()],
                               [df_map["__LAT__"].max(), df_map["__LON__"].max()]])

            folium.LayerControl(collapsed=True).add_to(m2)
            folium_static(m2, width=1200, height=700)

        # Tabela
        st.markdown("### 📋 Tabela de Obras")
        priority = [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]
        ordered = [c for c in priority if c and c in df_obras.columns]
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)
    else:
        st.error(f"❌ Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")


# =====================================================
# 3) Milhã em Mapas — FERRAMENTAS PADRONIZADAS
# =====================================================
with aba3:
    # Import robusto (local) para capturar viewport quando possível
    try:
        from streamlit_folium import st_folium as _st_folium
        _HAS_ST_FOLIUM = True
    except Exception:
        _HAS_ST_FOLIUM = False

    render_card(
        "<h2>🗺️ Milhã em Mapas</h2>",
        "<p>Explore as camadas territoriais, de infraestrutura e recursos hídricos do município</p>",
    )

    # Painel Fixo
    show_panel = True 
    
    if "m3_view" not in st.session_state:
        st.session_state["m3_view"] = {"center": [-5.680, -39.200], "zoom": 11}
    if "m3_should_fit" not in st.session_state:
        st.session_state["m3_should_fit"] = True

    # Carregar dados GeoJSON - ATUALIZADO COM ESPELHOS D'ÁGUA
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
        "Espelhos d'Água": "espelhos_dagua.geojson",  # NOVA CAMADA ADICIONADA
    }
    data_geo = {
        name: load_geojson_any([os.path.join(b, fname) for b in base_dir_candidates])
        for name, fname in files.items()
    }

    # Layout do mapa/painel (Fixo)
    col_map, col_panel = st.columns([5, 2], gap="large")

    # Painel de camadas (Fixo) - ATUALIZADO COM ESPELHOS D'ÁGUA
    with col_panel:
        st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🎯 Camadas do Mapa</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-subtitle">Selecione o que deseja visualizar</div>', unsafe_allow_html=True)

        with st.expander("🗾 Território", expanded=True):
            show_distritos = st.checkbox("Distritos", value=True, key="lyr_distritos")
            show_sede_distritos = st.checkbox("Sede Distritos", value=True, key="lyr_sede")
            show_localidades = st.checkbox("Localidades", value=False, key="lyr_local")

        with st.expander("🏥 Infraestrutura", expanded=False):
            show_escolas = st.checkbox("Escolas", value=False, key="lyr_escolas")
            show_unidades = st.checkbox("Unidades de Saúde", value=False, key="lyr_unid")
            show_estradas = st.checkbox("Estradas", value=False, key="lyr_estradas")

        with st.expander("💧 Recursos Hídricos", expanded=False):
            show_tecnologias = st.checkbox("Tecnologias Sociais", value=False, key="lyr_tec")
            show_outorgas = st.checkbox("Outorgas Vigentes", value=False, key="lyr_outorgas")
            show_espelhos_agua = st.checkbox("Espelhos d'Água", value=False, key="lyr_espelhos")  # NOVO CHECKBOX
            st.markdown("**Poços**")
            show_pocos_cidade = st.checkbox("Poços Cidade", value=False, key="lyr_pc")
            show_pocos_rural = st.checkbox("Poços Zona Rural", value=False, key="lyr_pr")

        st.markdown('</div>', unsafe_allow_html=True)

    # =======================
    # MAPA (usando mesma abordagem da aba Obras)
    # =======================
    with col_map:
        st.markdown("### 🗺️ Mapa Interativo")

        # Usa SEMPRE o último centro/zoom salvo
        center = st.session_state["m3_view"]["center"]
        zoom   = st.session_state["m3_view"]["zoom"]

        m3 = folium.Map(
            location=center, 
            zoom_start=zoom, 
            tiles=None,
            control_scale=True
        )
        add_base_tiles(m3)
        
        # --- FERRAMENTAS DO MAPA ORGANIZADAS POR POSIÇÃO ---
        
        # LADO ESQUERDO (TOPLEFT)
        
        # 1. Fullscreen - AGORA EM 'topleft'
        Fullscreen(
            position='topleft', 
            title='Tela Cheia', 
            title_cancel='Sair', 
            force_separate_button=True
        ).add_to(m3)
        
        # LADO DIREITO (TOPRIGHT)
        
        # 2. Ferramentas de Desenho - AGORA EM 'topright'
        Draw(
            export=True,
            position='topright',
            draw_options={
                'marker': True,
                'circle': True,
                'polyline': True,
                'polygon': True,
                'rectangle': True
            }
        ).add_to(m3)
        
        # 3. Controle de Medidas - AGORA EM 'topright'
        m3.add_child(MeasureControl(
            primary_length_unit="meters", 
            secondary_length_unit="kilometers", 
            primary_area_unit="hectares",
            position='topright'
        ))
        
        # LADO INFERIOR ESQUERDO (BOTTOMLEFT)
        
        # 4. Posição do Mouse - BOTTOMLEFT (posição mantida)
        MousePosition(
            position='bottomleft',
            separator=' | ',
            empty_string='Coordenadas indisponíveis',
            lng_first=True,
            num_digits=4,
            prefix='Coordenadas:'
        ).add_to(m3)
        
        # Fit somente na primeira carga para centralizar
        if st.session_state["m3_should_fit"] and data_geo.get("Distritos"):
            b = geojson_bounds(data_geo["Distritos"])
            if b:
                (min_lat, min_lon), (max_lat, max_lon) = b
                m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            st.session_state["m3_should_fit"] = False

        # --- Camadas ---
        # Território
        if show_distritos and data_geo.get("Distritos"):
            folium.GeoJson(
                data_geo["Distritos"],
                name="Distritos",
                style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.2, "color": "#000000", "weight": 1},
                tooltip=folium.GeoJsonTooltip(fields=list(data_geo["Distritos"]["features"][0]["properties"].keys())[:3])
            ).add_to(m3)

        if show_sede_distritos and data_geo.get("Sede Distritos"):
            layer_sd = folium.FeatureGroup(name="Sede Distritos")
            for ftr in data_geo["Sede Distritos"]["features"]:
                x, y = ftr["geometry"]["coordinates"]
                nome = ftr["properties"].get("nome_do_distrito", "Sede")
                folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(layer_sd)
            layer_sd.add_to(m3)

        if show_localidades and data_geo.get("Localidades"):
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
        if show_escolas and data_geo.get("Escolas"):
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

        if show_unidades and data_geo.get("Unidades de Saúde"):
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

        # NOVA CAMADA: ESTRADAS
        if show_estradas and data_geo.get("Estradas"):
            layer_estradas = folium.FeatureGroup(name="Estradas")
            folium.GeoJson(
                data_geo["Estradas"],
                name="Estradas",
                style_function=lambda x: {
                    "color": "#8B4513",  # Cor marrom para estradas
                    "weight": 2,         # Linha mais grossa
                    "opacity": 0.8
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=list(data_geo["Estradas"]["features"][0]["properties"].keys())[:3],
                    aliases=["Propriedade:"] * 3  # Rótulos para as propriedades
                )
            ).add_to(layer_estradas)
            layer_estradas.add_to(m3)

        # Recursos Hídricos
        if show_tecnologias and data_geo.get("Tecnologias Sociais"):
            layer_tec = folium.FeatureGroup(name="Tecnologias Sociais")
            for ftr in data_geo["Tecnologias Sociais"]["features"]:
                x, y = ftr["geometry"]["coordinates"]
                props = ftr["properties"]
                nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
                popup = "<div style='font-family:Arial;font-size:13px'><b>Local:</b> {}</div>".format(nome)
                folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="orange", icon="tint")).add_to(layer_tec)
            layer_tec.add_to(m3)

        # CAMADA ATUALIZADA: OUTORGAS MILHA
        if show_outorgas and data_geo.get("Outorgas Vigentes"):
            layer_outorgas = folium.FeatureGroup(name="Outorgas Vigentes")
            for ftr in data_geo["Outorgas Vigentes"]["features"]:
                props = ftr["properties"]
                
                # Usar coordenadas geográficas diretamente do GeoJSON
                coords = ftr["geometry"]["coordinates"]
                lng, lat = coords[0], coords[1]
                
                # Criar popup simplificado conforme solicitado
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
                
                # Definir cor baseada no tipo de uso
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

        # NOVA CAMADA: ESPELHOS D'ÁGUA
        if show_espelhos_agua and data_geo.get("Espelhos d'Água"):
            layer_espelhos = folium.FeatureGroup(name="Espelhos d'Água")
            folium.GeoJson(
                data_geo["Espelhos d'Água"],
                name="Espelhos d'Água",
                style_function=lambda x: {
                    "fillColor": "#1E90FF",  # Azul para corpos d'água
                    "fillOpacity": 0.7,      # Opacidade moderada
                    "color": "#000080",      # Borda azul escuro
                    "weight": 2,             # Espessura da borda
                    "opacity": 0.8
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["CODIGOES0", "AREA1"],
                    aliases=["Código:", "Área (ha):"],
                    style=("font-family: Arial; font-size: 12px;")
                ),
                popup=folium.GeoJsonPopup(
                    fields=["CODIGOES0", "AREA1"],
                    aliases=["Código:", "Área (ha):"],
                    style=("font-family: Arial; font-size: 12px; max-width: 300px;")
                )
            ).add_to(layer_espelhos)
            layer_espelhos.add_to(m3)

        if show_pocos_cidade and data_geo.get("Poços Cidade"):
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

        if show_pocos_rural and data_geo.get("Poços Zona Rural"):
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

        # 5. LayerControl (Controle de Camadas) - AGORA EM 'topleft'
        folium.LayerControl(collapsed=True, position='topleft').add_to(m3)

        # Render preservando viewport quando possível
        if _HAS_ST_FOLIUM:
            try:
                out = _st_folium(m3, width=1200, height=700)
            except TypeError:
                out = _st_folium(m3)
            # Atualiza centro/zoom se a lib fornecer
            if isinstance(out, dict):
                last_center = out.get("last_center") or out.get("center")
                zoom_val = out.get("zoom") or out.get("last_zoom")
                if last_center and ("lat" in last_center and "lng" in last_center):
                    st.session_state["m3_view"]["center"] = [last_center["lat"], last_center["lng"]]
                if zoom_val is not None:
                    try:
                        st.session_state["m3_view"]["zoom"] = int(zoom_val)
                    except Exception:
                        pass
        else:
            # Fallback: sem captura de viewport 
            folium_static(m3, width=1200, height=700)


# =====================================================
# Rodapé
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: {COLORS["text_light"]}; padding: 2rem;'>
        <p><strong>ATLAS Geoespacial de Milhã</strong> - Desenvolvido para transparência e gestão pública eficiente</p>
        <p style='font-size: 0.9rem;'>© 2024 Prefeitura Municipal de Milhã</p>
    </div>
    """,
    unsafe_allow_html=True
)
