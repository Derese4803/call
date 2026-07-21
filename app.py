import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="OAF Nursery Analytics", layout="wide", page_icon="🌳")

# --- LOAD DATA: Try Google Sheet first, fallback to local ---
@st.cache_data(ttl=300)
def load_data():
    """Try to load from Google Sheets, fallback to local CSV if fails"""
    
    # Try Google Sheets first
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet="Sheet1", ttl=0)
        st.sidebar.success("✅ Connected to Google Sheets")
        return df, "google_sheets"
    except Exception as e:
        st.sidebar.warning(f"⚠️ Google Sheets failed: {str(e)[:80]}...")
        
        # Fallback: Look for local data file
        try:
            # Try to find the data file in common locations
            possible_paths = [
                "nursery_data.csv",
                "data.csv",
                "sheet_data.csv",
                os.path.join(os.path.dirname(__file__), "nursery_data.csv"),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    st.sidebar.info(f"📁 Loaded from local file: {path}")
                    return df, "local"
            
            # If no file found, create sample dataframe with correct columns
            st.sidebar.error("❌ No data source found!")
            st.sidebar.info("Please either:\n1. Fix Google Sheets connection, or\n2. Save your data as 'nursery_data.csv' in the app folder")
            
            # Return empty dataframe with expected columns
            return pd.DataFrame(), "none"
            
        except Exception as e2:
            st.sidebar.error(f"❌ Local file also failed: {str(e2)[:80]}")
            return pd.DataFrame(), "none"

# --- SIDEBAR ---
st.sidebar.title("🌳 OAF System Menu")
st.sidebar.markdown("Nursery Count Analytics Dashboard")

# Load data
with st.spinner("Loading data..."):
    df, source = load_data()

# Show data source info
if source == "google_sheets":
    st.sidebar.success("📡 Live data from Google Sheets")
elif source == "local":
    st.sidebar.info("📁 Using local data file")
else:
    st.sidebar.error("⚠️ No data loaded!")

st.sidebar.divider()

# --- MAIN DASHBOARD ---
st.title("📊 OAF Nursery Production Analytics")
st.markdown("Live management intelligence metrics from field count data.")

if df.empty:
    st.error("""
    ❌ **No data available!**
    
    To fix this, you need to:
    
    **Option 1: Fix Google Sheets Connection**
    - Make sure `.streamlit/secrets.toml` is configured
    - Share your Google Sheet with: `oaf-nursery-project@helpful-monitor-482107-h6.iam.gserviceaccount.com`
    - Enable Google Sheets API in Google Cloud Console
    
    **Option 2: Use Local Data**
    - Save your data as `nursery_data.csv` in the same folder as `app.py`
    """)
    st.stop()

# --- DATA CLEANING ---
# Clean column names
df.columns = df.columns.str.strip()

# Identify species columns (Ready counts)
species_ready_cols = [
    'Gesho Count Ready', 'Grevillea Count Ready', 'Decurrens Count Ready',
    'Wanza Count Ready', 'Papaya Count Ready', 'Moringa Count Ready',
    'Coffee Count Ready', 'Guava Count Ready', 'Lemon Count Ready',
    'Arzelibano Count Ready', 'Neem Count Ready'
]

# Clean numeric columns - remove commas and convert
for col in df.columns:
    if df[col].dtype == object:
        # Try to clean commas from numbers
        try:
            df[col] = df[col].astype(str).str.replace(',', '').replace('nan', pd.NA)
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except:
            pass

# --- FILTERS ---
st.markdown("### 🔍 Filter Controls")

col1, col2, col3 = st.columns(3)

with col1:
    if 'Zone' in df.columns:
        zones = sorted(df['Zone'].dropna().unique())
        sel_zones = st.multiselect("Zone:", zones, default=zones)
    else:
        sel_zones = []
        st.warning("No 'Zone' column")

with col2:
    if 'Woreda' in df.columns:
        woredas = sorted(df['Woreda'].dropna().unique())
        sel_woredas = st.multiselect("Woreda:", woredas, default=woredas)
    else:
        sel_woredas = []
        st.warning("No 'Woreda' column")

with col3:
    if 'Cluster' in df.columns:
        clusters = sorted(df['Cluster'].dropna().unique())
        sel_clusters = st.multiselect("Cluster:", clusters, default=clusters)
    else:
        sel_clusters = []
        st.warning("No 'Cluster' column")

# Apply filters
filtered_df = df.copy()
if sel_zones and 'Zone' in df.columns:
    filtered_df = filtered_df[filtered_df['Zone'].isin(sel_zones)]
if sel_woredas and 'Woreda' in df.columns:
    filtered_df = filtered_df[filtered_df['Woreda'].isin(sel_woredas)]
if sel_clusters and 'Cluster' in df.columns:
    filtered_df = filtered_df[filtered_df['Cluster'].isin(sel_clusters)]

st.divider()

# --- KPI METRICS ---
st.markdown("### 📈 Key Performance Indicators")

# Calculate totals
total_kebeles = len(filtered_df)

# Species totals
species_summary = {}
for species in ['Gesho', 'Grevillea', 'Decurrens', 'Wanza', 'Papaya', 
                'Moringa', 'Coffee', 'Guava', 'Lemon', 'Arzelibano', 'Neem']:
    ready_col = f'{species} Count Ready'
    if ready_col in filtered_df.columns:
        species_summary[species] = filtered_df[ready_col].sum()

total_ready = sum(species_summary.values())

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("🏘️ Kebeles", f"{total_kebeles}")
kpi2.metric("🌱 Total Ready Seedlings", f"{total_ready:,.0f}")
kpi3.metric("📊 Avg Ready/Kebele", f"{total_ready/total_kebeles:,.0f}" if total_kebeles > 0 else "0")
kpi4.metric("📍 Woredas", f"{filtered_df['Woreda'].nunique()}" if 'Woreda' in filtered_df.columns else "N/A")

st.divider()

# --- CHARTS ---
if filtered_df.empty:
    st.info("ℹ️ No data matches the selected filters.")
else:
    ch1, ch2 = st.columns(2)
    
    with ch1:
        st.markdown("#### 🌿 Species Distribution (Ready Count)")
        if species_summary:
            species_df = pd.DataFrame({
                "Species": list(species_summary.keys()),
                "Ready Count": list(species_summary.values())
            }).sort_values("Ready Count", ascending=True)
            
            fig_bar = px.bar(
                species_df, 
                y="Species", 
                x="Ready Count", 
                orientation='h',
                color="Species",
                text_auto=True,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No species data found")
    
    with ch2:
        st.markdown("#### 🥧 Species Proportion")
        if species_summary:
            species_df = pd.DataFrame({
                "Species": list(species_summary.keys()),
                "Ready Count": list(species_summary.values())
            })
            fig_pie = px.pie(
                species_df,
                values="Ready Count",
                names="Species",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No species data found")

    st.divider()
    
    # Zone/Woreda breakdown
    st.markdown("#### 📍 Ready Seedlings by Zone & Woreda")
    if 'Zone' in filtered_df.columns and 'Woreda' in filtered_df.columns:
        zone_woreda = filtered_df.groupby(['Zone', 'Woreda']).size().reset_index(name='Kebele Count')
        fig_sunburst = px.sunburst(
            filtered_df,
            path=['Zone', 'Woreda', 'Kebele'],
            values='Gesho Count Ready' if 'Gesho Count Ready' in filtered_df.columns else None,
            color='Zone'
        )
        st.plotly_chart(fig_sunburst, use_container_width=True)
    
    st.divider()
    
    # Data table
    st.markdown("#### 📁 Full Data Ledger")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "⬇️ Download Filtered Data as CSV",
        csv,
        "nursery_filtered_data.csv",
        "text/csv"
    )

st.sidebar.divider()
st.sidebar.caption("OAF Nursery Management System")
