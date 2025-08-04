import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# ----------------- Telegram Bot Setup -----------------
BOT_TOKEN = '7584048122:AAGEK38sT0qP96MQfAME9biB8AF6pATbzoA'
CHAT_ID = '5482001069'


# ----------------- Leak detection threshold -----------------
THRESHOLD = 5  # L/min

# ----------------- Page config -----------------
st.set_page_config(page_title="💧 AquaMind AI Dashboard", layout="wide")
#st.title("💧 Smart Water AI Dashboard")
st.title("💧  AquaMind AI Dashboard")

# ----------------- Load Data Safely -----------------
file_path = r'E:\Hackathon\Small Ai\water_predictions.csv'
try:
    df = pd.read_csv(file_path, parse_dates=['Timestamp'])
except ValueError:
    df = pd.read_csv(file_path)
    st.warning("⚠️ 'Timestamp' column missing in CSV. Loaded without date parsing. Check your CSV headers.")
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
time_step = st.slider("Select Time Step for Simulation", min_value=0, max_value=len(df) - 1, value=len(df) - 1)
st.write(f"Displaying data for time step: {time_step}")

selected_row = df.iloc[time_step]
latest_diff = selected_row['Diff']
latest_pred_diff = selected_row['Pred_Diff']
timestamp = selected_row['Timestamp']

# ----------------- Notification Tracking -----------------
if 'last_notified_timestamp_actual' not in st.session_state:
    st.session_state['last_notified_timestamp_actual'] = None

if 'last_notified_timestamp_predicted' not in st.session_state:
    st.session_state['last_notified_timestamp_predicted'] = None

# ----------------- Leak Detection (Actual) -----------------
if latest_diff > THRESHOLD:
    st.error(f"🚨 Leak Detected! Sudden change of {latest_diff:.2f} L/min at {timestamp}.")
    if st.session_state['last_notified_timestamp_actual'] != str(timestamp):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    'chat_id': CHAT_ID,
                    'text': f"🚨 Leak Detected!\nTime: {timestamp}\nChange: {latest_diff:.2f} L/min.\nCheck immediately."
                }
            )
            if response.status_code == 200:
                st.success("✅ Telegram notification sent for actual leak.")
                st.session_state['last_notified_timestamp_actual'] = str(timestamp)
            else:
                st.warning(f"⚠️ Telegram notification failed: {response.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram error: {e}")
else:
    st.success(f"✅ No leaks detected at {timestamp}. Flow rate stable.")

# ----------------- Leak Detection (Predicted) -----------------
if latest_pred_diff > THRESHOLD:
    st.warning(f"🔮 Potential Leak Predicted! Change of {latest_pred_diff:.2f} L/min at {timestamp}.")
    if st.session_state['last_notified_timestamp_predicted'] != str(timestamp):
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={
                    'chat_id': CHAT_ID,
                    'text': f"🔮 Potential Future Leak Detected!\nTime: {timestamp}\nPredicted change: {latest_pred_diff:.2f} L/min.\nMonitor closely."
                }
            )
            if response.status_code == 200:
                st.success("✅ Telegram notification sent for predicted leak.")
                st.session_state['last_notified_timestamp_predicted'] = str(timestamp)
            else:
                st.warning(f"⚠️ Telegram notification failed: {response.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram error: {e}")
else:
    st.info(f"✅ No sudden predicted changes detected at {timestamp}.")

# ----------------- Send Custom Telegram Notification Button -----------------
st.subheader("📲 Manual Telegram Notification Tester")

if st.button("📤 Send Test Notification to Telegram"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_message = f"✅ Test Notification from AquaMind2.0\nTime: {now}\nManual test initiated from dashboard."
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                'chat_id': CHAT_ID,
                'text': test_message
            }
        )
        if response.status_code == 200:
            st.success("✅ Test notification sent to Telegram successfully.")
        else:
            st.warning(f"⚠️ Failed to send test notification: {response.text}")
    except Exception as e:
        st.error(f"❌ Telegram error: {e}")

