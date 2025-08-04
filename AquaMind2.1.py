import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
from fpdf import FPDF

# ----------------- Telegram Bot Setup -----------------
BOT_TOKEN = 'YOUR_BOT_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

# ----------------- Leak detection threshold -----------------
THRESHOLD = 5  # L/min

# ----------------- Page config -----------------
st.set_page_config(page_title="💧 AquaMind2.0 Dashboard", layout="wide")
st.title("💧 AquaMind2.0 Dashboard")

# ----------------- Load Data -----------------
file_path = r'E:\Hackathon\Small Ai\water_predictions.csv'
try:
    df = pd.read_csv(file_path, parse_dates=['Timestamp'])
except ValueError:
    df = pd.read_csv(file_path)
    st.warning("⚠️ 'Timestamp' column missing in CSV. Loaded without date parsing.")
except Exception as e:
    st.error(f"❌ Failed to load CSV: {e}")
    st.stop()

# ----------------- Feature Engineering -----------------
if 'Timestamp' not in df.columns:
    df['Timestamp'] = pd.date_range(start='2025-01-01', periods=len(df), freq='H')

df['Diff'] = df['Actual_Flow_Rate_L_per_min'].diff().abs()
df['Pred_Diff'] = df['Predicted_Flow_Rate_L_per_min'].diff().abs()

# ----------------- Interactive Simulation Slider -----------------
st.subheader("🎛️ Interactive Simulation")
time_step = st.slider("Select Time Step for Simulation", min_value=0, max_value=len(df)-1, value=len(df)-1)
selected_row = df.iloc[time_step]
latest_diff = selected_row['Diff']
latest_pred_diff = selected_row['Pred_Diff']
timestamp = selected_row['Timestamp']

# ----------------- Notification Tracking -----------------
if 'last_notified_actual' not in st.session_state:
    st.session_state['last_notified_actual'] = None
if 'last_notified_predicted' not in st.session_state:
    st.session_state['last_notified_predicted'] = None

# ----------------- Leak Detection (Actual) -----------------
if latest_diff > THRESHOLD:
    st.error(f"🚨 Leak Detected! Change of {latest_diff:.2f} L/min at {timestamp}.")
    if st.session_state['last_notified_actual'] != str(timestamp):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    'chat_id': CHAT_ID,
                    'text': f"🚨 Leak Detected!\nTime: {timestamp}\nChange: {latest_diff:.2f} L/min.\nCheck immediately."
                }
            )
            if resp.status_code == 200:
                st.success("✅ Telegram notification sent for leak.")
                st.session_state['last_notified_actual'] = str(timestamp)
            else:
                st.warning(f"⚠️ Telegram failed: {resp.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram error: {e}")
else:
    st.success(f"✅ No leaks detected at {timestamp}.")

# ----------------- Leak Detection (Predicted) -----------------
if latest_pred_diff > THRESHOLD:
    st.warning(f"🔮 Potential Leak Predicted! Change of {latest_pred_diff:.2f} L/min at {timestamp}.")
    if st.session_state['last_notified_predicted'] != str(timestamp):
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    'chat_id': CHAT_ID,
                    'text': f"🔮 Potential Leak Predicted!\nTime: {timestamp}\nPredicted Change: {latest_pred_diff:.2f} L/min.\nMonitor closely."
                }
            )
            if resp.status_code == 200:
                st.success("✅ Telegram notification sent for predicted leak.")
                st.session_state['last_notified_predicted'] = str(timestamp)
            else:
                st.warning(f"⚠️ Telegram failed: {resp.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram error: {e}")
else:
    st.info(f"✅ No predicted leaks at {timestamp}.")

# ----------------- Manual Test Notification Button -----------------
st.subheader("📲 Manual Telegram Notification Tester")
if st.button("📤 Send Test Notification to Telegram"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"✅ Test Notification from AquaMind2.0\nTime: {now}\nManual test triggered from dashboard."
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={'chat_id': CHAT_ID, 'text': msg}
        )
        if resp.status_code == 200:
            st.success("✅ Test notification sent successfully!")
        else:
            st.warning(f"⚠️ Failed to send test notification: {resp.text}")
    except Exception as e:
        st.error(f"❌ Telegram error: {e}")

# ----------------- Metrics -----------------
col1, col2, col3 = st.columns(3)
col1.metric("💦 Current Actual Flow Rate", f"{selected_row['Actual_Flow_Rate_L_per_min']:.2f} L/min")
col2.metric("🔮 Predicted Flow Rate", f"{selected_row['Predicted_Flow_Rate_L_per_min']:.2f} L/min")
mae = abs(df['Actual_Flow_Rate_L_per_min'] - df['Predicted_Flow_Rate_L_per_min']).mean()
col3.metric("📉 Model MAE", f"{mae:.2f} L/min")

# ----------------- Plot -----------------
fig = px.line(
    df.iloc[:time_step+1].reset_index(),
    x='Timestamp',
    y=['Actual_Flow_Rate_L_per_min', 'Predicted_Flow_Rate_L_per_min'],
    labels={'value': 'Flow Rate (L/min)', 'Timestamp': 'Time'},
    title="Actual vs Predicted Water Flow Rate",
    color_discrete_map={
        "Actual_Flow_Rate_L_per_min": "#1f77b4",
        "Predicted_Flow_Rate_L_per_min": "#ff7f0e"
    }
)
fig.update_layout(template='plotly_dark', height=500)
st.plotly_chart(fig, use_container_width=True)

# ----------------- Download Option -----------------
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Data as CSV", data=csv, file_name='water_predictions.csv', mime='text/csv')

# ----------------- PDF Generation with Confetti + Telegram Upload -----------------
def generate_pdf(df, selected_row, mae, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(200, 10, txt=f"AquaMind2.0 Dashboard Report - {now}", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Actual Flow Rate: {selected_row['Actual_Flow_Rate_L_per_min']:.2f} L/min", ln=True)
    pdf.cell(200, 10, txt=f"Predicted Flow Rate: {selected_row['Predicted_Flow_Rate_L_per_min']:.2f} L/min", ln=True)
    pdf.cell(200, 10, txt=f"Model MAE: {mae:.2f} L/min", ln=True)
    if selected_row['Diff'] > THRESHOLD:
        pdf.cell(200, 10, txt=f"🚨 Leak Detected!", ln=True)
    else:
        pdf.cell(200, 10, txt=f"✅ No Leak Detected.", ln=True)
    fig.write_image("plot.png")
    pdf.image("plot.png", x=10, w=180)
    filename = "AquaMind2.0_Report.pdf"
    pdf.output(filename)
    return filename

st.subheader("📄 Judge Report Generator")
if st.button("📄 Generate & Send PDF Report"):
    with st.spinner("Generating report..."):
        pdf_file = generate_pdf(df, selected_row, mae, fig)
        with open(pdf_file, "rb") as f:
            st.download_button("📥 Download Report PDF", data=f, file_name=pdf_file, mime="application/pdf")
        st.balloons()
        try:
            files = {'document': open(pdf_file, 'rb')}
            data = {'chat_id': CHAT_ID, 'caption': '📄 AquaMind2.0 Report generated automatically.'}
            resp = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", files=files, data=data)
            if resp.status_code == 200:
                st.success("✅ PDF sent to Telegram for backup!")
            else:
                st.warning(f"⚠️ Telegram upload failed: {resp.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram upload error: {e}")

# ----------------- Footer -----------------
st.markdown("<br>", unsafe_allow_html=True)
st.info("🚀 Project by **Quantum Pulse** | Smart Water AI Dashboard with Leak Detection & Predictive Analytics")
