import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- PAGE SETUP ---
st.set_page_config(page_title="OAF Nursery Analytics", layout="wide", page_icon="🌳")

# --- GOOGLE SHEETS CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("📊 OAF Nursery Production Analytics")
st.markdown("Live management intelligence metrics from Google Sheets.")
st.divider()

# --- LOAD DATA ---
with st.spinner("Loading data from Google Sheets..."):
    try:
        df = conn.read(worksheet="Sheet1", ttl=0).dropna(how="all")
        st.success(f"✅ Loaded {len(df)} rows successfully!")
    except Exception as e:
        st.error(f"❌ Failed to load data: {e}")
        st.info("Make sure: (1) Google Sheets API is enabled, (2) Sheet is shared with Service Account as Editor, (3) secrets.toml is correct")
        st.stop()

# --- EMPTY STATE ---
if df.empty:
    st.warning("⚠️ No data found in 'Sheet1'. The sheet exists but has no rows.")
    st.stop()

# --- DATA CLEANING ---
numeric_cols = ["guava_beds", "gesho_beds", "lemon_beds", "grevillea_beds"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# --- KPI METRICS ---
total_nurseries = len(df)
sum_guava = int(df["guava_beds"].sum()) if "guava_beds" in df.columns else 0
sum_gesho = int(df["gesho_beds"].sum()) if "gesho_beds" in df.columns else 0
sum_lemon = int(df["lemon_beds"].sum()) if "lemon_beds" in df.columns else 0
sum_grevillea = int(df["grevillea_beds"].sum()) if "grevillea_beds" in df.columns else 0
total_beds = sum_guava + sum_gesho + sum_lemon + sum_grevillea

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("🚜 Monitored Locations", f"{total_nurseries}")
kpi2.metric("🌱 Total Active Beds", f"{total_beds:,}")
kpi3.metric("📊 Mean Bed Capacity/Site", f"{round(total_beds/total_nurseries, 1) if total_nurseries > 0 else 0}")

st.divider()

# --- FILTERS ---
st.markdown("### 🔍 Filter Controls")

# Woreda filter
if "woreda" in df.columns:
    sel_woreda = st.multiselect(
        "Isolate targeted Woredas / ወረዳዎች:", 
        options=sorted(df["woreda"].dropna().unique()), 
        default=sorted(df["woreda"].dropna().unique())
    )
    filtered_df = df[df["woreda"].isin(sel_woreda)] if sel_woreda else df.iloc[0:0]
else:
    st.warning("No 'woreda' column found in data.")
    filtered_df = df

st.divider()

# --- CHARTS ---
if filtered_df.empty:
    st.info("ℹ️ No data matches the selected filters.")
else:
    ch1, ch2 = st.columns(2)
    
    with ch1:
        st.markdown("#### Crop Distribution Metrics (Total Beds)")
        species_data = {
            "Species": ["Guava", "Gesho", "Lemon", "Grevillea"],
            "Total Beds": [
                int(filtered_df["guava_beds"].sum()) if "guava_beds" in filtered_df.columns else 0,
                int(filtered_df["gesho_beds"].sum()) if "gesho_beds" in filtered_df.columns else 0,
                int(filtered_df["lemon_beds"].sum()) if "lemon_beds" in filtered_df.columns else 0,
                int(filtered_df["grevillea_beds"].sum()) if "grevillea_beds" in filtered_df.columns else 0,
            ]
        }
        species_totals = pd.DataFrame(species_data)
        fig_bar = px.bar(
            species_totals, 
            x="Species", 
            y="Total Beds", 
            color="Species", 
            text_auto=True, 
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with ch2:
        st.markdown("#### Asset Integrity Status (Fencing Ratio)")
        if "is_fenced" in filtered_df.columns:
            fence_counts = filtered_df["is_fenced"].value_counts().reset_index()
            if not fence_counts.empty:
                fence_counts.columns = ["Fenced Status", "Count"]
                fig_pie = px.pie(
                    fence_counts, 
                    values="Count", 
                    names="Fenced Status", 
                    hole=0.4, 
                    color_discrete_sequence=["#2ecc71", "#e74c3c"]
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No fencing data available.")
        else:
            st.info("No 'is_fenced' column found.")

    st.divider()
    st.markdown("#### 📁 Active Data Ledger Summary")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
