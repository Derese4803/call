import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. INITIAL SYSTEM SETUP ---
# Configure layout to wide mode for the dashboard grid system
st.set_page_config(page_title="OAF Nursery Management Portal", layout="wide", page_icon="🌳")

# Establish direct data connection to Google Sheets using Streamlit Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# Simple state manager to handle sidebar page routing
if "page" not in st.session_state: 
    st.session_state["page"] = "Form"

def navigate_to(page_name):
    st.session_state["page"] = page_name
    st.rerun()

# --- 2. SIDEBAR MULTI-PAGE NAVIGATION ---
st.sidebar.title("OAF System Menu 🌳")
st.sidebar.markdown("Navigate through registration and reporting windows.")

if st.sidebar.button("📝 Farmer Registration Form", use_container_width=True): 
    navigate_to("Form")
    
if st.sidebar.button("📊 Live Analytics Dashboard", use_container_width=True): 
    navigate_to("Dashboard")

st.sidebar.divider()
st.sidebar.caption("Connected to Google Cloud Platform via secure Service Account Protocol.")


# --- 3. INTERACTIVE PAGE: REGISTRATION FORM ---
if st.session_state["page"] == "Form":
    st.title("🚜 Nursery Back Check Entry / መመዝገቢያ ቅጽ")
    st.markdown("Submit field collection parameters straight to the core database pipeline.")
    st.divider()
    
    with st.form("main_form", clear_on_submit=True):
        st.markdown("#### 📍 Administrative Attributes")
        f1, f2, f3 = st.columns(3)
        woreda = f1.text_input("Woreda / ወረዳ *").strip()
        kebele = f2.text_input("Kebele / ቀበሌ *").strip()
        tno_name = f3.text_input("TNO Name / የTNO ስም *").strip()
        
        st.divider()
        st.markdown("#### 👤 Farmer & Operational Profiles")
        c1, c2, c3 = st.columns(3)
        fa_name = c1.text_input("FA Name / የFA ስም").strip()
        cbe_account = c2.text_input("CBE Account / የባንክ ሂሳብ").strip()
        phone_number = c3.text_input("Phone Number / ስልክ ቁጥር").strip()
        
        fenced = st.radio("Is it Fenced? / አጥር አለው?", ["Yes / አለው", "No / የለውም"], horizontal=True)
        
        st.divider()
        st.markdown("#### 🌱 Seedling Bed Allocations")
        col_g, col_ge, col_l, col_gr = st.columns(4)
        g_b = col_g.number_input("Guava Beds / ዘይቶን", min_value=0, step=1)
        ge_b = col_ge.number_input("Gesho Beds / ጌሾ", min_value=0, step=1)
        l_b = col_l.number_input("Lemon Beds / ሎሚ", min_value=0, step=1)
        gr_b = col_gr.number_input("Grevillea Beds / ግራቪሊያ", min_value=0, step=1)
        
        st.divider()
        rem = st.text_area("Field Operational Remarks / አስተያየት")
        
        submit = st.form_submit_button("Submit Data / መረጃውን መዝግብ")

    if submit:
        if not woreda or not kebele or not tno_name:
            st.error("❌ Crucial verification failure: Woreda, Kebele, and TNO Name inputs are mandatory!")
        else:
            with st.spinner("Pushing operational records directly to cloud databases..."):
                try:
                    # Sync with current spreadsheet data to find target append boundaries
                    try:
                        existing_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how="all")
                    except Exception:
                        existing_df = pd.DataFrame()

                    # Format the UI information into a structured data frame row matching database tables
                    new_row = {
                        'woreda': woreda, 'kebele': kebele, 'tno_name': tno_name,
                        'fa_name': fa_name, 'cbe_account': cbe_account, 'phone_number': phone_number, 
                        'is_fenced': fenced, 'guava_beds': g_b, 'gesho_beds': ge_b, 
                        'lemon_beds': l_b, 'grevillea_beds': gr_b, 'general_remark': rem, 
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Append data structure downstream
                    updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    # Overwrite/push straight back to target worksheet endpoint using the correct .update() method
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    # Clear internal cache so dashboard registers fresh entries instantly
                    st.cache_data.clear()
                    
                    st.success("✅ Transaction complete. Row verified and saved to Google Sheets.")
                    st.balloons()
                except Exception as e:
                    st.error(f"GSheets Execution Exception raised: {e}")


# --- 4. INTERACTIVE PAGE: LIVE EXECUTIVE DASHBOARD ---
elif st.session_state["page"] == "Dashboard":
    st.title("📊 OAF Nursery Production Analytics")
    st.markdown("Live management intelligence metrics computed directly from target spreadsheet records.")
    st.divider()

    with st.spinner("Streaming analytical indexes from remote storage..."):
        try:
            # Bypass cache (ttl=0) to force a fresh data sync on every load
            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how="all")
        except Exception:
            df = pd.DataFrame()

    if df.empty:
        st.warning("⚠️ No database metrics located in 'Sheet1'. Submit form registrations to display analytics.")
    else:
        # Cast critical text-based table elements back to high-fidelity numbers safely
        for col in ["guava_beds", "gesho_beds", "lemon_beds", "grevillea_beds"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Aggregate total calculation metrics across rows
        total_nurseries = len(df)
        sum_guava = int(df["guava_beds"].sum())
        sum_gesho = int(df["gesho_beds"].sum())
        sum_lemon = int(df["lemon_beds"].sum())
        sum_grevillea = int(df["grevillea_beds"].sum())
        total_beds = sum_guava + sum_gesho + sum_lemon + sum_grevillea
        
        # Display KPI banner cards
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("🚜 Monitored Locations", f"{total_nurseries}")
        kpi2.metric("🌱 Total Active Beds", f"{total_beds:,}")
        kpi3.metric("📊 Mean Bed Capacity/Site", f"{round(total_beds/total_nurseries, 1) if total_nurseries > 0 else 0}")
        
        st.divider()

        # Operational interactive filtering elements
        st.markdown("### 🔍 Filter Controls")
        sel_woreda = st.multiselect("Isolate targeted Woredas / ወረዳዎች:", options=df["woreda"].unique(), default=df["woreda"].unique())
        filtered_df = df[df["woreda"].isin(sel_woreda)]

        st.divider()

        # Render data visualization elements
        ch1, ch2 = st.columns(2)
        
        with ch1:
            st.markdown("#### Crop Distribution Metrics (Total Beds)")
            species_totals = pd.DataFrame({
                "Species": ["Guava", "Gesho", "Lemon", "Grevillea"],
                "Total Beds": [
                    filtered_df["guava_beds"].sum(), 
                    filtered_df["gesho_beds"].sum(), 
                    filtered_df["lemon_beds"].sum(), 
                    filtered_df["grevillea_beds"].sum()
                ]
            })
            fig_bar = px.bar(species_totals, x="Species", y="Total Beds", color="Species", text_auto=True, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with ch2:
            st.markdown("#### Asset Integrity Status (Fencing Ratio)")
            fence_counts = filtered_df["is_fenced"].value_counts().reset_index()
            fence_counts.columns = ["Fenced Status", "Count"]
            fig_pie = px.pie(fence_counts, values="Count", names="Fenced Status", hole=0.4, color_discrete_sequence=["#2ecc71", "#e74c3c"])
            st.plotly_chart(fig_pie, use_container_width=True)

        st.divider()
        st.markdown("#### 📁 Active Data Ledger Summary")
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
