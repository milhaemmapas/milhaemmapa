import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import (
    MeasureControl,
    Fullscreen,
    Draw,
    MousePosition,
    MiniMap,
    MarkerCluster,
)
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
    initial_sidebar_state="expanded",  # 👉 menu lateral aberto por padrão
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
}

# =====================================================
# CSS Global Atualizado
# =====================================================
def css_global():
    st.markdown(
        f"""
        <style>
            .main {{ background-color: {COLORS["light_bg"]}; }}
            .block-container {{ padding-top: .5rem; padding-bottom: 1rem; }}

            /* Header moderno */
            .main-header {{
                background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
                color: white; padding: 1.6rem 1rem; border-radius: 0 0 20px 20px; margin-bottom: 1.2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header-content {{ display: flex; align-items: center; gap: 1.2rem; max-width: 1200px; margin: 0 auto; }}
            .header-text h1 {{ font-size: 2rem; font-weight: 800; margin: 0; color: white; }}
            .header-text p {{ font-size: 1rem; opacity: .95; margin: .2rem 0 0; }}
            .header-logo {{ width: 84px; height: 84px; border-radius: 16px; border: 3px solid rgba(255,255,255,.25); padding: 6px; background: rgba(255,255,255,.08); }}

            /* Cards */
            .modern-card {{ background: {COLORS['card_bg']}; border-radius: 16px; padding: 1.3rem; box-shadow: 0 4px 20px rgba(0,0,0,.08); border: 1px solid {COLORS['border']}; margin-bottom: 1rem; }}
            .panel-title {{ color: {COLORS['primary']}; font-weight: 800; margin-bottom: .2rem; }}
            .panel-subtitle {{ color: {COLORS['text_light']}; font-size: .9rem; margin-bottom: .6rem; border-bottom: 1px solid {COLORS['border']}; padding-bottom: .4rem; }}

            /* Abas */
            .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; }}
            .stTabs [data-baseweb="tab"] {{ background: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; border-radius: 12px 12px 0 0; padding: .7rem 1.1rem; font-weight: 700; color: {COLORS['text_light']}; }}
            .stTabs [aria-selected="true"] {{ background: {COLORS['primary']} !important; color: white !important; border-color: {COLORS['primary']} !important; }}

            /* Botões */
            .stButton button {{ background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%); color: white; border: none; border-radius: 10px; padding: .5rem 1rem; font-weight: 700; }}
            .stButton button:hover {{ filter: brightness(1.05); }}

            /* KPI */
            .stat-card{{ background: linear-gradient(135deg, {COLORS['primary']}15, {COLORS['secondary']}15); border-radius: 14px; padding: 1rem; text-align: center; border: 1px solid {COLORS['border']}; }}
            .stat-number{{ font-size: 1.6rem; font-weight: 800; color: {COLORS['primary']}; margin-bottom: .2rem; }}
            .feature-icon {{ font-size: 1.4rem; }}
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
                    <p>Dados territoriais, obras públicas e infraestrutura municipal — tudo num só lugar</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =====================================================
# Helpers
# =====================================================

def render_card(title_html: str, body_html: str):
    st.markdown(f"<div class='modern-card'>{title_html}{body_html}</div>", unsafe_allow_html=True)


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
        folium.TileLayer(tiles=url, name=name, attr=attr, control=True).add_to(m)


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
# Layout Principal
# =====================================================
css_global()
create_header()

# ---------------- Sidebar (menu lateral de camadas) ----------------
st.sidebar.markdown("## 🎛️ Menu de Camadas")
st.sidebar.caption("Ative/desative o que deseja ver no mapa. Use os presets para rapidez.")

# Presets (aplicam em ambas as abas de mapa)
if "layer_state" not in st.session_state:
    st.session_state.layer_state = {
        # Território
        "Distritos": True,
        "Sede Distritos": True,
        "Localidades": False,
        # Infra
        "Escolas": False,
        "Unidades de Saúde": False,
        "Estradas": False,
        # Hídricos
        "Tecnologias Sociais": False,
        "Outorgas Vigentes": False,
        "Espelhos d'Água": False,
        "Poços Cidade": False,
        "Poços Zona Rural": False,
        # Obras (aba 2)
        "Obras Municipais": True,
    }

col_p1, col_p2 = st.sidebar.columns(2)
if col_p1.button("Tudo"):
    for k in st.session_state.layer_state.keys():
        st.session_state.layer_state[k] = True
if col_p2.button("Limpar"):
    for k in st.session_state.layer_state.keys():
        st.session_state.layer_state[k] = False

col_p3, col_p4 = st.sidebar.columns(2)
if col_p3.button("Infraestrutura"):
    for k in ["Escolas", "Unidades de Saúde", "Estradas"]:
        st.session_state.layer_state[k] = True
if col_p4.button("Hídricos"):
    for k in ["Tecnologias Sociais", "Outorgas Vigentes", "Espelhos d'Água", "Poços Cidade", "Poços Zona Rural"]:
        st.session_state.layer_state[k] = True

st.sidebar.markdown("---")
with st.sidebar.expander("🗾 Território", True):
    st.session_state.layer_state["Distritos"] = st.checkbox("Distritos", value=st.session_state.layer_state["Distritos"]) 
    st.session_state.layer_state["Sede Distritos"] = st.checkbox("Sede Distritos", value=st.session_state.layer_state["Sede Distritos"]) 
    st.session_state.layer_state["Localidades"] = st.checkbox("Localidades", value=st.session_state.layer_state["Localidades"]) 

with st.sidebar.expander("🏥 Infraestrutura", False):
    st.session_state.layer_state["Escolas"] = st.checkbox("Escolas", value=st.session_state.layer_state["Escolas"]) 
    st.session_state.layer_state["Unidades de Saúde"] = st.checkbox("Unidades de Saúde", value=st.session_state.layer_state["Unidades de Saúde"]) 
    st.session_state.layer_state["Estradas"] = st.checkbox("Estradas", value=st.session_state.layer_state["Estradas"]) 

with st.sidebar.expander("💧 Recursos Hídricos", False):
    st.session_state.layer_state["Tecnologias Sociais"] = st.checkbox("Tecnologias Sociais", value=st.session_state.layer_state["Tecnologias Sociais"]) 
    st.session_state.layer_state["Outorgas Vigentes"] = st.checkbox("Outorgas Vigentes", value=st.session_state.layer_state["Outorgas Vigentes"]) 
    st.session_state.layer_state["Espelhos d'Água"] = st.checkbox("Espelhos d'Água", value=st.session_state.layer_state["Espelhos d'Água"]) 
    st.caption("**Poços**")
    st.session_state.layer_state["Poços Cidade"] = st.checkbox("Poços Cidade", value=st.session_state.layer_state["Poços Cidade"]) 
    st.session_state.layer_state["Poços Zona Rural"] = st.checkbox("Poços Zona Rural", value=st.session_state.layer_state["Poços Zona Rural"]) 

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧱 Obras")
st.session_state.layer_state["Obras Municipais"] = st.sidebar.checkbox("Exibir Obras Municipais (aba Painel de Obras)", value=st.session_state.layer_state["Obras Municipais"]) 

# Abas principais (mantidas)
aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])

# =====================================================
# 1) Página Inicial
# =====================================================
with aba1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
            <div class="stat-card">
                <div class="feature-icon">📊</div>
                <div class="stat-number">100+</div>
                <div class="stat-label">Dados Geoespaciais</div>
            </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class="stat-card">
                <div class="feature-icon">🏗️</div>
                <div class="stat-number">50+</div>
                <div class="stat-label">Obras Monitoradas</div>
            </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class="stat-card">
                <div class="feature-icon">💧</div>
                <div class="stat-number">30+</div>
                <div class="stat-label">Recursos Hídricos</div>
            </div>""", unsafe_allow_html=True)

    render_card(
        "<h2>🌟 Bem-vindo ao ATLAS Geoespacial de Milhã</h2>",
        """
        <p>Plataforma integrada de <strong>dados geoespaciais</strong> do município para apoiar a tomada de decisão, qualificar projetos e aproximar a gestão municipal da população.</p>
        <ul>
            <li><strong>Transparência</strong>: Acesso fácil às informações públicas</li>
            <li><strong>Planejamento</strong>: Base para o ordenamento territorial</li>
            <li><strong>Monitoramento</strong>: Acompanhamento de obras e serviços</li>
            <li><strong>Participação</strong>: Engajamento social com dados</li>
        </ul>
        """,
    )

