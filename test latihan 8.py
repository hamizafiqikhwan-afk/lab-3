import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import folium
from streamlit_folium import st_folium
import json
import ezdxf
import io
from pyproj import Transformer

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Maklumat Geografi (GIS)", 
    page_icon="🗺️",
    layout="wide"
)

# --- REKA BENTUK TEMA & CSS TERSUAI ---
st.markdown("""
    <style>
    /* Styling Kad Metrik */
    .metric-container {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .metric-title {
        color: #6c757d;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #1f2937;
        font-size: 1.8rem;
        font-weight: 700;
    }
    
    /* Cantikkan Kotak Pembuka (Expander) */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #2b2b2b;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNGSI MATEMATIK & GEOMETRI ---
def calculate_polygon_area(x, y):
    x = np.array(x)
    y = np.array(y)
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))

def calculate_bearing_distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    distance = np.hypot(dx, dy)
    
    angle_rad = np.arctan2(dx, dy)
    angle_deg = np.degrees(angle_rad) % 360
    
    d = int(angle_deg)
    m = int((angle_deg - d) * 60)
    s = round(((angle_deg - d) * 60 - m) * 60)
    
    bearing_str = f"{d}°{m:02d}'{s:02d}\""
    return bearing_str, distance

# --- FUNGSI UNJURAN KOORDINAT ---
def reproject_coordinates(e_list, n_list, epsg_code, swap_axes=False):
    if str(epsg_code) == "4326":
        if swap_axes:
            return list(zip(e_list, n_list))
        return list(zip(n_list, e_list))
    
    if swap_axes:
        x_in, y_in = n_list, e_list
    else:
        x_in, y_in = e_list, n_list

    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
    
    latlon_coords = []
    for x, y in zip(x_in, y_in):
        lon, lat = transformer.transform(x, y)
        latlon_coords.append((lat, lon))
        
    return latlon_coords

# --- FUNGSI EKSPORT ---
def generate_geojson(df, latlon_coords):
    features = []
    coords = [[float(lon), float(lat)] for lat, lon in latlon_coords]
    coords.append(coords[0])
    
    polygon_feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        },
        "properties": {"name": "Sempadan Poligon"}
    }
    features.append(polygon_feature)
    
    for idx, (lat, lon) in enumerate(latlon_coords):
        stn_val = int(df['STN'].iloc[idx]) if 'STN' in df.columns else int(idx + 1)
        point_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            },
            "properties": {"STN": stn_val}
        }
        features.append(point_feature)
        
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    return json.dumps(geojson_data, indent=4)

def generate_dxf(df):
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    doc.layers.add(name="POLYGON", color=1)
    doc.layers.add(name="POINTS", color=3)
    doc.layers.add(name="TEXT", color=7)

    points = [(row['E'], row['N']) for _, row in df.iterrows()]
    msp.add_lwpolyline(points, close=True, dxfattribs={'layer': 'POLYGON'})
    
    for _, row in df.iterrows():
        e, n = row['E'], row['N']
        msp.add_point((e, n), dxfattribs={'layer': 'POINTS'})
        if 'STN' in df.columns:
            msp.add_text(f"STN {int(row['STN'])}", dxfattribs={'layer': 'TEXT', 'height': 1.0}).set_placement((e + 0.5, n + 0.5))
            
    stream = io.StringIO()
    doc.write(stream)
    return stream.getvalue()

# Inisialisasi session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- HALAMAN LOG MASUK ---
if not st.session_state.logged_in:
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try:
            st.image("logo.png", width=200)
        except:
            st.warning("⚠️ Logo 'logo.png' tidak dijumpai.")

        st.title("🌐 Sistem Maklumat Geografi")
        st.caption("Sila log masuk untuk mengakses portal pemetaan geospatial.")
        
        with st.form("login_form"):
            username = st.text_input("Nama Pengguna / Emel", placeholder="cth: admin")
            password = st.text_input("Kata Laluan", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Log Masuk", use_container_width=True)

            if submit:
                if username == "admin" and password == "1234":
                    st.session_state.logged_in = True
                    st.success("Log masuk berjaya!")
                    st.rerun()
                elif not username or not password:
                    st.warning("Sila isi kedua-dua ruangan.")
                else:
                    st.error("Nama pengguna atau kata laluan salah.")

# --- HALAMAN DASHBOARD / UTAMA ---
else:
    # Sidebar
    st.sidebar.header("⚙️ Panel Kawalan")
    
    uploaded_file = st.sidebar.file_uploader("📂 Muat Naik Fail CSV (E, N, STN)", type=["csv"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    # Tajuk Utama
    st.title("🗺️ Dashboard Analisis Poligon GIS")
    st.write("Visualisasi ruang, pengiraan luas, dan pemetaan interaktif geospatial.")
    st.markdown("---")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        if 'E' in df.columns and 'N' in df.columns:
            st.sidebar.success("✅ Fail CSV Berjaya Dimuat Naik")

            # Pengiraan Utama
            e_coords = df['E'].tolist()
            n_coords = df['N'].tolist()
            area_m2 = calculate_polygon_area(e_coords, n_coords)
            area_hectares = area_m2 / 10000.0
            center_e = np.mean(e_coords)
            center_n = np.mean(n_coords)

            # Paparan Metrik Cantik
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">📐 LUAS (METER PERSEGI)</div>
                        <div class="metric-value">{area_m2:,.2f} m²</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-title">🌾 LUAS (HEKTAR)</div>
                        <div class="metric-value">{area_hectares:,.4f} ha</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Tab Navigation
            tab_cad, tab_sat, tab_data, tab_export = st.tabs([
                "📐 Plot CAD 2D", 
                "🌍 Imej Satelit", 
                "📄 Jadual Data", 
                "📥 Eksport"
            ])

            # TAB 1: CAD VIEW
            with tab_cad:
                st.subheader("Visualisasi Poligon (2D CAD)")

                with st.expander("🛠️ Tetapan Paparan Plot 2D", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    show_cad_polygon = c1.checkbox("Poligon", value=True, key="cad_poly")
                    show_cad_points = c2.checkbox("Stesen (STN)", value=True, key="cad_pts")
                    show_cad_bearing = c3.checkbox("Bearing", value=False, key="cad_bear")
                    show_cad_distance = c4.checkbox("Jarak", value=False, key="cad_dist")

                fig, ax = plt.subplots(figsize=(8, 6))

                e_polygon = e_coords + [e_coords[0]]
                n_polygon = n_coords + [n_coords[0]]

                if show_cad_polygon:
                    ax.plot(e_polygon, n_polygon, color='#1e3a8a', linestyle='-', linewidth=2, label='Sempadan Poligon')
                    ax.fill(e_polygon, n_polygon, color='#3b82f6', alpha=0.25)

                if show_cad_points:
                    ax.scatter(e_coords, n_coords, color='#ef4444', s=40, zorder=5, label='Stesen (STN)')
                    if 'STN' in df.columns:
                        for idx, row in df.iterrows():
                            ax.annotate(f" STN {int(row['STN'])}", (row['E'], row['N']), fontsize=9, fontweight='bold', color='#111827')

                num_points = len(e_coords)
                for i in range(num_points):
                    x1, y1 = e_coords[i], n_coords[i]
                    x2, y2 = e_coords[(i + 1) % num_points], n_coords[(i + 1) % num_points]
                    
                    bearing, distance = calculate_bearing_distance(x1, y1, x2, y2)
                    mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2

                    label_text = ""
                    if show_cad_bearing and show_cad_distance:
                        label_text = f"{bearing}\n{distance:.2f}m"
                    elif show_cad_bearing:
                        label_text = f"{bearing}"
                    elif show_cad_distance:
                        label_text = f"{distance:.2f}m"

                    if label_text:
                        ax.text(mid_x, mid_y, label_text, fontsize=8, color='#065f46',
                                ha='center', va='center', bbox=dict(boxstyle='round,pad=0.3', facecolor='#d1fae5', edgecolor='#10b981', alpha=0.85))

                if show_cad_polygon:
                    ax.text(center_e, center_n, f"Luas:\n{area_m2:,.2f} m²", fontsize=10, 
                            fontweight='bold', color='#1e40af', ha='center', va='center',
                            bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffff', alpha=0.9, edgecolor='#3b82f6'))

                ax.set_title("Plot Sempadan Poligon & Pengiraan Luas", fontsize=12, pad=12)
                ax.set_xlabel("Easting (E)")
                ax.set_ylabel("Northing (N)")
                ax.grid(True, linestyle='--', alpha=0.4)
                ax.legend(loc='upper right')

                min_e, max_e = min(e_coords), max(e_coords)
                min_n, max_n = min(n_coords), max(n_coords)
                pad_e = max((max_e - min_e) * 0.1, 5)
                pad_n = max((max_n - min_n) * 0.1, 5)

                ax.set_xlim(min_e - pad_e, max_e + pad_e)
                ax.set_ylim(min_n - pad_n, max_n + pad_n)
                ax.set_aspect('equal', adjustable='box')
                ax.ticklabel_format(style='plain', useOffset=False)

                st.pyplot(fig, use_container_width=True)

            # TAB 2: IMEJ SATELIT
            with tab_sat:
                st.subheader("Overlay Peta Satelit Interaktif")

                crs_dict = {
                    "GDM2000 / Peninsula RSO (Piawai)": "3375",
                    "Kertau / RSO Malaya (Metres)": "3168",
                    "Kertau 1968 / Malaya Grid (Metres)": "4379",
                    "Kertau 1968 / Johor Grid (Metres)": "4390",
                    "GDM2000 / Borneo RSO (Sabah/Sarawak)": "3376",
                    "Timbalai 1948 / East Malaysia BRSO": "29873",
                    "Timbalai 1948 / Sabah Cassini": "29871",
                    "Perak": "2385",
                    "Selangor": "2384",
                    "Kedah & Perlis": "2383",
                    "Kelantan": "2381",
                    "Terengganu": "2382",
                    "Pahang": "2386",
                    "Negeri Sembilan & Melaka": "2387",
                    "Johor": "2388",
                    "Penang": "2389",
                    "WGS 84 / UTM Zone 47N (Semenanjung Barat)": "32647",
                    "WGS 84 / UTM Zone 48N (Semenanjung Timur & Sarawak Barat)": "32648",
                    "WGS 84 / UTM Zone 49N (Sarawak Timur & Sabah)": "32649",
                    "WGS 84 / UTM Zone 50N (Sabah Timur)": "32650",
                    "WGS 84 (Geographic Lat/Long)": "4326",
                    "Custom EPSG Code...": "CUSTOM"
                }

                with st.expander("🌍 Tetapan Koordinat & Layer Satelit", expanded=True):
                    col_crs, col_custom, col_swap = st.columns([2.5, 1.5, 1.5])

                    selected_crs_name = col_crs.selectbox(
                        "Sistem Koordinat Data CSV:",
                        options=list(crs_dict.keys()),
                        key="sat_crs_select"
                    )

                    if crs_dict[selected_crs_name] == "CUSTOM":
                        epsg_code = col_custom.text_input("Kod EPSG Tersuai:", value="3375", key="custom_epsg_input").strip()
                    else:
                        epsg_code = crs_dict[selected_crs_name]
                        col_custom.empty()

                    swap_axes = col_swap.checkbox("🔄 Tukar (E ↔ N)", value=False, key="sat_swap")

                    st.markdown("---")
                    sc1, sc2, sc3, sc4, sc5 = st.columns([1, 1, 1, 1, 1.5])
                    show_sat_polygon = sc1.checkbox("Poligon", value=True, key="sat_poly")
                    show_sat_points = sc2.checkbox("Stesen", value=True, key="sat_pts")
                    show_sat_bearing = sc3.checkbox("Bearing", value=True, key="sat_bear")
                    show_sat_distance = sc4.checkbox("Jarak", value=True, key="sat_dist")
                    zoom_level = sc5.slider("Zoom:", min_value=10, max_value=20, value=17, step=1, key="sat_zoom")

                try:
                    latlon_coords = reproject_coordinates(e_coords, n_coords, epsg_code, swap_axes=swap_axes)
                    center_lat = np.mean([pt[0] for pt in latlon_coords])
                    center_lon = np.mean([pt[1] for pt in latlon_coords])

                    m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_level, max_zoom=20, tiles=None)

                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                        attr='Google',
                        name='Google Satellite',
                        overlay=False,
                        control=True,
                        max_zoom=20
                    ).add_to(m)

                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google',
                        name='Google Hybrid',
                        overlay=False,
                        control=True,
                        max_zoom=20
                    ).add_to(m)

                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
                        attr='Google',
                        name='Google Roadmap',
                        overlay=False,
                        control=True,
                        max_zoom=20
                    ).add_to(m)

                    folium.TileLayer(
                        tiles='OpenStreetMap',
                        name='OpenStreetMap',
                        overlay=False,
                        control=True
                    ).add_to(m)

                    if show_sat_polygon:
                        folium.Polygon(
                            locations=latlon_coords,
                            color='#f59e0b',
                            weight=3,
                            fill=True,
                            fill_color='#06b6d4',
                            fill_opacity=0.35,
                            popup=f"Luas: {area_m2:,.2f} m² ({area_hectares:.4f} ha)"
                        ).add_to(m)

                    if show_sat_points:
                        for idx, (lat, lon) in enumerate(latlon_coords):
                            stn_label = f"STN {df['STN'].iloc[idx]}" if 'STN' in df.columns else f"STN {idx+1}"
                            folium.CircleMarker(
                                location=[lat, lon],
                                radius=5,
                                color='#ef4444',
                                fill=True,
                                fill_color='#ffffff',
                                fill_opacity=1.0,
                                popup=f"{stn_label}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}"
                            ).add_to(m)

                    if show_sat_bearing or show_sat_distance:
                        num_pts = len(e_coords)
                        for i in range(num_pts):
                            x1, y1 = e_coords[i], n_coords[i]
                            x2, y2 = e_coords[(i + 1) % num_pts], n_coords[(i + 1) % num_pts]
                            
                            bearing, distance = calculate_bearing_distance(x1, y1, x2, y2)
                            
                            lat1, lon1 = latlon_coords[i]
                            lat2, lon2 = latlon_coords[(i + 1) % num_pts]
                            mid_lat = (lat1 + lat2) / 2
                            mid_lon = (lon1 + lon2) / 2

                            label_text = ""
                            if show_sat_bearing and show_sat_distance:
                                label_text = f"{bearing}<br>{distance:.2f}m"
                            elif show_sat_bearing:
                                label_text = f"{bearing}"
                            elif show_sat_distance:
                                label_text = f"{distance:.2f}m"

                            if label_text:
                                html_content = f"""
                                <div style="
                                    font-size: 10px;
                                    font-weight: bold;
                                    color: #064e3b;
                                    background-color: rgba(254, 243, 199, 0.9);
                                    border: 1px solid #059669;
                                    padding: 2px 4px;
                                    border-radius: 4px;
                                    text-align: center;
                                    white-space: nowrap;
                                ">{label_text}</div>
                                """
                                folium.Marker(
                                    location=[mid_lat, mid_lon],
                                    icon=folium.DivIcon(
                                        icon_size=(100, 20),
                                        icon_anchor=(50, 10),
                                        html=html_content
                                    )
                                ).add_to(m)

                    folium.LayerControl().add_to(m)

                    st_folium(m, use_container_width=True, height=550)

                except Exception as e:
                    st.error(f"⚠️ Ralat Unjuran Koordinat (EPSG:{epsg_code}): {e}")

            # TAB 3: DATA KOORDINAT
            with tab_data:
                st.subheader("Jadual Data Koordinat Input")
                st.dataframe(df, use_container_width=True, hide_index=True)

            # TAB 4: EKSPORT FAIL
            with tab_export:
                st.subheader("Muat Turun Hasil Eksport")
                st.write("Eksport data ke format GeoJSON (ruang GIS) atau DXF (CAD/AutoCAD).")
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_exp1, col_exp2 = st.columns(2)

                try:
                    active_epsg = epsg_code if 'epsg_code' in locals() else "3375"
                    active_swap = swap_axes if 'swap_axes' in locals() else False
                    
                    latlon_coords = reproject_coordinates(e_coords, n_coords, active_epsg, swap_axes=active_swap)
                    geojson_file = generate_geojson(df, latlon_coords)
                    col_exp1.download_button(
                        label="🌐 Muat Turun GeoJSON (WGS84)",
                        data=geojson_file,
                        file_name="peta_poligon_wgs84.geojson",
                        mime="application/json",
                        use_container_width=True
                    ) # <-- Pembetulan di sini (tambah penutup kurungan)

                except Exception as e:
                    col_exp1.error("Gagal menjana GeoJSON (Semak tetapan CRS).")

                dxf_file = generate_dxf(df)
                col_exp2.download_button(
                    label="📐 Muat Turun DXF (AutoCAD)",
                    data=dxf_file,
                    file_name="pelan_poligon.dxf",
                    mime="application/dxf",
                    use_container_width=True
                )

        else:
            st.error("⚠️ Fail CSV mesti mengandungi lajur 'E' (Easting) dan 'N' (Northing).")