# ----------------- Metrics -----------------
col1, col2, col3 = st.columns(3)
col1.metric("💦 Current Actual Flow Rate", f"{selected_row['Actual_Flow_Rate_L_per_min']:.2f} L/min")
col2.metric("🔮 Predicted Next Hour Flow Rate", f"{selected_row['Predicted_Flow_Rate_L_per_min']:.2f} L/min")
mae = abs(df['Actual_Flow_Rate_L_per_min'] - df['Predicted_Flow_Rate_L_per_min']).mean()
col3.metric("📉 Model MAE", f"{mae:.2f} L/min")

# ----------------- Plot -----------------
fig = px.line(
    df.iloc[:time_step + 1].reset_index(),
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

# ----------------- Raw Data Viewer -----------------
with st.expander("🔍 View Raw Data"):
    st.dataframe(df.head(), use_container_width=True)

# ----------------- Download Option -----------------
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", data=csv, file_name='water_predictions.csv', mime='text/csv')

# ----------------- Footer -----------------
st.markdown("<br><br>", unsafe_allow_html=True)
st.info("🚀 Project by **Quantum Pulse** | Smart Water Usage Prediction with Leak Detection for Conservation")

from fpdf import FPDF
from datetime import datetime
import matplotlib.pyplot as plt
import io
import requests

# PDF generation function with Telegram auto-upload
def generate_pdf_report(df, selected_row, mae, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="AquaMind2.0 Dashboard Report", ln=True, align='C')
    pdf.ln(5)

    # Timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Generated on: {now}", ln=True, align='L')
    pdf.ln(5)

    # Current Metrics
    pdf.cell(200, 10, txt=f"Current Actual Flow Rate: {selected_row['Actual_Flow_Rate_L_per_min']:.2f} L/min", ln=True)
    pdf.cell(200, 10, txt=f"Predicted Next Hour Flow Rate: {selected_row['Predicted_Flow_Rate_L_per_min']:.2f} L/min", ln=True)
    pdf.cell(200, 10, txt=f"Model MAE: {mae:.2f} L/min", ln=True)
    pdf.ln(5)

    # Leak detection status
    if selected_row['Diff'] > THRESHOLD:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(200, 10, txt=f"🚨 Leak Detected! Change of {selected_row['Diff']:.2f} L/min at {selected_row['Timestamp']}.", ln=True)
    else:
        pdf.set_text_color(0, 128, 0)
        pdf.cell(200, 10, txt=f"✅ No leak detected at {selected_row['Timestamp']}.", ln=True)
    pdf.set_text_color(0, 0, 0)

    # Save plot image using kaleido
    fig.write_image("dashboard_plot.png")

    # Insert image
    pdf.ln(5)
    pdf.image("dashboard_plot.png", x=10, w=180)

    # Footer
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="🚀 Project by Quantum Pulse | Smart Water AI Dashboard", ln=True, align='C')

    # Save PDF
    pdf_output = "AquaMind2_Dashboard_Report.pdf"
    pdf.output(pdf_output)

    return pdf_output

# --- Streamlit Button with confetti and auto-upload ---
if st.button("📄 Generate PDF Report for Judges"):
    with st.spinner("Generating PDF report..."):
        pdf_file = generate_pdf_report(df, selected_row, mae, fig)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📥 Download AquaMind2.0 Dashboard Report PDF",
                data=f,
                file_name="AquaMind2_Dashboard_Report.pdf",
                mime="application/pdf"
            )
        # 🎉 Confetti
        st.balloons()

        # Telegram upload
        try:
            files = {'document': open(pdf_file, 'rb')}
            telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
            payload = {'chat_id': CHAT_ID, 'caption': '📄 AquaMind2.0 Dashboard Report generated and backed up automatically.'}
            response = requests.post(telegram_url, files=files, data=payload)
            if response.status_code == 200:
                st.success("✅ PDF sent to Telegram for backup!")
            else:
                st.warning(f"⚠️ Telegram upload failed: {response.text}")
        except Exception as e:
            st.warning(f"⚠️ Telegram upload error: {e}")
