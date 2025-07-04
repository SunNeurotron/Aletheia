# Aletheia_v3/dashboard/dashboard.py
import math
import os  # For environment variables
from datetime import datetime  # For formatting timestamps

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# --- Configuration ---
# API URL should point to the FastAPI service.
# In Docker Compose, this is 'http://api_service_name:port'.
# The service name is 'api' and port is '8000' as per docker-compose.yml.
API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
# MLFLOW UI URL
MLFLOW_UI_URL = os.getenv("MLFLOW_UI_URL", "http://mlflow:5000")


# --- Page Setup ---
st.set_page_config(
    page_title="Aletheia v3.0: Discovery Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 Aletheia v3.0: AI-Guided Discovery Dashboard (MDU Edition)")
st.markdown(
    f"""
Welcome to the Aletheia platform. Use this dashboard to submit and monitor AI-driven research jobs.
Track your experiments in [MLflow]({MLFLOW_UI_URL}).
"""
)

# --- Session State Initialization ---
# Store submitted job IDs to persist across reruns.
if "submitted_jobs" not in st.session_state:
    st.session_state.submitted_jobs = []  # List of job_ids

# --- Sidebar for Job Submission & Info ---
with st.sidebar:
    st.header("🚀 Submit New Intelligent Job")
    with st.form("search_form"):
        # n_calls corresponds to JobCreateRequest schema in FastAPI
        n_calls = st.slider(
            "Search Budget (AI evaluations)",
            min_value=20,  # Consistent with schema (gt=10)
            max_value=500,  # Consistent with schema (le=1000, but 500 is a more practical UI limit)
            value=50,
            step=10,
            help="Number of evaluations the AI will perform. Higher values mean more thorough search but longer runtime.",
        )
        submitted = st.form_submit_button("Start Intelligent Discovery")

        if submitted:
            payload = {"n_calls": n_calls}
            try:
                # The endpoint is now just /searches (router has no prefix)
                response = requests.post(
                    f"{API_BASE_URL}/searches", json=payload, timeout=10
                )
                if response.status_code == 202:  # HTTP 202 Accepted
                    job_info = response.json()
                    job_id = job_info.get("id")
                    if job_id:
                        # Add to the beginning of the list to show newest first
                        st.session_state.submitted_jobs.insert(0, job_id)
                        st.success(
                            f"Job '{job_id}' submitted successfully! Status: {job_info.get('status')}."
                        )
                    else:
                        st.error(
                            "Submission successful, but no job ID received in response."
                        )
                else:
                    st.error(
                        f"API Error ({response.status_code}): {response.text}"
                    )
            except requests.exceptions.RequestException as e:
                st.error(
                    f"API Connection Error: {e}. Is the API service running at {API_BASE_URL}?"
                )

    st.markdown("---")
    st.header("🔗 Quick Links")
    st.markdown(f"- [**MLflow Experiments**]({MLFLOW_UI_URL})")
    st.markdown(f"- [**API Documentation**]({API_BASE_URL}/docs)")


# --- Main Area for Job Monitoring & Results ---
st.header("📊 Job Monitoring & Results")

if not st.session_state.submitted_jobs:
    st.info(
        "No jobs submitted yet. Use the sidebar to start a new discovery job."
    )
