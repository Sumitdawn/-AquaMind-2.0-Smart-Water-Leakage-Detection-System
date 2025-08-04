import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# Telegram bot details
BOT_TOKEN = '7584048122:AAGEK38sT0qP96MQfAME9biB8AF6pATbzoA'
CHAT_ID = '5482001069'

st.set_page_config(page_title="💧 Smart Water AI Dashboard", layout="wide")
st.title("💧 Smart Water AI Dashboard")

# Load data
df = pd.read_csv(r'E:\Hackathon\Small Ai\water_predictions.csv')

# Leak detection threshold
THRESHOLD = 5  # L/min

# Calculate difference
df['Diff'] = df['Actual_Flow_Rate_L_per_min'].diff().abs()

# ✅ Define latest_diff BEFORE sending notifications
latest_diff = df['Diff'].iloc[-1]

if latest_diff > THRESHOLD:
    st.error(f"🚨 Leak Detected! Sudden change of {latest_diff:.2f} L/min detected.")

    # Send Telegram notification using requests
    try:
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': f"🚨 Leak Detected in Smart Water AI System!\nSudden change detected: {latest_diff:.2f} L/min.\nPlease check immediately."
        }
        response = requests.post(telegram_url, data=payload)
        if response.status_code == 200:
            st.success("✅ Telegram notification sent successfully.")
        else:
            st.warning(f"⚠️ Telegram notification failed: {response.text}")
    except Exception as e:
        st.warning(f"⚠️ Telegram notification error: {e}")

else:
    st.success("✅ No leaks detected. Flow rate is stable.")

# Raw data toggle
with st.expander("🔍 View Raw Data (Optional)"):
    st.dataframe(df.head(), use_container_width=True)

# Metrics
col1, col2, col3 = st.columns(3)
current_actual = df['Actual_Flow_Rate_L_per_min'].iloc[-1]
current_predicted = df['Predicted_Flow_Rate_L_per_min'].iloc[-1]
mae = abs(df['Actual_Flow_Rate_L_per_min'] - df['Predicted_Flow_Rate_L_per_min']).mean()

col1.metric("💦 Current Actual Flow Rate", f"{current_actual:.2f} L/min")
col2.metric("🔮 Predicted Next Hour Flow Rate", f"{current_predicted:.2f} L/min")
col3.metric("📉 Model MAE", f"{mae:.2f} L/min")

# Interactive simulation
st.subheader("🎛️ Interactive Simulation")

time_step = st.slider("Select Time Step for Simulation", min_value=0, max_value=len(df)-1, value=len(df)-1)

st.write(f"Displaying data for time step: {time_step}")

# Plot
fig = px.line(df.iloc[:time_step+1].reset_index(),
              x='index',
              y=['Actual_Flow_Rate_L_per_min', 'Predicted_Flow_Rate_L_per_min'],
              labels={'value': 'Flow Rate (L/min)', 'index': 'Time Step'},
              title="Actual vs Predicted Water Flow Rate",
              color_discrete_map={
                  "Actual_Flow_Rate_L_per_min": "#1f77b4",
                  "Predicted_Flow_Rate_L_per_min": "#ff7f0e"
              })
fig.update_layout(template='plotly_dark', height=500)

st.plotly_chart(fig, use_container_width=True)

# Download button
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Data as CSV", data=csv, file_name='water_predictions.csv', mime='text/csv')

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)
st.info("🚀 Project by **Quantum Pulse** | Smart Water Usage Prediction with Leak Detection for Conservation")
