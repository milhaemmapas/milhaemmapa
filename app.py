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
    "error": "#EF4444"
}

# =====================================================
# CSS Global
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
                margin-bottom: 2rem; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header-content {{ display: flex; align-items: center; gap: 2rem; max-width: 1200px; margin: 0 auto; }}
            .header-text h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: .5rem; color: white; }}
            .header-text p {{ font-size: 1.1rem; opacity: .9; margin-bottom: 0; }}
            .header-logo {{
                width: 120px; height: 120px; border-radius: 50%; border: 4px solid rgba(255,255,255,0.2);
                padding: 8px; background: rgba(255,255,255,0.1);
            }}

            .modern-card {{
                background: {COLORS["card_bg"]}; border-radius: 16px; padding: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08); border: 1px solid {COLORS["border"]};
                margin-bottom: 1.5rem; transition: transform .2s ease, box-shadow .2s ease;
            }}
            .modern-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0,0,0,0.12); }}

            .stTabs [data-baseweb="tab-list"] {{ gap: 8px; background: transparent; }}
            .stTabs [data-baseweb="tab"] {{
                background: {COLORS["card_bg"]}; border: 1px solid {COLORS["border"]};
                border-radius: 12px 12px 0 0; padding: 1rem 2rem; font-weight: 600;
                color: {COLORS["text_light"]}; transition: all .3s ease;
            }}
            .stTabs [aria-selected="true"] {{
                background: {COLORS["primary"]} !important; color: white !important; border-color: {COLORS["primary"]} !important;
            }}

            .stButton button {{
                background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
                color: white; border: none; border-radius: 10px; padding: .5rem 1.5rem; font-weight: 600;
                transition: all .3s ease;
            }}
            .stButton button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(30,58,138,.3); }}

            .sticky-panel {{
                position: sticky; top: 20px; background: {COLORS["card_bg"]};
                border: 1px solid {COLORS["border"]}; border-radius: 16px; padding: 1.5rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            }}
            .panel-title {{ color: {COLORS["primary"]}; font-size: 1.25rem; font-weight: 700; margin-bottom: .5rem; }}
            .panel-subtitle {{ color: {COLORS["text_light"]}; font-size: .9rem; margin-bottom: 1rem; border-bottom: 1px solid {COLORS["border"]}; padding-bottom: .5rem; }}

            .feature-icon {{ font-size: 2rem; margin-bottom: 1rem; color: {COLORS["primary"]}; }}
            .stat-card {{
                background: linear-gradient(135deg, {COLORS["primary"]}15, {COLORS["secondary"]}15);
                border-radius: 12px; padding: 1.5rem; text-align: center; border: 1px solid {COLORS["border"]};
            }}
            .stat-number {{ font-size: 2rem; font-weight: 700; color: {COLORS["primary"]}; margin-bottom: .5rem; }}
            .stat-label {{ color: {COLORS["text_light"]}; font-size: .9rem; }}

            @keyframes fadeIn {{ from {{ opacity:0; transform: translateY(20px); }} to {{ opacity:1; transform: translateY(0); }} }}
            .fade-in {{ animation: fadeIn .6s ease-out; }}
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
# Utilidades
# =====================================================
def autodetect_coords(df: pd.DataFrame):
    candidates_lat = [c for c in df.columns if re.search(r"(?:^|\\b)(lat|latitude|y)(?:\\b|$)", c, re.I)]
    candidates_lon = [c for c in df.columns if re.search(r"(?:^|\\b)(lon|long|longitude|x)(?:\\b|$)", c, re.I)]
    if candidates_lat and candidates_lon:
        return candidates_lat[0], candidates_lon[0]
    for c in df.columns:
        if re.search(r"coord|coordenad", c, re.I):
            try:
                tmp = df[c].astype(str).str.extract(r"(-?\\d+[\\.,]?\\d*)\\s*[,;]\\s*(-?\\d+[\\.,]?\\d*)")
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
        ("Open Street Map", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "© OpenStreetMap contributors"),
        ("CartoDB Positron", "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("CartoDB Dark", "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("Esri Satellite", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Tiles © Esri")
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
        m = re.search(r"-?\\d+[.,]?\\d*", txt)
        if not m: return None
        try: return float(m.group(0).replace(",", "."))
        except Exception: return None
    return s.apply(_conv)

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

# =====================================================
# Layout Principal
# =====================================================
css_global()
create_header()

aba1, aba2, aba3 = st.tabs(["🏠 Página Inicial", "🏗️ Painel de Obras", "🗺️ Milhã em Mapas"])

# =====================================================
# 1) Página Inicial
# =====================================================
with aba1:
    col1, col2, col3 = st.columns(3)
    for icon, num, label in [("📊","100+","Dados Geoespaciais"),("🏗️","50+","Obras Monitoradas"),("💧","30+","Recursos Hídricos")]:
        with (col1 if icon=="📊" else col2 if icon=="🏗️" else col3):
            st.markdown('<div class="stat-card fade-in">', unsafe_allow_html=True)
            st.markdown(f'<div class="feature-icon">{icon}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-number">{num}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="stat-label">{label}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
    st.markdown("## 🌟 Bem-vindo ao ATLAS Geoespacial de Milhã")
    st.markdown(
        """
        Esta plataforma integra **dados geoespaciais** do município para apoiar a tomada de decisões públicas,
        qualificar projetos urbanos e aproximar a gestão municipal dos cidadãos.

        ### 🎯 Objetivos Principais:
        - **Transparência**: Disponibilizar informações públicas de forma acessível
        - **Planejamento**: Auxiliar no planejamento urbano e territorial
        - **Monitoramento**: Acompanhar obras e projetos em tempo real
        - **Participação**: Engajar a comunidade no desenvolvimento municipal
        """
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 2) Painel de Obras (com mapa funcional)
# =====================================================
with aba2:
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("## 🏗️ Painel de Obras Municipais")
    st.markdown("Visualize e acompanhe o andamento das obras públicas em Milhã")

    CSV_OBRAS_CANDIDATES = ["dados/milha_obras.csv", "/mnt/data/milha_obras.csv"]
    CSV_OBRAS = next((p for p in CSV_OBRAS_CANDIDATES if os.path.exists(p)), CSV_OBRAS_CANDIDATES[0])
    df_obras_raw = sniff_read_csv(CSV_OBRAS)

    if df_obras_raw.empty:
        st.error("❌ Não foi possível carregar os dados das obras.")
    else:
        # Normaliza possíveis colunas relevantes
        df = df_obras_raw.copy()
        latlon = autodetect_coords(df)
        if latlon:
            lat_col, lon_col = latlon
            df["_lat"] = to_float_series(df[lat_col])
            df["_lon"] = to_float_series(df[lon_col])
            df = df.dropna(subset=["_lat","_lon"])
        else:
            st.warning("Não foram detectadas colunas de coordenadas nas obras. Exibindo somente tabela.")
            st.dataframe(df)
            st.markdown('</div>', unsafe_allow_html=True)
            # Sai da aba se não tem coordenadas
            st.stop()

        # Mapa das obras
        center = [df["_lat"].mean(), df["_lon"].mean()] if not df.empty else [-5.683, -39.187]
        m = folium.Map(location=center, zoom_start=12, control_scale=True, prefer_canvas=True)
        add_base_tiles(m)
        m.add_child(MeasureControl(primary_length_unit="meters"))
        Fullscreen().add_to(m)
        MousePosition().add_to(m)
        Draw(export=True).add_to(m)

        # Campos usuais
        col_titulo = pick(df.columns, "obra", "titulo", "nome", "Projeto", "Empreendimento")
        col_status = pick(df.columns, "status", "situacao", "situação")
        col_valor  = pick(df.columns, "valor", "valor_total", "investimento")
        col_end    = pick(df.columns, "endereco", "endereço", "local", "logradouro", "bairro")

        def status_color(s):
            s = str(s).strip().lower()
            if any(k in s for k in ["conclu", "final"]): return "green"
            if any(k in s for k in ["em and", "andamento", "execu"]): return "orange"
            if any(k in s for k in ["paral", "susp", "inter"]): return "red"
            return "blue"

        for _, r in df.iterrows():
            nome = str(r.get(col_titulo) or "Obra")
            sts  = str(r.get(col_status) or "—")
            val  = br_money(r.get(col_valor)) if col_valor else "—"
            endr = str(r.get(col_end) or "—")
            html = f"""
            <div style="font-family:Segoe UI; min-width:220px;">
                <h4 style="margin:0 0 .5rem 0; color:{COLORS['primary']};">{nome}</h4>
                <p style="margin:.25rem 0;"><b>Status:</b> {sts}</p>
                <p style="margin:.25rem 0;"><b>Valor:</b> {val}</p>
                <p style="margin:.25rem 0;"><b>Endereço:</b> {endr}</p>
            </div>
            """
            folium.CircleMarker(
                location=[r["_lat"], r["_lon"]],
                radius=6,
                color=status_color(sts),
                weight=2,
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(html, max_width=320),
                tooltip=nome
            ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        folium_static(m, height=650)

        st.success("✅ Dados carregados e mapa renderizado com sucesso!")
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# 3) Milhã em Mapas (com camadas e GeoJSON)
# =====================================================
with aba3:
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("## 🗺️ Milhã em Mapas")
    st.markdown("Explore as camadas territoriais, de infraestrutura e recursos hídricos do município")

    col_map, col_control = st.columns([3, 1])

    with col_control:
        st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">🎯 Camadas do Mapa</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel-subtitle">Selecione o que deseja visualizar</div>', unsafe_allow_html=True)

        with st.expander("🗾 Território", expanded=True):
            cb_distritos   = st.checkbox("Distritos", value=True, key="distritos")
            cb_localidades = st.checkbox("Localidades", value=True, key="localidades")

        with st.expander("🏥 Infraestrutura", expanded=True):
            cb_escolas = st.checkbox("Escolas", value=True, key="escolas")
            cb_saude   = st.checkbox("Unidades de Saúde", value=True, key="saude")

        with st.expander("💧 Recursos Hídricos", expanded=True):
            cb_pu  = st.checkbox("Poços Urbanos", value=True, key="pocos_urbanos")
            cb_pr  = st.checkbox("Poços Rurais", value=True, key="pocos_rurais")
            cb_tec = st.checkbox("Tecnologias Sociais", value=True, key="tec_sociais")

        st.markdown('</div>', unsafe_allow_html=True)

    with col_map:
        # Centro padrão aproximado de Milhã-CE
        center = [-5.683, -39.187]
        m = folium.Map(location=center, zoom_start=11, control_scale=True, prefer_canvas=True)
        add_base_tiles(m)
        Fullscreen().add_to(m)
        m.add_child(MeasureControl(primary_length_unit="meters"))
        MousePosition().add_to(m)
        Draw(export=True).add_to(m)

        # Função auxiliar para adicionar um GeoJSON (se existir)
        def add_geo_layer(layer_name: str, path_candidates, style=None, tooltip_keys=None):
            gj = load_geojson_any(path_candidates)
            if not gj:
                return None
            if style is None:
                style = lambda f: {"color": COLORS["primary"], "weight": 2, "fillOpacity": 0.05}
            g = folium.GeoJson(
                gj,
                name=layer_name,
                style_function=style,
                tooltip=folium.GeoJsonTooltip(fields=tooltip_keys) if tooltip_keys else None
            )
            g.add_to(m)
            return geojson_bounds(gj)

        # Acumula bounds para ajustar a vista
        all_bounds = []

        # SUGESTÃO DE ARQUIVOS — ajuste os nomes se necessário
        if cb_distritos:
            b = add_geo_layer(
                "Distritos",
                ["dados/distritos.geojson", "dados/milha_distritos.geojson", "/mnt/data/distritos.geojson"],
                style=lambda f: {"color": COLORS["secondary"], "weight": 2, "fillOpacity": 0.05},
                tooltip_keys=["name","nome","distrito"]
            )
            if b: all_bounds.append(b)

        if cb_localidades:
            b = add_geo_layer(
                "Localidades",
                ["dados/localidades.geojson", "/mnt/data/localidades.geojson"],
                style=lambda f: {"color": COLORS["accent"], "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["nome","name","localidade"]
            )
            if b: all_bounds.append(b)

        if cb_escolas:
            b = add_geo_layer(
                "Escolas",
                ["dados/escolas.geojson", "/mnt/data/escolas.geojson"],
                style=lambda f: {"color": "#2563EB", "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["nome","escola","name"]
            )
            if b: all_bounds.append(b)

        if cb_saude:
            b = add_geo_layer(
                "Unidades de Saúde",
                ["dados/saude.geojson", "/mnt/data/saude.geojson"],
                style=lambda f: {"color": "#16A34A", "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["unidade","nome","name"]
            )
            if b: all_bounds.append(b)

        if cb_pu:
            b = add_geo_layer(
                "Poços Urbanos",
                ["dados/pocos_urbanos.geojson", "/mnt/data/pocos_urbanos.geojson"],
                style=lambda f: {"color": "#0ea5e9", "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["nome","status","id"]
            )
            if b: all_bounds.append(b)

        if cb_pr:
            b = add_geo_layer(
                "Poços Rurais",
                ["dados/pocos_rurais.geojson", "/mnt/data/pocos_rurais.geojson"],
                style=lambda f: {"color": "#0284c7", "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["nome","status","id"]
            )
            if b: all_bounds.append(b)

        if cb_tec:
            b = add_geo_layer(
                "Tecnologias Sociais",
                ["dados/tecnologias_sociais.geojson", "/mnt/data/tecnologias_sociais.geojson"],
                style=lambda f: {"color": "#F59E0B", "weight": 1, "fillOpacity": 0.05},
                tooltip_keys=["tipo","nome","programa"]
            )
            if b: all_bounds.append(b)

        folium.LayerControl(collapsed=False).add_to(m)

        # Ajusta a vista se houver bounds
        if all_bounds:
            min_lat = min(b[0][0] for b in all_bounds)
            min_lon = min(b[0][1] for b in all_bounds)
            max_lat = max(b[1][0] for b in all_bounds)
            max_lon = max(b[1][1] for b in all_bounds)
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

        folium_static(m, height=650)

    st.markdown('</div>', unsafe_allow_html=True)

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
