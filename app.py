import streamlit as st
import pandas as pd
import datetime
import re
import os
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- DEBUG: Check secrets file location ---
st.write("Current working directory:", os.getcwd())
secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")
st.write("Looking for secrets at:", secrets_path)
st.write("File exists:", os.path.exists(secrets_path))

if os.path.exists(secrets_path):
    st.success("✅ secrets.toml found!")
    try:
        st.write("Spreadsheet from secrets:", st.secrets["connections"]["gsheets"]["spreadsheet"])
        st.write("Service account email:", st.secrets["connections"]["gsheets"]["credentials"]["client_email"])
    except Exception as e:
        st.error(f"❌ Error reading secrets: {e}")
else:
    st.error("❌ secrets.toml NOT FOUND! Check folder structure.")
    st.info("Expected path: " + secrets_path)
    st.stop()  # Stop app if secrets not found

# --- 1. INITIAL SYSTEM SETUP ---
st.set_page_config(page_title="OAF Nursery Management Portal", layout="wide", page_icon="🌳")

# Initialize Google Sheets connection
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("✅ GSheets connection initialized!")
except Exception as e:
    st.error(f"❌ Failed to initialize GSheets connection: {e}")
    st.stop()

# Simple state manager for sidebar page routing
if "page" not in st.session_state: 
    st.session_state["page"] = "Form"

def navigate_to(page_name):
    st.session_state["page"] = page_name

# --- 2. SIDEBAR MULTI-PAGE NAVIGATION ---
st.sidebar.title("OAF System Menu 🌳")
st.sidebar.markdown("Navigate through registration and reporting windows.")

if st.sidebar.button("📝 Farmer Registration Form", use_container_width=True): 
    navigate_to("Form")
    st.rerun()
    
if st.sidebar.button("📊 Live Analytics Dashboard", use_container_width=True): 
    navigate_to("Dashboard")
    st.rerun()

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
        woreda = f1.text_input("Woreda / ወረዳ *")
        kebele = f2.text_input("Kebele / ቀበሌ *")
        tno_name = f3.text_input("TNO Name / የTNO ስም *")
        
        st.divider()
        st.markdown("#### 👤 Farmer & Operational Profiles")
        c1, c2, c3 = st.columns(3)
        fa_name = c1.text_input("FA Name / የFA ስም")
        cbe_account = c2.text_input("CBE Account / የባንክ ሂሳብ")
        phone_number = c3.text_input("Phone Number / ስልክ ቁጥር", placeholder="e.g., 0912345678")
        
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
        # Validation
        woreda = woreda.strip()
        kebele = kebele.strip()
        tno_name = tno_name.strip()
        phone_number = phone_number.strip()
        cbe_account = cbe_account.strip()
        rem = rem.strip()
        
        errors = []
        if not woreda:
            errors.append("Woreda / ወረዳ is required.")
        if not kebele:
            errors.append("Kebele / ቀበሌ is required.")
        if not tno_name:
            errors.append("TNO Name / የTNO ስም is required.")
        
        if phone_number and not re.match(r'^(09\d{8}|\+251\d{9})$', phone_number):
            errors.append("Phone number must be a valid Ethiopian number (e.g., 0912345678 or +251912345678).")
        
        if cbe_account and not re.match(r'^\d{13,16}$', cbe_account):
            errors.append("CBE Account must be 13-16 digits.")
        
        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            with st.spinner("Pushing operational records directly to cloud databases..."):
                try:
                    # Read existing data
                    try:
                        existing_df = conn.read(worksheet="Sheet1", ttl=0).dropna(how="all")
                        st.write("Existing rows:", len(existing_df))
                    except Exception as read_err:
                        st.warning(f"Could not read existing data (this is OK for new sheet): {read_err}")
                        existing_df = pd.DataFrame()

                    # Prepare new row
                    new_row = {
                        'woreda': woreda, 
                        'kebele': kebele, 
                        'tno_name': tno_name,
                        'fa_name': fa_name, 
                        'cbe_account': cbe_account, 
                        'phone_number': phone_number, 
                        'is_fenced': fenced, 
                        'guava_beds': int(g_b), 
                        'gesho_beds': int(ge_b), 
                        'lemon_beds': int(l_b), 
                        'grevillea_beds': int(gr_b), 
                        'general_remark': rem, 
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Append and save
                    updated_df = pd.concat([existing_df, pd.DataFrame([new_row])], ignore_index=True)
                    
                    st.write("Attempting to write", len(updated_df), "rows...")
                    conn.create(worksheet="Sheet1", data=updated_df)
                    
                    st.success("✅ Transaction complete. Row verified and saved to Google Sheets.")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"GSheets Execution Exception raised: {e}")
                    st.info("Common causes: Sheet not shared with service account, or wrong spreadsheet URL in secrets.toml")


# --- 4. INTERACTIVE PAGE: LIVE EXECUTIVE DASHBOARD ---
elif st.session_state["page"] == "Dashboard":
    st.title("📊 OAF Nursery Production Analytics")
    st.markdown("Live management intelligence metrics computed directly from target spreadsheet records.")
    st.divider()

    with st.spinner("Streaming analytical indexes from remote storage..."):
        try:
            df = conn.read(worksheet="Sheet1", ttl=0).dropna(how="all")
            st.write("Loaded", len(df), "rows from Sheet1")
        except Exception as e:
            st.error(f"Failed to read data: {e}")
            df = pd.DataFrame()

    if df.empty:
        st.warning("⚠️ No database metrics located in 'Sheet1'. Submit form registrations to display analytics.")
    else:
        # Cast numeric columns
        numeric_cols = ["guava_beds", "gesho_beds", "lemon_beds", "grevillea_beds"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Calculate KPIs
        total_nurseries = len(df)
        sum_guava = int(df["guava_beds"].sum())
        sum_gesho = int(df["gesho_beds"].sum())
        sum_lemon = int(df["lemon_beds"].sum())
        sum_grevillea = int(df["grevillea_beds"].sum())
        total_beds = sum_guava + sum_gesho + sum_lemon + sum_grevillea
        
        # KPI cards
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("🚜 Monitored Locations", f"{total_nurseries}")
        kpi2.metric("🌱 Total Active Beds", f"{total_beds:,}")
        kpi3.metric("📊 Mean Bed Capacity/Site", f"{round(total_beds/total_nurseries, 1) if total_nurseries > 0 else 0}")
        
        st.divider()

        # Filters
        st.markdown("### 🔍 Filter Controls")
        sel_woreda = st.multiselect(
            "Isolate targeted Woredas / ወረዳዎች:", 
            options=sorted(df["woreda"].dropna().unique()), 
            default=sorted(df["woreda"].dropna().unique())
        )
        filtered_df = df[df["woreda"].isin(sel_woreda)] if sel_woreda else df.iloc[0:0]

        st.divider()

        if filtered_df.empty:
            st.info("ℹ️ No data matches the selected filters.")
        else:
            ch1, ch2 = st.columns(2)
            
            with ch1:
                st.markdown("#### Crop Distribution Metrics (Total Beds)")
                species_totals = pd.DataFrame({
                    "Species": ["Guava", "Gesho", "Lemon", "Grevillea"],
                    "Total Beds": [
                        int(filtered_df["guava_beds"].sum()), 
                        int(filtered_df["gesho_beds"].sum()), 
                        int(filtered_df["lemon_beds"].sum()), 
                        int(filtered_df["grevillea_beds"].sum())
                    ]
                })
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

            st.divider()
            st.markdown("#### 📁 Active Data Ledger Summary")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
