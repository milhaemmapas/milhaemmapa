Tenha como referencia as cores dessa imagem e melhore o layout desta página, deixando com visual mais moderno e atraente. Use sua criatividade

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
# Configuração inicial
# =====================================================
st.set_page_config(page_title="ATLAS • Milhã", layout="wide")

# =====================================================
# Utilidades
# =====================================================

def css_global():
    st.markdown(
        """
        <style>
            html, body, [data-testid="stAppViewContainer"] > .main { padding: 8px !important; }
            .block-container { padding-top: 0rem !important; }
            button[title="View fullscreen"] { display: none; }
            .top-banner { width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; }
            .footer-banner { width: 100%; height: auto; border-radius: 6px; margin-top: 16px; }
            .page-card { background: #ffffff; border: 1px solid #dbe2ea; border-radius: 10px; padding: 18px; }
            .hero { display:flex; gap:16px; align-items:center; }
            .hero img { height: 90px; }
            .hero h2 { margin: 0; font-size: 1.6rem; color: #0f172a; }

            /* Painel lateral interno da aba (gruda no topo ao rolar) */
            .sticky-panel {
                position: sticky;
                top: 8px;
                border: 1px solid #dbe2ea;
                border-radius: 10px;
                background: #fff;
                padding: 12px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            }
            .panel-title { font-weight: 700; margin-bottom: 6px; color: #0f172a; }
            .panel-subtitle { font-size: 0.9rem; color: #475569; margin-bottom: 8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

def show_top_banner():
    st.markdown(
        '<img class="top-banner" src="https://i.ibb.co/v4d32PvX/banner.jpg" alt="Banner topo" />',
        unsafe_allow_html=True,
    )

def show_footer_banner():
    st.markdown(
        '<img class="footer-banner" src="https://i.ibb.co/8nQQp8pS/barra-inferrior.png" alt="Banner rodapé" />',
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
        ("Open Street Map", "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "© OpenStreetMap contributors"),
        ("CartoDB Positron", "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("CartoDB Dark", "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", "© OpenStreetMap, © CARTO"),
        ("Esri Satellite", "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "Tiles © Esri")
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
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  # remove acentos
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)  # troca espaços/símbolos por _
    return s.strip("_")

def geojson_bounds(gj: dict):
    """
    Retorna ((min_lat, min_lon), (max_lat, max_lon)) da geometria GeoJSON.
    Funciona para FeatureCollection/Feature/Geometry.
    """
    if not gj:
        return None
    lats, lons = [], []

    def _ingest_coords(coords):
        # coords pode ter profundidades diferentes (MultiPolygon, Polygon, LineString, Point)
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
        # GeoJSON geometry pura
        _ingest_coords(gj.get("coordinates", []))

    if not lats or not lons:
        return None
    return (min(lats), min(lons)), (max(lats), max(lons))

# =====================================================
# Layout comum
# =====================================================
css_global()
show_top_banner()

# Abas
aba1, aba2, aba3 = st.tabs(["Página inicial", "Painel de Obras", "Milhã em Mapas"])

# =====================================================
# 1) Página inicial
# =====================================================
with aba1:
    st.markdown("## Bem-vindo ao ATLAS de Milhã")
    st.markdown(
        """
        Este espaço reúne dados geoespaciais para apoiar decisões públicas, qualificar projetos e aproximar a gestão das pessoas.
        O uso de mapas facilita a leitura do território, integra informações e ajuda a priorizar ações. Explore as abas para
        visualizar obras, equipamentos e recursos hídricos.
        """
    )
    colA, colB = st.columns([1,1])
    with colA:
        st.image("https://i.ibb.co/7Nr6N5bm/brasao-milha.png", caption="Município de Milhã", use_container_width=True)
    with colB:
        st.markdown(
            """
            ### O que você encontra aqui
            - Painel de obras com localização e detalhes principais.
            - Camadas do território: distritos e localidades.
            - Infraestrutura essencial: escolas e unidades de saúde.
            - Recursos hídricos: tecnologias sociais e poços.
            """
        )

# =====================================================
# 2) Painel de Obras (CSV: dados/milha_obras.csv)
# =====================================================
with aba2:
    st.subheader("Mapa das Obras")
    st.caption("Fonte: CSV oficial (pasta dados)")

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
            coords = autodetect_coords(df_obras_raw.copy())  # fallback na planilha bruta
            if coords:
                lat_col, lon_col = coords

        if not lat_col or not lon_col:
            st.error("Não foi possível localizar colunas de latitude/longitude (mesmo após normalização).")
            st.stop()

        df_obras["__LAT__"] = to_float_series(df_obras[lat_col])
        df_obras["__LON__"] = to_float_series(df_obras[lon_col])

        # Heurística para corrigir inversão e sinal
        lat_s = pd.to_numeric(df_obras["__LAT__"], errors="coerce")
        lon_s = pd.to_numeric(df_obras["__LON__"], errors="coerce")

        def _pct_inside(a, b):
            try:
                m = (a.between(-6.5, -4.5)) & (b.between(-40.5, -38.0))  # região CE
                return float(m.mean())
            except Exception:
                return 0.0

        cands = [
            ("orig",     lat_s,            lon_s,            _pct_inside(lat_s,            lon_s)),
            ("swap",     lon_s,            lat_s,            _pct_inside(lon_s,            lat_s)),
            ("neg_lon",  lat_s,            lon_s.mul(-1.0),  _pct_inside(lat_s,            lon_s.mul(-1.0))),
            ("swap_neg", lon_s,            lat_s.mul(-1.0),  _pct_inside(lon_s,            lat_s.mul(-1.0))),
        ]
        best = max(cands, key=lambda x: x[3])
        if best[0] != "orig" and best[3] >= cands[0][3]:
            df_obras["__LAT__"], df_obras["__LON__"] = best[1], best[2]

        df_map = df_obras.dropna(subset=["__LAT__", "__LON__"]).copy()

        # Campos para popup/tabela
        cols = list(df_obras.columns)
        def pick_norm(*options):
            return next((c for c in cols if c in [norm_col(o) for o in options]), None)

        c_obra    = pick_norm("Obra", "Nome", "Projeto", "Descrição")
        c_status  = pick_norm("Status", "Situação")
        c_empresa = pick_norm("Empresa", "Contratada")
        c_valor   = pick_norm("Valor", "Valor Total", "Custo")
        c_bairro  = pick_norm("Bairro", "Localidade")
        c_dtini   = pick_norm("Início", "Data Início", "Inicio")
        c_dtfim   = pick_norm("Término", "Data Fim", "Termino")

        st.success(f"{len(df_map)} obra(s) com coordenadas válidas. (Arquivo: {os.path.basename(CSV_OBRAS)})")

        # Painel lateral (Obras / Distritos / Sede)
        base_dir_candidates = ["dados", "/mnt/data"]
        gj_distritos = load_geojson_any([os.path.join(b, "milha_dist_polig.geojson") for b in base_dir_candidates])
        gj_sede      = load_geojson_any([os.path.join(b, "Distritos_pontos.geojson") for b in base_dir_candidates])

        if "show_layer_panel_obras" not in st.session_state:
            st.session_state["show_layer_panel_obras"] = True
        show_now = st.session_state["show_layer_panel_obras"]
        wrapper_id = "toggle-lyr-obras" if show_now else "toggle-lyr-obras-pulse"

        st.markdown(
            """
            <style>
            @keyframes pulseObras {
                0%   { transform: scale(1);   box-shadow: 0 0 0 0 rgba(2, 132, 199, 0.35); }
                70%  { transform: scale(1.03); box-shadow: 0 0 0 12px rgba(2, 132, 199, 0); }
                100% { transform: scale(1);   box-shadow: 0 0 0 0 rgba(2, 132, 199, 0); }
            }
            #toggle-lyr-obras-pulse button {
                animation: pulseObras 1.1s ease-in-out 0s 2;
                border-color: #0284c7 !important;
            }
            .sticky-panel { position: sticky; top: 8px; border: 1px solid #dbe2ea; border-radius: 10px; background: #fff; padding: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.05); }
            .panel-title { font-weight: 700; margin-bottom: 6px; color: #0f172a; }
            .panel-subtitle { font-size: .9rem; color: #475569; margin-bottom: 8px; }
            </style>
            """,
            unsafe_allow_html=True
        )

        col_btn, _ = st.columns([1, 6])
        with col_btn:
            st.markdown(f"<div id='{wrapper_id}'>", unsafe_allow_html=True)
            label = ("🙈 Ocultar painel de camadas"
                     if show_now else
                     "👁️ Exibir painel de camadas")
            if st.button(label, use_container_width=True, key="toggle_panel_btn_obras"):
                st.session_state["show_layer_panel_obras"] = not st.session_state["show_layer_panel_obras"]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        show_panel = st.session_state["show_layer_panel_obras"]

        # Layout: com painel ou sem painel
        if show_panel:
            col_map, col_panel = st.columns([5, 2], gap="large")
        else:
            col_map, = st.columns([1])

        # Painel lateral (checkboxes)
        if show_panel:
            with col_panel:
                st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
                st.markdown('<div class="panel-title">Camadas</div>', unsafe_allow_html=True)
                st.markdown('<div class="panel-subtitle">Ative/desative as camadas do mapa</div>', unsafe_allow_html=True)

                show_obras      = st.checkbox("Obras (marcadores)", value=True, key="obras_markers")
                show_distritos  = st.checkbox("Distritos (polígonos)", value=True, key="obras_distritos")
                show_sede       = st.checkbox("Sede de Distritos (pontos)", value=True, key="obras_sede")

                st.markdown('</div>', unsafe_allow_html=True)
        else:
            show_obras     = st.session_state.get("obras_markers", True)
            show_distritos = st.session_state.get("obras_distritos", True)
            show_sede      = st.session_state.get("obras_sede", True)

        # ---------- Mapa ----------
        with col_map:
            default_center = [-5.680, -39.200]
            default_zoom = 12

            m2 = folium.Map(location=default_center, zoom_start=default_zoom, tiles=None)
            add_base_tiles(m2)
            Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m2)
            m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
            MousePosition().add_to(m2)
            Draw(export=True).add_to(m2)

            # Centraliza pela camada Distritos se existir
            if gj_distritos:
                b = geojson_bounds(gj_distritos)
                if b:
                    (min_lat, min_lon), (max_lat, max_lon) = b
                    m2.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
            elif not df_map.empty:
                # fallback p/ pontos de obras
                m2.fit_bounds([[df_map["__LAT__"].min(), df_map["__LON__"].min()],
                               [df_map["__LAT__"].max(), df_map["__LON__"].max()]])

            def status_icon_color(status_val: str):
                s = (str(status_val) if status_val is not None else "").strip().lower()
                if any(k in s for k in ["conclu", "finaliz"]):     return "green"
                if any(k in s for k in ["execu", "andamento"]):    return "orange"
                if any(k in s for k in ["paralis", "suspens"]):    return "red"
                if any(k in s for k in ["planej", "licita", "proj"]): return "blue"
                return "gray"

            # Distritos
            if show_distritos and gj_distritos:
                folium.GeoJson(
                    gj_distritos,
                    name="Distritos",
                    style_function=lambda x: {"fillColor": "#9fe2fc", "fillOpacity": 0.2, "color": "#000000", "weight": 1},
                ).add_to(m2)

            # Sede de Distritos
            if show_sede and gj_sede:
                lyr_sede = folium.FeatureGroup(name="Sede de Distritos")
                for f in gj_sede.get("features", []):
                    x, y = f["geometry"]["coordinates"]
                    nome = f.get("properties", {}).get("Name", "Sede")
                    folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="darkgreen", icon="home")).add_to(lyr_sede)
                lyr_sede.add_to(m2)

            # Obras
            if show_obras and not df_map.empty:
                lyr_obras = folium.FeatureGroup(name="Obras")
                ignore_cols = {"__LAT__", "__LON__"}
                for _, r in df_map.iterrows():
                    nome   = str(r.get(c_obra, "Obra")) if c_obra else "Obra"
                    status = str(r.get(c_status, "-")) if c_status else "-"
                    empresa= str(r.get(c_empresa, "-")) if c_empresa else "-"
                    valor  = br_money(r.get(c_valor)) if c_valor else "-"
                    bairro = str(r.get(c_bairro, "-")) if c_bairro else "-"
                    dtini  = str(r.get(c_dtini, "-")) if c_dtini else "-"
                    dtfim  = str(r.get(c_dtfim, "-")) if c_dtfim else "-"

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

            folium.LayerControl(collapsed=True).add_to(m2)
            folium_static(m2, width=1200, height=700)

        # Tabela
        st.markdown("### Tabela de Obras")
        priority = [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]
        ordered = [c for c in priority if c and c in df_obras.columns]
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)
    else:
        st.error(f"Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")

# =====================================================
# 3) Milhã em Mapas — painel interno com botão (sem Domicílios)
# =====================================================
with aba3:
    st.subheader("Camadas do Território, Infraestrutura e Recursos Hídricos")

    # estado inicial do painel
    if "show_layer_panel" not in st.session_state:
        st.session_state["show_layer_panel"] = True

    # CSS da animação (aplicado só quando o painel estiver oculto)
    st.markdown(
        """
        <style>
        @keyframes pulse {
            0%   { transform: scale(1);   box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.35); }
            70%  { transform: scale(1.03); box-shadow: 0 0 0 12px rgba(15, 118, 110, 0); }
            100% { transform: scale(1);   box-shadow: 0 0 0 0 rgba(15, 118, 110, 0); }
        }
        #toggle-panel-pulse button {
            animation: pulse 1.1s ease-in-out 0s 2;
            border-color: #0f766e !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Botão com ícone para exibir/ocultar
    show_now = st.session_state["show_layer_panel"]
    wrapper_id = "toggle-panel" if show_now else "toggle-panel-pulse"

    col_btn, _ = st.columns([1, 6])
    with col_btn:
        st.markdown(f"<div id='{wrapper_id}'>", unsafe_allow_html=True)
        label = ("🙈 Ocultar painel de camadas"
                 if show_now else
                 "👁️ Exibir painel de camadas")
        if st.button(label, use_container_width=True, key="toggle_panel_btn"):
            st.session_state["show_layer_panel"] = not st.session_state["show_layer_panel"]
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    show_panel = st.session_state["show_layer_panel"]

    # Carregar dados GeoJSON (pasta dados ou /mnt/data)
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
    }
    data_geo = {name: load_geojson_any([os.path.join(b, fname) for b in base_dir_candidates])
                for name, fname in files.items()}

    # Layout: com painel (mapa + painel) ou sem painel (mapa full)
    if show_panel:
        col_map, col_panel = st.columns([5, 2], gap="large")
    else:
        col_map, = st.columns([1])

    # ----- Painel de camadas (só quando habilitado) -----
    if show_panel:
        with col_panel:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)
            st.markdown('<div class="panel-title">Camadas</div>', unsafe_allow_html=True)
            st.markdown('<div class="panel-subtitle">Ative/desative as camadas do mapa</div>', unsafe_allow_html=True)

            with st.expander("1) Território", expanded=True):
                show_distritos = st.checkbox("Distritos", value=True, key="lyr_distritos")
                show_sede_distritos = st.checkbox("Sede Distritos", value=True, key="lyr_sede")
                show_localidades = st.checkbox("Localidades", value=True, key="lyr_local")

            with st.expander("2) Infraestrutura", expanded=False):
                show_escolas = st.checkbox("Escolas", value=False, key="lyr_escolas")
                show_unidades = st.checkbox("Unidades de Saúde", value=False, key="lyr_unid")

            with st.expander("3) Recursos Hídricos", expanded=False):
                show_tecnologias = st.checkbox("Tecnologias Sociais", value=False, key="lyr_tec")
                st.markdown("**Poços**")
                show_pocos_cidade = st.checkbox("Poços Cidade", value=False, key="lyr_pc")
                show_pocos_rural = st.checkbox("Poços Zona Rural", value=False, key="lyr_pr")

            st.markdown('</div>', unsafe_allow_html=True)

    else:
        # painel oculto → usa valores atuais/padrão
        show_distritos      = st.session_state.get("lyr_distritos", True)
        show_sede_distritos = st.session_state.get("lyr_sede", True)
        show_localidades    = st.session_state.get("lyr_local", True)
        show_escolas        = st.session_state.get("lyr_escolas", False)
        show_unidades       = st.session_state.get("lyr_unid", False)
        show_tecnologias    = st.session_state.get("lyr_tec", False)
        show_pocos_cidade   = st.session_state.get("lyr_pc", False)
        show_pocos_rural    = st.session_state.get("lyr_pr", False)

    # ----- Mapa -----
    with col_map:
        m3 = folium.Map(location=[-5.680, -39.200], zoom_start=10, tiles=None)
        add_base_tiles(m3)
        Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m3)
        m3.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
        MousePosition().add_to(m3)

        # Centraliza por Distritos se disponível
        if data_geo.get("Distritos"):
            b = geojson_bounds(data_geo["Distritos"])
            if b:
                (min_lat, min_lon), (max_lat, max_lon) = b
                m3.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

        # 1. Território
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
                nome = ftr["properties"].get("Name", "Sede")
                folium.Marker([y, x], tooltip=nome, icon=folium.Icon(color="green", icon="home")).add_to(layer_sd)
            layer_sd.add_to(m3)

        if show_localidades and data_geo.get("Localidades"):
            layer_loc = folium.FeatureGroup(name="Localidades")
            for ftr in data_geo["Localidades"]["features"]:
                x, y = ftr["geometry"]["coordinates"]
                props = ftr["properties"]
                nome = props.get("Name", "Localidade")
                distrito = props.get("Distrito", "-")
                popup = f"<b>Localidade:</b> {nome}<br><b>Distrito:</b> {distrito}"
                folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="purple", icon="flag")).add_to(layer_loc)
            layer_loc.add_to(m3)

        # 2. Infraestrutura
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

        # 3. Recursos Hídricos
        if show_tecnologias and data_geo.get("Tecnologias Sociais"):
            layer_tec = folium.FeatureGroup(name="Tecnologias Sociais")
            for ftr in data_geo["Tecnologias Sociais"]["features"]:
                x, y = ftr["geometry"]["coordinates"]
                props = ftr["properties"]
                nome = props.get("Comunidade", props.get("Name", "Tecnologia Social"))
                popup = "<div style='font-family:Arial;font-size:13px'><b>Local:</b> {}</div>".format(nome)
                folium.Marker([y, x], tooltip=nome, popup=popup, icon=folium.Icon(color="orange", icon="tint")).add_to(layer_tec)
            layer_tec.add_to(m3)

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

        folium.LayerControl(collapsed=True).add_to(m3)
        folium_static(m3, width=1200, height=700)

# Rodapé comum
show_footer_banner()