else:
    if st.button("🔄 Refresh All Job Statuses"):
        # This button simply triggers a rerun, which will fetch statuses.
        pass

    # Display jobs, newest first (as they are inserted at index 0)
    for job_id in st.session_state.submitted_jobs:
        try:
            response = requests.get(
                f"{API_BASE_URL}/searches/{job_id}", timeout=10
            )
            if response.status_code == 200:
                job_data = response.json()
                status = job_data.get("status", "Unknown").upper()
                n_calls_job = job_data.get("n_calls", "N/A")
                created_at_raw = job_data.get("created_at")
                created_at_str = (
                    datetime.fromisoformat(created_at_raw).strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                    if created_at_raw
                    else "N/A"
                )

                # Determine expander default state: expand processing or completed jobs
                expanded_default = status in ["PROCESSING", "COMPLETED"]

                with st.expander(
                    f"Job ID: {job_id} | Status: {status} | Created: {created_at_str}",
                    expanded=expanded_default,
                ):
                    st.write(f"**Requested AI Evaluations:** {n_calls_job}")

                    # Display MLflow link for the specific job if available
                    # (Assuming celery worker logs job_id as a tag or param)
                    # This requires constructing the MLflow run URL if possible, or just linking to experiment.
                    # For now, a general link is in sidebar. We can enhance this if MLflow run IDs are easily accessible.
                    # st.markdown(f"[View in MLflow]({MLFLOW_UI_URL}/#/experiments/EXPERIMENT_ID/runs/RUN_ID)")

                    if status == "COMPLETED":
                        hits = job_data.get("hits", [])
                        if hits:
                            st.subheader(f"🏆 Discovered Hits ({len(hits)})")

                            # Prepare data for DataFrame and Plot
                            df_hits = pd.DataFrame(hits)
                            # Select and rename columns for better display
                            df_display = df_hits[
                                ["a", "b", "c", "quality"]
                            ].copy()
                            df_display.rename(
                                columns={"quality": "Quality (q)"},
                                inplace=True,
                            )
                            st.dataframe(df_display)

                            # Plotting results
                            # Using log10(c) for x-axis can spread out points if c varies a lot.
                            # Ensure 'c' is positive before log.
                            valid_hits_for_plot = [
                                h for h in hits if h.get("c", 0) > 0
                            ]
                            if valid_hits_for_plot:
                                log_c_values = [
                                    math.log10(h["c"])
                                    for h in valid_hits_for_plot
                                ]
                                qualities = [
                                    h["quality"] for h in valid_hits_for_plot
                                ]
                                hover_texts = [
                                    f"a={h['a']}, b={h['b']}, c={h['c']}<br>q={h['quality']:.4f}"
                                    for h in valid_hits_for_plot
                                ]

                                fig = go.Figure(
                                    data=[
                                        go.Scatter(
                                            x=log_c_values,
                                            y=qualities,
                                            mode="markers",
                                            marker=dict(
                                                size=10,
                                                color=qualities,
                                                colorscale="Viridis",
                                                showscale=True,
                                                colorbar=dict(
                                                    title="Quality (q)"
                                                ),
                                            ),
                                            text=hover_texts,
                                            hoverinfo="text",
                                        )
                                    ]
                                )
                                fig.update_layout(
                                    title="Discovery Results: Quality vs. Magnitude of c",
                                    xaxis_title="Magnitude (log10(c))",
                                    yaxis_title="Quality (q)",
                                    height=500,
                                )
                                st.plotly_chart(fig, use_container_width=True)

                                # New 3D Scatter Plot
                                st.subheader("Hits in 3D Space (a, b, c)")
                                fig_3d = go.Figure(
                                    data=[
                                        go.Scatter3d(
                                            x=[
                                                h["a"]
                                                for h in valid_hits_for_plot
                                            ],
                                            y=[
                                                h["b"]
                                                for h in valid_hits_for_plot
                                            ],
                                            z=[
                                                h["c"]
                                                for h in valid_hits_for_plot
                                            ],
                                            mode="markers",
                                            marker=dict(
                                                size=5,
                                                color=[
                                                    h["quality"]
                                                    for h in valid_hits_for_plot
                                                ],
                                                colorscale="Viridis",  # Same colorscale for consistency
                                                colorbar=dict(
                                                    title="Quality (q)"
                                                ),
                                                opacity=0.8,
                                            ),
                                            text=[
                                                f"a={h['a']}, b={h['b']}, c={h['c']}<br>q={h['quality']:.4f}"
                                                for h in valid_hits_for_plot
                                            ],
                                            hoverinfo="text",
                                        )
                                    ]
                                )
                                fig_3d.update_layout(
                                    title="3D Scatter of Hits (a, b, c) Colored by Quality",
                                    scene=dict(
                                        xaxis_title="Component 'a'",
                                        yaxis_title="Component 'b'",
                                        zaxis_title="Component 'c' (a+b)",
                                        aspectmode="cube",  # Or 'data', 'auto'
                                    ),
                                    margin=dict(
                                        r=0, b=0, l=0, t=40
                                    ),  # Adjust margins
                                    height=600,
                                )
                                st.plotly_chart(
                                    fig_3d, use_container_width=True
                                )

                            else:
                                st.info(
                                    "Hits found, but 'c' values are not suitable for plotting."
                                )
                        else:
                            st.info(
                                "Job completed, but no new high-quality hits were found in this run."
                            )

                        st.markdown(
                            "---"
                        )  # Separator before next section within expander
                        st.subheader("Factor Analysis (Conceptual)")
                        st.info(
                            """
                            **Future Enhancement:** This section will provide insights into the prime factorization of discovered hits.
                            For example:
                            - Distribution of the number of distinct prime factors of `a*b*c`.
                            - Relationship between `rad(abc)` and `c`. (Currently visualized by quality `q`).
                            - Identification of hits where `a`, `b`, or `c` are perfect powers.

                            Implementing efficient prime factorization for many large numbers directly in the dashboard
                            can be computationally intensive. This data might be pre-calculated by worker tasks
                            or analyzed via dedicated data processing jobs in future versions.
                            The `is_c_perfect_power_naive` in the Dask example (`docs/DASK_INTEGRATION.md`) shows a conceptual direction.
                        """
                        )

                    elif status == "PROCESSING":
                        st.info(
                            "Job is currently processing. Refresh to see updates."
                        )
                    elif status == "PENDING":
                        st.info(
                            "Job is pending and will be picked up by a worker soon."
                        )
                    elif status == "FAILED" or "ERROR" in status:
                        st.error(
                            f"Job encountered an error. Status: {status}. Check API logs or MLflow for details."
                        )

            elif response.status_code == 404:
                st.error(
                    f"Job ID '{job_id}' not found in the system. It might have been an invalid ID or an issue occurred."
                )
                # Optionally, remove invalid ID from session state
                # st.session_state.submitted_jobs.remove(job_id)
            else:
                st.warning(
                    f"Could not retrieve status for job {job_id}. API responded with {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to API for job {job_id}: {e}")
        except (
            Exception
        ) as e:  # Catch any other unexpected errors during rendering
            st.error(
                f"An unexpected error occurred while displaying job {job_id}: {e}"
            )

# --- Footer ---
st.markdown("---")
st.markdown(
    f"<p align='center'>Aletheia Platform v3.0 (MDU Edition) | Current API: {API_BASE_URL}</p>",
    unsafe_allow_html=True,
)
