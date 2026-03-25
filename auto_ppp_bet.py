import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Page Configuration ---
st.set_page_config(page_title="NBA Live PPP Tracker", page_icon="🏀", layout="centered")

# --- Styling & Header ---
st.title("🏀 NBA Q1 Live Stats & Strategy")
st.markdown("Enter Q1 stats to identify efficiency outliers for Q2 betting.")

# --- Sidebar: Reference & Outliers ---
with st.sidebar:
    st.header("📌 Betting Reminders (Outliers)")
    st.info("**Brooklyn Nets**: Unpredicatable Q2 when Q1 is underscoring")
    st.warning("**Spurs**: The Alien (Wemby) is a wild card.")
    st.error("**Wolves (30-33 pts)**: Not really hyper-efficient within the range but often underperform in Q2. Caution on unders.")
    st.divider()
# --- st.write("Formula: `0.96 * (FGA + (0.44 * FTA) - OREB + TOV)`")

# --- Connection to Google Sheets ---
# This uses the URL from your Streamlit Secrets or local .streamlit/secrets.toml
conn = st.connection("gsheets", type=GSheetsConnection)

# --- Input Form ---
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        team_name = st.text_input("Team Name", placeholder="e.g. Lakers")
        pts = st.number_input("Points Scored", min_value=0, step=1)
        fga = st.number_input("Field Goal Attempts (FGA)", min_value=0, step=1)
    with col2:
        fta = st.number_input("Free Throw Attempts (FTA)", min_value=0.0, step=1.0)
        oreb = st.number_input("Offensive Rebounds (OREB)", min_value=0, step=1)
        tov = st.number_input("Turnovers (TOV)", min_value=0, step=1)

# --- Calculation Engine ---
if st.button("Calculate & Analyze", use_container_width=True, type="primary"):
    # Possession Formula
    possessions = 0.96 * (fga + (0.44 * fta) - oreb + tov)
    
    if possessions > 0:
        ppp = pts / possessions
        
        # Q2 Estimation Logic
        if pts > 21:        
            over_est = round(((pts + 28) * 0.5), 2)
        else:
            over_est = round(((pts + 28) * 0.5) - 1, 2)

        if pts < 37:        
            under_est = round(((pts + 30) * 0.5), 2)
        else:
            under_est = round(((pts + 30) * 0.5) + 1, 2)

        # --- Display Results ---
        st.divider()
        m1, m2 = st.columns(2)
        m1.metric("Est. Possessions", f"{possessions:.2f}")
        m2.metric("PPP (Efficiency)", f"{ppp:.3f}")

        # Logic-Based Recommendations
        rec = "No Bet"
        target = 0
        
        if ppp > 1.35:
            rec = "Under"
            target = under_est
            st.error(f"⚠️ FADE ALERT: {team_name} is Overperforming.")
            st.subheader(f"🎯 Strategy: Bet UNDER {under_est:.1f}")
        elif ppp < 0.95:
            rec = "Over"
            target = over_est
            st.success(f"📉 BOUNCE BACK: {team_name} is Underperforming.")
            st.subheader(f"🎯 Strategy: Bet OVER {over_est:.1f}")
        else:
            st.info(f"✅ NEUTRAL: {team_name} is at sustainable levels.")
            st.write("No strong betting edge detected.")

        # --- Data Logging to Google Sheets ---
        try:
            # Create row to append
            new_data = pd.DataFrame([{
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Team": team_name,
                "PPP": round(ppp, 3),
                "Points": pts,
                "Possessions": round(possessions, 2),
                "Recommendation": rec,
                "Target Line": target
            }])
            
            # Read existing sheet and append
            existing_df = conn.read()
            updated_df = pd.concat([existing_df, new_data], ignore_index=True)
            conn.update(data=updated_df)
            
            st.toast("Data synced to Google Sheets!", icon="☁️")
        except Exception as e:
            st.warning(f"Note: Could not sync to cloud. (Error: {e})")
            
    else:
        st.error("Possessions cannot be zero. Please check your inputs.")

# --- History View ---
st.divider()
if st.checkbox("Show Recent History"):
    try:
        history = conn.read()
        st.dataframe(history.tail(10), use_container_width=True)
    except:
        st.write("Connect your Google Sheet to see history here.")
