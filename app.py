import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MeasureControl, Fullscreen, Draw, MousePosition
import json
import re
import os

# =====================================================
# Configuração inicial da página
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
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_top_banner():
    st.markdown(
        """
        <img class="top-banner" src="https://i.ibb.co/v4d32PvX/banner.jpg" alt="Banner topo" />
        """,
        unsafe_allow_html=True,
    )


def show_footer_banner():
    st.markdown(
        """
        <img class="footer-banner" src="https://i.ibb.co/8nQQp8pS/barra-inferrior.png" alt="Banner rodapé" />
        """,
        unsafe_allow_html=True,
    )


def autodetect_coords(df: pd.DataFrame):
    """Retorna (lat_col, lon_col) ou None. Tenta pares comuns e coluna única 'COORDENADAS'."""
    # Pares latitude/longitude
    candidates_lat = [c for c in df.columns if re.search(r"(?:^|\b)(lat|latitude|y)(?:\b|$)", c, re.I)]
    candidates_lon = [c for c in df.columns if re.search(r"(?:^|\b)(lon|long|longitude|x)(?:\b|$)", c, re.I)]
    if candidates_lat and candidates_lon:
        return candidates_lat[0], candidates_lon[0]

    # Coluna única tipo "-5.123, -39.456"
    single = None
    for c in df.columns:
        if re.search(r"coord|coordenad", c, re.I):
            single = c
            break
    if single is not None:
        try:
            tmp = df[single].astype(str).str.extract(r"(-?\d+[\.,]?\d*)\s*[,;]\s*(-?\d+[\.,]?\d*)")
            tmp.columns = ["LATITUDE", "LONGITUDE"]
            # Converte vírgula decimal
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
            - Camadas temáticas do território: distritos, localidades e domicílios.
            - Infraestrutura essencial: escolas e unidades de saúde.
            - Recursos hídricos: tecnologias sociais e poços.
            """
        )

# =====================================================
# 2) Painel de Obras  (base: CSV em dados/milha_obras.csv)
# =====================================================
with aba2:
    st.subheader("Mapa das Obras")
    st.caption("Fonte: CSV oficial (pasta dados)")

    # Caminhos possíveis para o CSV
    CSV_OBRAS_CANDIDATES = ["dados/milha_obras.csv", "/mnt/data/milha_obras.csv"]
    CSV_OBRAS = next((p for p in CSV_OBRAS_CANDIDATES if os.path.exists(p)), CSV_OBRAS_CANDIDATES[0])

    # Helpers locais
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
                sample = f.read(4096)
                f.seek(0)
                sep = ";" if sample.count(";") > sample.count(",") else ","
                return pd.read_csv(f, sep=sep)
        except Exception as e:
            st.error(f"Falha ao ler CSV em '{path}': {e}")
            return pd.DataFrame()

    def to_float_series(s: pd.Series) -> pd.Series:
        def _conv(v):
            if pd.isna(v):
                return None
            txt = str(v)
            m = re.search(r"-?\d+[.,]?\d*", txt)
            if not m:
                return None
            try:
                return float(m.group(0).replace(",", "."))
            except Exception:
                return None
        return s.apply(_conv)

    # === Carregamento do CSV ===
    df_obras = sniff_read_csv(CSV_OBRAS)

    if not df_obras.empty:
        # 1) Detectar coordenadas
        coords = autodetect_coords(df_obras)
        if coords is None:
            # tenta pares usuais manualmente
            lat = pick(df_obras.columns, "LAT", "Latitude", "LATITUDE", "lat")
            lon = pick(df_obras.columns, "LON", "Longitude", "LONGITUDE", "lon", "long")
            if lat and lon:
                df_obras["__LAT__"] = to_float_series(df_obras[lat])
                df_obras["__LON__"] = to_float_series(df_obras[lon])
            else:
                st.error("Não foi possível identificar colunas de latitude/longitude nem 'COORDENADAS'.")
                df_map = pd.DataFrame()
        else:
            lat_col, lon_col = coords
            df_obras["__LAT__"] = to_float_series(df_obras[lat_col])
            df_obras["__LON__"] = to_float_series(df_obras[lon_col])

        # 2) Correção heurística para enquadrar Milhã-CE (lat/lon invertidos e/ou longitude positiva)
        if "__LAT__" in df_obras.columns and "__LON__" in df_obras.columns:
            # força dtype numérico para permitir operações como -lon
            lat_s = pd.to_numeric(df_obras["__LAT__"], errors="coerce")
            lon_s = pd.to_numeric(df_obras["__LON__"], errors="coerce")

            def _pct_inside(a, b):
                try:
                    # Milhã/CE ~ lat -6.5..-4.5, lon -40.5..-38.0
                    m = (a.between(-6.5, -4.5)) & (b.between(-40.5, -38.0))
                    return float(m.mean())
                except Exception:
                    return 0.0

            cands = [
                ("orig",     lat_s,            lon_s,            _pct_inside(lat_s,            lon_s)),
                ("swap",     lon_s,            lat_s,            _pct_inside(lon_s,            lat_s)),
                ("neg_lon",  lat_s,            lon_s.mul(-1.0),  _pct_inside(lat_s,            lon_s.mul(-1.0))),
                ("swap_neg", lon_s,            lat_s.mul(-1.0),  _pct_inside(lon_s,            lat_s.mul(-1.0))),
            ]
            best = max(cands, key=lambda x: x[3])
            if best[0] != "orig" and best[3] > cands[0][3]:
                df_obras["__LAT__"], df_obras["__LON__"] = best[1], best[2]

        # 3) Filtrar coordenadas válidas
        df_map = df_obras.dropna(subset=["__LAT__", "__LON__"]).copy()

        # 4) Colunas prioritárias
        cols = list(df_obras.columns)
        c_obra    = pick(cols, "Obra", "OBRA", "Nome", "NOME", "Projeto", "Descrição")
        c_status  = pick(cols, "Status", "STATUS", "Situação", "SITUACAO", "SITUAÇÃO")
        c_empresa = pick(cols, "Empresa", "EMPRESA", "Contratada", "CONTRATADA")
        c_valor   = pick(cols, "Valor", "VALOR", "Valor Total", "VALOR_TOTAL", "Custo", "CUSTO")
        c_bairro  = pick(cols, "Bairro", "BAIRRO", "Localidade", "LOCALIDADE")
        c_dtini   = pick(cols, "Início", "DATA_INICIO", "Data Início", "DATA INICIO", "Inicio")
        c_dtfim   = pick(cols, "Término", "DATA_FIM", "Data Fim", "DATA FIM", "Termino")

        st.success(f"{len(df_map)} obra(s) com coordenadas válidas. (Arquivo: {os.path.basename(CSV_OBRAS)})")

        # 5) Centro do mapa
        center = [-5.680, -39.200]
        if not df_map.empty:
            center = [df_map["__LAT__"].mean(), df_map["__LON__"].mean()]

        # 6) Mapa e controles
        m2 = folium.Map(location=center, zoom_start=12, tiles=None)
        add_base_tiles(m2)
        Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m2)
        m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
        MousePosition().add_to(m2)
        Draw(export=True).add_to(m2)

        # 7) Cor por status
        def status_icon_color(status_val: str):
            s = (status_val or "").strip().lower()
            if any(k in s for k in ["conclu", "finaliz"]):     return "green"
            if any(k in s for k in ["execu", "andamento"]):    return "orange"
            if any(k in s for k in ["paralis", "suspens"]):    return "red"
            if any(k in s for k in ["planej", "licita", "proj"]): return "blue"
            return "gray"

        # 8) Marcadores + popups
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
            ).add_to(m2)

        folium.LayerControl(collapsed=True).add_to(m2)
        folium_static(m2, width=1200, height=700)

        # 9) Tabela
        st.markdown("### Tabela de Obras")
        ordered = []
        for c in [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]:
            if c and c not in ordered:
                ordered.append(c)
        rest = [c for c in df_obras.columns if c not in ordered]
        st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)
    else:
        st.error(f"Não foi possível carregar o CSV de obras em: {CSV_OBRAS}")

# =====================================================
# 3) Milhã em Mapas
# =====================================================
with aba3:
    st.subheader("Camadas do Território, Infraestrutura e Recursos Hídricos")

    # ================================
    # Carregamento dos arquivos (pasta dados)
    # ================================
    base_dir_candidates = ["dados", "/mnt/data"]
    files = {
        # Território
        "Distritos": "milha_dist_polig.geojson",
        "Sede Distritos": "Distritos_pontos.geojson",
        "Localidades": "Localidades.geojson",
        "Domicílios Cidade": "domicilios_cidade.geojson",
        "Domicílios Rural": "domicilios_rural_mil.geojson",
        # Infraestrutura
        "Escolas": "Escolas_publicas.geojson",
        "Unidades de Saúde": "Unidades_saude.geojson",
        # Recursos Hídricos
        "Tecnologias Sociais": "teclogias_sociais.geojson",
        "Poços Cidade": "pocos_cidade_mil.geojson",
        "Poços Zona Rural": "pocos_rural_mil.geojson",
    }

    data_geo = {}
    for name, fname in files.items():
        candidates = [os.path.join(b, fname) for b in base_dir_candidates]
        data_geo[name] = load_geojson_any(candidates)

    # ================================
    # Barra lateral (hierarquia de camadas)
    # ================================
    st.sidebar.markdown("### Milhã em Mapas — Camadas")

    with st.sidebar.expander("1) Território", expanded=True):
        show_distritos = st.checkbox("Distritos", value=True)
        show_sede_distritos = st.checkbox("Sede Distritos", value=True)
        show_localidades = st.checkbox("Localidades", value=True)
        st.markdown("**Domicílios**")
        show_dom_cidade = st.checkbox("Domicílios Cidade", value=False)
        show_dom_rural = st.checkbox("Domicílios Rural", value=False)

    with st.sidebar.expander("2) Infraestrutura", expanded=False):
        show_escolas = st.checkbox("Escolas", value=False)
        show_unidades = st.checkbox("Unidades de Saúde", value=False)

    with st.sidebar.expander("3) Recursos Hídricos", expanded=False):
        show_tecnologias = st.checkbox("Tecnologias Sociais", value=False)
        st.markdown("**Poços**")
        show_pocos_cidade = st.checkbox("Poços Cidade", value=False)
        show_pocos_rural = st.checkbox("Poços Zona Rural", value=False)

    # ================================
    # Mapa
    # ================================
    m3 = folium.Map(location=[-5.680, -39.200], zoom_start=10, tiles=None)
    add_base_tiles(m3)
    Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m3)
    m3.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
    MousePosition().add_to(m3)

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
            folium.Marker(
                location=[y, x],
                tooltip=nome,
                icon=folium.Icon(color="green", icon="home")
            ).add_to(layer_sd)
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

    if show_dom_cidade and data_geo.get("Domicílios Cidade"):
        folium.GeoJson(
            data_geo["Domicílios Cidade"],
            name="Domicílios Cidade",
            style_function=lambda x: {"fillColor": "#0ea5e9", "fillOpacity": 0.3, "color": "#0369a1", "weight": 1},
        ).add_to(m3)

    if show_dom_rural and data_geo.get("Domicílios Rural"):
        folium.GeoJson(
            data_geo["Domicílios Rural"],
            name="Domicílios Rural",
            style_function=lambda x: {"fillColor": "#86efac", "fillOpacity": 0.25, "color": "#16a34a", "weight": 1},
        ).add_to(m3)

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
            popup = (
                "<div style='font-family:Arial;font-size:13px'>"
                f"<b>Local:</b> {nome}"
                "</div>"
            )
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
