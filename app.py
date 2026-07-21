import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import json

# --- PAGE SETUP ---
st.set_page_config(page_title="OAF Nursery Analytics", layout="wide", page_icon="🌳")

st.title("📊 OAF Nursery Production Analytics")
st.markdown("Live management intelligence metrics from Google Sheets.")

# --- GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    """Connect to Google Sheets using gspread with Service Account"""
    try:
        # Load credentials from secrets.toml
        creds_info = dict(st.secrets["connections"]["gsheets"]["credentials"])
        
        # Create credentials object
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        
        # Authorize gspread
        client = gspread.authorize(creds)
        return client
        
    except Exception as e:
        st.error(f"❌ Authentication failed: {e}")
        return None

@st.cache_data(ttl=300)
def load_sheet_data():
    """Load data from Google Sheet"""
    client = get_gsheet_client()
    
    if client is None:
        return pd.DataFrame(), False
    
    try:
        # Open sheet by URL
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        spreadsheet = client.open_by_url(sheet_url)
        
        # Get first worksheet
        worksheet = spreadsheet.sheet1
        
        # Get all records
        data = worksheet.get_all_records()
        
        df = pd.DataFrame(data)
        
        return df, True
        
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Spreadsheet not found. Check the URL in secrets.toml")
        return pd.DataFrame(), False
        
    except gspread.exceptions.APIError as e:
        st.error(f"❌ Google API Error: {e}")
        st.info("Make sure the sheet is shared with the Service Account email as EDITOR")
        return pd.DataFrame(), False
        
    except Exception as e:
        st.error(f"❌ Error reading sheet: {e}")
        return pd.DataFrame(), False

# --- LOAD DATA ---
with st.spinner("Connecting to Google Sheets..."):
    df, success = load_sheet_data()

if not success:
    st.error("""
    ❌ **Failed to connect to Google Sheets!**
    
    **Required fixes:**
    
    1. **Enable APIs** in Google Cloud Console:
       - Google Sheets API
       - Google Drive API
    
    2. **Share your sheet** with Service Account email as **EDITOR**
    
    3. **Verify secrets.toml** has correct credentials
    
    4. **Install required package:**
       ```bash
       pip install gspread
       ```
    """)
    st.stop()

# Show success
st.success(f"✅ Connected! Loaded {len(df)} rows and {len(df.columns)} columns")

# --- SIDEBAR ---
st.sidebar.title("🌳 OAF System Menu")
st.sidebar.markdown("Nursery Count Analytics Dashboard")
st.sidebar.success("📡 Live data from Google Sheets")
st.sidebar.divider()

# --- DATA CLEANING ---
# Clean column names
df.columns = df.columns.str.strip()

# Convert numeric columns - remove commas
for col in df.columns:
    if df[col].dtype == object:
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

total_kebeles = len(filtered_df)

# Species totals
species_list = ['Gesho', 'Grevillea', 'Decurrens', 'Wanza', 'Papaya', 
                'Moringa', 'Coffee', 'Guava', 'Lemon', 'Arzelibano', 'Neem']

species_summary = {}
for species in species_list:
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