# =====================================================
# 2) Painel de Obras — com menu lateral de camadas
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
            nopts = [norm_col(o) for o in options]
            return next((c for c in cols if c in nopts), None)

        c_obra    = pick_norm("Obra", "Nome", "Projeto", "Descrição")
        c_status  = pick_norm("Status", "Situação")
        c_empresa = pick_norm("Empresa", "Contratada")
        c_valor   = pick_norm("Valor", "Valor Total", "Custo")
        c_bairro  = pick_norm("Bairro", "Localidade")
        c_dtini   = pick_norm("Início", "Data Início", "Inicio")
        c_dtfim   = pick_norm("Término", "Data Fim", "Termino")

        st.success(f"✅ **{len(df_map)} obra(s)** com coordenadas válidas encontradas")

        # GeoJSON auxiliares
        base_dir_candidates = ["dados", "/mnt/data"]
        gj_distritos = load_geojson_any([os.path.join(b, "milha_dist_polig.geojson") for b in base_dir_candidates])
        gj_sede      = load_geojson_any([os.path.join(b, "Distritos_pontos.geojson") for b in base_dir_candidates])

        st.markdown("### 🗺️ Mapa Interativo")

        # Centro padrão/distritos
        default_center = [-5.680, -39.200]
        bounds = None
        if gj_distritos:
            b = geojson_bounds(gj_distritos)
            if b:
                bounds = b
                (min_lat, min_lon), (max_lat, max_lon) = b
                default_center = [(min_lat + max_lat)/2, (min_lon + max_lon)/2]

        m2 = folium.Map(location=default_center, zoom_start=12, tiles=None, control_scale=True)
        add_base_tiles(m2)
        MiniMap(toggle_display=True).add_to(m2)
        Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m2)
        m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
        MousePosition().add_to(m2)
        Draw(export=True).add_to(m2)

        # Distritos
        if st.session_state.layer_state["Distritos"] and gj_distritos:
            folium.GeoJson(
                gj_distritos,
                name="Distritos",
                style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.12, "color": "#000000", "weight": 1},
            ).add_to(m2)

        # Sede
        if st.session_state.layer_state["Sede Distritos"] and gj_sede:
            lyr_sd = folium.FeatureGroup(name="Sede de Distritos")
            for f in gj_sede.get("features", []):
                x, y = f["geometry"]["coordinates"]
                nome = f.get("properties", {}).get("nome_do_distrito", "Sede")
                folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(lyr_sd)
            lyr_sd.add_to(m2)

        # Obras (controladas pela sidebar)
        if st.session_state.layer_state["Obras Municipais"] and not df_map.empty:
            lyr_obras = folium.FeatureGroup(name="Obras")
            cluster = MarkerCluster().add_to(lyr_obras)

            def status_icon_color(status_val: str):
                s = (str(status_val) if status_val is not None else "").strip().lower()
                if any(k in s for k in ["conclu", "finaliz"]):     return "green"
                if any(k in s for k in ["execu", "andamento"]):    return "orange"
                if any(k in s for k in ["paralis", "suspens"]):    return "red"
                if any(k in s for k in ["planej", "licita", "proj"]): return "blue"
                return "gray"

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
                    icon=folium.Icon(color=status_icon_color(status), icon="info-sign"),
                ).add_to(cluster)

            lyr_obras.add_to(m2)

        # Ajuste de bounds
        if bounds:
            (min_lat, min_lon), (max_lat, max_lon) = bounds
            m2.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
        elif not df_map.empty:
            m2.fit_bounds([[df_map["__LAT__"].min(), df_map["__LON__"].min()], [df_map["__LAT__"].max(), df_map["__LON__"].max()]])

        folium.LayerControl(collapsed=True, position='topleft').add_to(m2)
        folium_static(m2, width=1200, height=680)

        # Tabela
        st.markdown("### 📋 Tabela de Obras")
        priority = [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]
        ordered = [c for c in priority if c and c in df_obras.columns]
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)

    else:
        st.error(f"❌ Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")


