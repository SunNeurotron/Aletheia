import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import math

st.set_page_config(page_title="ABC Discovery Dashboard", page_icon="🔬", layout="wide")
st.title("🔬 ABC Intelligent Discovery Dashboard")

API_URL = "http://api:8000"
if 'submitted_jobs' not in st.session_state: st.session_state.submitted_jobs = []

with st.sidebar:
    st.header("🚀 Submit New Intelligent Job")
    with st.form("search_form"):
        n_calls = st.slider("Search Budget (AI evaluations)", min_value=20, max_value=200, value=50)
        submitted = st.form_submit_button("Start Intelligent Discovery")
        if submitted:
            try:
                response = requests.post(f"{API_URL}/searches", json={"n_calls": n_calls})
                if response.status_code == 202:
                    job_id = response.json().get("job_id")
                    st.session_state.submitted_jobs.insert(0, job_id)
                    st.success(f"Job {job_id} submitted!")
                else: st.error(f"Error: {response.text}")
            except requests.exceptions.ConnectionError: st.error("API connection failed.")

st.header("📊 Job Monitoring & Results")
if not st.session_state.submitted_jobs: st.info("No jobs submitted yet.")
else:
    if st.button("🔄 Refresh Statuses"): pass
    for job_id in st.session_state.submitted_jobs:
        try:
            response = requests.get(f"{API_URL}/searches/{job_id}")
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status")
                with st.expander(f"Job ID: {job_id} | Status: {status.upper()}", expanded=True):
                    st.write(f"**AI Evaluations:** {job_data.get('n_calls')}")
                    if status == "completed":
                        hits = job_data.get("hits", [])
                        if hits:
                            st.dataframe(pd.DataFrame(hits))
                            fig = go.Figure(data=go.Scatter(x=[math.log10(h['c']) for h in hits],y=[h['quality'] for h in hits],mode='markers',text=[f"q={h['quality']:.4f}" for h in hits]))
                            fig.update_layout(title="Discovery Results", xaxis_title="Magnitude (log10(c))", yaxis_title="Quality (q)")
                            st.plotly_chart(fig, use_container_width=True)
                        else: st.info("Job completed with no new high-quality hits.")
        except: st.error(f"Could not retrieve status for job {job_id}.")
