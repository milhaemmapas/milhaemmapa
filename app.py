import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from folium.plugins import MeasureControl, Fullscreen, Draw, MousePosition
import json
import re
import io
import os

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


def guess_sheet_csv_url(edit_url: str) -> str:
    """Converte URL de edição do Google Sheets para link CSV export.
    Funciona para planilhas públicas. Caso não esteja pública, exibe aviso.
    """
    try:
        # Padrão: https://docs.google.com/spreadsheets/d/<ID>/edit?gid=<gid>
        m = re.search(r"/d/([\w-]+)/", edit_url)
        gid_m = re.search(r"[?&]gid=(\d+)", edit_url)
        if not m:
            return edit_url
        file_id = m.group(1)
        gid = gid_m.group(1) if gid_m else "0"
        return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
    except Exception:
        return edit_url


def autodetect_coords(df: pd.DataFrame):
    """Retorna (lat_col, lon_col) ou None. Tenta pares comuns e coluna única 'COORDENADAS'."""
    cols = {c: c.lower() for c in df.columns}
    # Procura pares latitude/longitude
    candidates_lat = [c for c in df.columns if re.search(r"lat|latitude|y\\b", c, re.I)]
    candidates_lon = [c for c in df.columns if re.search(r"lon|long|longitude|x\\b", c, re.I)]
    # Heurística: preferir o primeiro par com mesmo prefixo ou qualquer par válido
    lat_col = None
    lon_col = None
    if candidates_lat and candidates_lon:
        lat_col = candidates_lat[0]
        lon_col = candidates_lon[0]
        return lat_col, lon_col

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


def read_public_sheet(url: str) -> pd.DataFrame:
    csv_url = guess_sheet_csv_url(url)
    try:
        return pd.read_csv(csv_url)
    except Exception:
        st.warning("Não foi possível ler a planilha pelo CSV público. Verifique se a planilha está publicada para qualquer pessoa com o link.")
        try:
            return pd.read_excel(url)
        except Exception:
            st.error("Falha ao carregar a planilha. Forneça um CSV direto ou publique a planilha.")
            return pd.DataFrame()


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
# 2) Painel de Obras
# =====================================================
with aba2:
    st.subheader("Mapa das Obras")
    st.caption("Fonte: Google Sheets informado")

    # ===== Helpers específicos do painel =====
    def br_money(x):
        try:
            v = float(str(x).replace(".", "").replace(",", ".")) if isinstance(x, str) and "," in str(x) and str(x).count(",")==1 and str(x).count(".")>1 else float(str(x).replace(",", "."))
            return f"R$ {v:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
        except Exception:
            return str(x)

    def pick(colnames, *options):
        """Seleciona a primeira coluna existente em df_obras dentre as opções."""
        for o in options:
            if o in colnames:
                return o
        # tentar case-insensitive
        lower = {c.lower(): c for c in colnames}
        for o in options:
            if o.lower() in lower:
                return lower[o.lower()]
        return None

    def status_icon_color(status_val: str):
        s = (status_val or "").strip().lower()
        if any(k in s for k in ["conclu", "finaliz"]):
            return "green"
        if any(k in s for k in ["execu", "andamento", "em andamento"]):
            return "orange"
        if any(k in s for k in ["paralis", "suspens"]):
            return "red"
        if any(k in s for k in ["planej", "licita", "projeto"]):
            return "blue"
        return "gray"

    url_planilha = st.text_input(
        "URL da planilha de Obras (Google Sheets)",
        value="https://docs.google.com/spreadsheets/d/1rZvNp7di3fcjh_lao-ryqLYgP1aYJ4M8t6ZGmrdhj8k/edit?gid=0#gid=0",
    )

    df_obras = read_public_sheet(url_planilha)
    if not df_obras.empty:
        # Detecta coordenadas
        coords = autodetect_coords(df_obras)
        if coords is None:
            st.error("Não foi possível identificar as colunas de latitude/longitude. Ajuste os cabeçalhos ou inclua uma coluna 'COORDENADAS' no formato 'lat,lon'.")
        else:
            lat_col, lon_col = coords
            # Normaliza números (vírgula para ponto) e converte
            for c in [lat_col, lon_col]:
                df_obras[c] = (
                    df_obras[c]
                    .astype(str)
                    .str.replace(",", ".", regex=False)
                )
            df_obras["__LAT__"] = pd.to_numeric(df_obras[lat_col], errors="coerce")
            df_obras["__LON__"] = pd.to_numeric(df_obras[lon_col], errors="coerce")
            df_map = df_obras.dropna(subset=["__LAT__", "__LON__"]).copy()

            # Colunas prioritárias
            cols = list(df_map.columns)
            c_obra    = pick(cols, "Obra", "OBRA", "Nome", "NOME", "Projeto", "Descrição")
            c_status  = pick(cols, "Status", "STATUS", "Situação", "SITUACAO", "SITUAÇÃO")
            c_empresa = pick(cols, "Empresa", "EMPRESA", "Contratada", "CONTRATADA")
            c_valor   = pick(cols, "Valor", "VALOR", "Valor Total", "VALOR_TOTAL", "Custo", "CUSTO")
            c_bairro  = pick(cols, "Bairro", "BAIRRO", "Localidade", "LOCALIDADE")
            c_dtini   = pick(cols, "Início", "DATA_INICIO", "Data Início", "DATA INICIO", "Inicio")
            c_dtfim   = pick(cols, "Término", "DATA_FIM", "Data Fim", "DATA FIM", "Termino")

            st.success(f"{len(df_map)} obra(s) com coordenadas válidas.")

            # Mapa centrado em Milhã-CE
            m2 = folium.Map(location=[-5.680, -39.200], zoom_start=11, tiles=None)
            add_base_tiles(m2)
            Fullscreen(position='topright', title='Tela Cheia', title_cancel='Sair', force_separate_button=True).add_to(m2)
            m2.add_child(MeasureControl(primary_length_unit="meters", secondary_length_unit="kilometers", primary_area_unit="hectares"))
            MousePosition().add_to(m2)
            Draw(export=True).add_to(m2)

            # Popups customizados
            for _, r in df_map.iterrows():
                nome   = str(r.get(c_obra, "Obra")) if c_obra else "Obra"
                status = str(r.get(c_status, "-")) if c_status else "-"
                empresa= str(r.get(c_empresa, "-")) if c_empresa else "-"
                valor  = br_money(r.get(c_valor)) if c_valor else "-"
                bairro = str(r.get(c_bairro, "-")) if c_bairro else "-"
                dtini  = str(r.get(c_dtini, "-")) if c_dtini else "-"
                dtfim  = str(r.get(c_dtfim, "-")) if c_dtfim else "-"

                extra_rows = []
                for c in df_map.columns:
                    if c in {lat_col, lon_col, "__LAT__", "__LON__", c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim}:
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

            st.markdown("### Tabela de Obras")
            # Reordena tabela com prioridades na frente, quando existirem
            ordered = []
            for c in [c_obra, c_status, c_empresa, c_valor, c_bairro, c_dtini, c_dtfim]:
                if c and c not in ordered:
                    ordered.append(c)
            rest = [c for c in df_obras.columns if c not in ordered]
            st.dataframe(df_obras[ordered + rest] if ordered else df_obras, use_container_width=True)

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