# =====================================================
# 3) Milhã em Mapas — com menu lateral de camadas
# =====================================================
with aba3:
    render_card("<h2>🗺️ Milhã em Mapas</h2>", "<p>Explore as camadas territoriais, de infraestrutura e recursos hídricos do município</p>")

    if "m3_view" not in st.session_state:
        st.session_state["m3_view"] = {"center": [-5.680, -39.200], "zoom": 11}
    if "m3_should_fit" not in st.session_state:
        st.session_state["m3_should_fit"] = True

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

    st.markdown("### 🗺️ Mapa Interativo")

    center = st.session_state["m3_view"]["center"]
    zoom   = st.session_state["m3_view"]["zoom"]

    m3 = folium.Map(location=center, zoom_start=zoom, tiles=None, control_scale=True)
    add_base_tiles(m3)
    MiniMap(toggle_display=True).add_to(m3)
    Fullscreen(position='topleft', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m3)
    Draw(export=True, position='topright', draw_options={'marker': True,'circle': True,'polyline': True,'polygon': True,'rectangle': True}).add_to(m3)
    m3.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares", position='topright'))
    MousePosition(position='bottomleft', separator=' | ', empty_string='—', lng_first=True, num_digits=4, prefix='Coord:').add_to(m3)

    # Fit inicial nos distritos
    if st.session_state["m3_should_fit"] and data_geo.get("Distritos"):
        b = geojson_bounds(data_geo["Distritos"])
        if b:
            (min_lat, min_lon), (max_lat, max_lon) = b
            m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
        st.session_state["m3_should_fit"] = False

    # ---------- Camadas (guiadas pelo menu lateral) ----------
    def add_geojson_layer(key, style_fn=None, tooltip_fields=None, popup_fields=None):
        if not st.session_state.layer_state.get(key):
            return
        gj = data_geo.get(key)
        if not gj:
            return
        layer = folium.FeatureGroup(name=key)
        folium.GeoJson(
            gj,
            name=key,
            style_function=style_fn,
            tooltip=folium.GeoJsonTooltip(fields=tooltip_fields) if tooltip_fields else None,
            popup=folium.GeoJsonPopup(fields=popup_fields) if popup_fields else None,
        ).add_to(layer)
        layer.add_to(m3)

    # Território
    add_geojson_layer(
        "Distritos",
        style_fn=lambda x: {"fillColor": "#8ecae6", "fillOpacity": 0.18, "color": "#1f2937", "weight": 1},
    )

    if st.session_state.layer_state["Sede Distritos"] and data_geo.get("Sede Distritos"):
        layer_sd = folium.FeatureGroup(name="Sede Distritos")
        for ftr in data_geo["Sede Distritos"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            nome = ftr.get("properties", {}).get("nome_do_distrito", "Sede")
            folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(layer_sd)
        layer_sd.add_to(m3)

    if st.session_state.layer_state["Localidades"] and data_geo.get("Localidades"):
        layer_loc = folium.FeatureGroup(name="Localidades")
        for ftr in data_geo["Localidades"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr.get("properties", {})
            nome = props.get("Localidade", props.get("Name", "Localidade"))
            distrito = props.get("Distrito", "-")
            popup = f"<b>Localidade:</b> {nome}<br><b>Distrito:</b> {distrito}"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="purple", icon="flag")).add_to(layer_loc)
        layer_loc.add_to(m3)

    # Infra
    if st.session_state.layer_state["Escolas"] and data_geo.get("Escolas"):
        layer_esc = folium.FeatureGroup(name="Escolas")
        for ftr in data_geo["Escolas"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr.get("properties", {})
            nome = props.get("no_entidad", props.get("Name", "Escola"))
            popup = f"<div style='font-family:Arial;font-size:13px'><b>Escola:</b> {nome}<br><b>Endereço:</b> {props.get('endereco','-')}</div>"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="red", icon="education")).add_to(layer_esc)
        layer_esc.add_to(m3)

    if st.session_state.layer_state["Unidades de Saúde"] and data_geo.get("Unidades de Saúde"):
        layer_saude = folium.FeatureGroup(name="Unidades de Saúde")
        for ftr in data_geo["Unidades de Saúde"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr.get("properties", {})
            nome = props.get("nome", props.get("Name", "Unidade"))
            popup = f"<div style='font-family:Arial;font-size:13px'><b>Unidade:</b> {nome}<br><b>Bairro:</b> {props.get('bairro','-')}<br><b>Município:</b> {props.get('municipio','-')}</div>"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="green", icon="plus-sign")).add_to(layer_saude)
        layer_saude.add_to(m3)

    if st.session_state.layer_state["Estradas"] and data_geo.get("Estradas"):
        add_geojson_layer(
            "Estradas",
            style_fn=lambda x: {"color": "#8B4513", "weight": 2, "opacity": 0.85},
            tooltip_fields=list(data_geo["Estradas"]["features"][0]["properties"].keys())[:3],
        )

    # Hídricos
    if st.session_state.layer_state["Tecnologias Sociais"] and data_geo.get("Tecnologias Sociais"):
        layer_tec = folium.FeatureGroup(name="Tecnologias Sociais")
        for ftr in data_geo["Tecnologias Sociais"]["features"]:
            x, y = ftr["geometry"]["coordinates"]
            props = ftr.get("properties", {})
            nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
            popup = f"<div style='font-family:Arial;font-size:13px'><b>Local:</b> {nome}</div>"
            folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="orange", icon="tint")).add_to(layer_tec)
        layer_tec.add_to(m3)

    if st.session_state.layer_state["Outorgas Vigentes"] and data_geo.get("Outorgas Vigentes"):
        layer_outorgas = folium.FeatureGroup(name="Outorgas Vigentes")
        for ftr in data_geo["Outorgas Vigentes"]["features"]:
            props = ftr.get("properties", {})
            lng, lat = ftr["geometry"]["coordinates"][:2]
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
            tipo_uso = (props.get('TIPO DE USO', '') or '').upper()
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
            folium.Marker([lat, lng], tooltip=props.get('REQUERENTE', 'Outorga'), popup=folium.Popup(popup_content, max_width=300), icon=folium.Icon(color=icon_color, icon='file-text', prefix='fa')).add_to(layer_outorgas)
        layer_outorgas.add_to(m3)

    if st.session_state.layer_state["Espelhos d'Água"] and data_geo.get("Espelhos d'Água"):
        add_geojson_layer(
            "Espelhos d'Água",
            style_fn=lambda x: {"fillColor": "#1E90FF", "fillOpacity": 0.6, "color": "#000080", "weight": 2, "opacity": 0.8},
            tooltip_fields=["CODIGOES0", "AREA1"],
            popup_fields=["CODIGOES0", "AREA1"],
        )

    for key in ["Poços Cidade", "Poços Zona Rural"]:
        if st.session_state.layer_state[key] and data_geo.get(key):
            lyr = folium.FeatureGroup(name=key)
            for ftr in data_geo[key]["features"]:
                x, y = ftr["geometry"]["coordinates"]
                props = ftr.get("properties", {})
                nome = props.get("Localidade", props.get("Name", "Poço"))
                popup = (
                    "<div style='font-family:Arial;font-size:13px'>"
                    f"<b>Localidade:</b> {nome}<br>"
                    f"<b>Profundidade:</b> {props.get('Profundida','-')}<br>"
                    f"<b>Vazão (L/h):</b> {props.get('Vazão_LH_2','-')}"
                    "</div>"
                )
                icon_color = "blue" if key == "Poços Cidade" else "cadetblue"
                folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color=icon_color, icon="tint")).add_to(lyr)
            lyr.add_to(m3)

    folium.LayerControl(collapsed=True, position='topleft').add_to(m3)
    folium_static(m3, width=1200, height=680)


# =====================================================
# Rodapé
# =====================================================
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: {COLORS["text_light"]}; padding: 1rem;'>
        <p><strong>ATLAS Geoespacial de Milhã</strong> — Transparência e gestão pública eficiente</p>
        <p style='font-size: .9rem;'>© 2025 Prefeitura Municipal de Milhã</p>
    </div>
    """,
    unsafe_allow_html=True,
)
