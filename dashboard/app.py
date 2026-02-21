import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="Healthcare Analytics Dashboard",
    layout="wide",
)

# --------------------------
# SIDEBAR
# --------------------------
st.sidebar.title("🏥 Healthcare Analytics")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Provider Analytics", "Appointment Trends", "Readmission Analysis"]
)

# --------------------------
# HEADER
# --------------------------
st.markdown('<h1 style="color: blue;">🏥 Healthcare Provider Analytics Platform</h1>', unsafe_allow_html=True)
st.markdown("---")

# --------------------------
# OVERVIEW PAGE
# --------------------------
if page == "Overview":

    response = requests.get(f"{BASE_URL}/providers")

    if response.status_code == 200:
        providers = response.json()
    else:
        st.error(f"API Error: {response.status_code}")
        st.write(response.text)
        providers = []

    appointments = requests.get(f"{BASE_URL}/appointments/analytics").json()
    readmissions = requests.get(f"{BASE_URL}/readmissions/rates").json()

    df_providers = pd.DataFrame(providers)
    df_appointments = pd.DataFrame(appointments)
    df_readmissions = pd.DataFrame(readmissions)

     # ---------------- KPI CARDS ----------------
    with st.container():
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            label="👨‍⚕️ Total Providers",
            value=len(df_providers),
            delta=f"{len(df_providers) * 0.05:.0f}%",  # example delta
        )
        col2.metric(
            label="📅 Total Appointments",
            value=df_appointments["total_appointments"].sum(),
            delta=f"{df_appointments['total_appointments'].sum() * 0.03:.0f}%",
        )
        col3.metric(
            label="🏥 Avg Readmission Rate",
            value=f"{round(df_readmissions['readmission_rate'].mean(), 2)}%",
            delta=f"{round(df_readmissions['readmission_rate'].mean() * -0.02, 2)}%",  # negative delta as improvement
        )
        col4.metric(
            label="💉 Total Encounter Types",
            value=df_appointments["encounter_type"].nunique(),
        )

    st.markdown('<h3 style="color:red;">📊 Appointments Trend</h3>', unsafe_allow_html=True)

    # Convert month_year to datetime for better x-axis handling
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )

    # Create the line chart
    fig = px.line(
        df_appointments,
        x="month_year",
        y="total_appointments",
        color="encounter_type",
        markers=True,
        title="Appointments Trend"
    )

   # Set y-axis from 0 to 50 with ticks every 10
    fig.update_yaxes(range=[0, 50], dtick=10)

    # Optional: make x-axis show years clearly
    fig.update_xaxes(
        tickformat="%Y",
        dtick="M120"  # roughly every 10 years
    )

    # Display chart
    st.plotly_chart(fig, use_container_width=True)

    # Box Plot: Distribution per Encounter Type
    st.markdown('<h3 style="color:red;">📦 Distribution of Appointments per Encounter Type</h3>', unsafe_allow_html=True)

    fig_box = px.box(
        df_appointments,
        x="encounter_type",
        y="total_appointments",
        color="encounter_type",
        title="Appointment Distribution by Encounter Type",
        template="plotly_white",
        color_discrete_sequence=px.colors.sequential.Bluered
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.markdown('<h3 style="color:red;">🔥 Appointments Heatmap</h3>', unsafe_allow_html=True)

    df_heat = df_appointments.groupby(["year", "month"])["total_appointments"].sum().reset_index()
    fig_heat = px.density_heatmap(
        df_heat,
        x="month",
        y="year",
        z="total_appointments",
        title="Monthly Appointments Heatmap",
        color_continuous_scale="Viridis",
        template="plotly_white"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown('<h3 style="color:red;">📊 Appointment Frequency Histogram</h3>', unsafe_allow_html=True)

    fig_hist = px.histogram(
        df_appointments,
        x="total_appointments",
        nbins=20,
        color="encounter_type",
        title="Distribution of Appointment Counts",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    # Set x-axis from 0 to 50 with ticks every 10
    fig_hist.update_xaxes(range=[0, 50], dtick=10)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown('<h3 style="color:red;">🥧 Encounter Type Distribution</h3>', unsafe_allow_html=True)
    df_pie = df_appointments.groupby("encounter_type")["total_appointments"].sum().reset_index()
    fig_pie = px.pie(
        df_pie,
        names="encounter_type",
        values="total_appointments",
        title="Appointment Share by Encounter Type",
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    # Increase chart size and font
    fig_pie.update_layout(
        title_font_size=30,      # larger title
        legend_font_size=16,     # larger legend
        font=dict(size=14),      # labels inside chart
        height=400,              # taller chart
        width=700                # wider chart
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Optional: display raw data
    st.dataframe(df_appointments)

# --------------------------
# PROVIDER ANALYTICS
# --------------------------
elif page == "Provider Analytics":

    try:
        providers = requests.get(f"{BASE_URL}/providers").json()
        df = pd.DataFrame(providers)
    except Exception as e:
        st.error(f"Could not load provider data: {e}")
        df = pd.DataFrame()

    st.markdown('<h3 style="color:red;">👨‍⚕️ Provider Productivity</h3>', unsafe_allow_html=True)

    search = st.text_input("Search Provider")

    if search:
        df = df[df["provider_name"].str.contains(search, case=False)]

    # Only create chart if total_appointments column exists
    if "total_appointments" in df.columns:
        fig = px.bar(
            df,
            x="provider_name",
            y="total_appointments",
            color="total_appointments",
            title="Appointments by Provider"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df)

# --------------------------
# APPOINTMENT ANALYTICS
# --------------------------
elif page == "Appointment Trends":

    data = requests.get(f"{BASE_URL}/appointments/analytics").json()
    df_appointments = pd.DataFrame(data)

    st.markdown('<h3 style="color:red;">📅 Appointment Trends</h3>', unsafe_allow_html=True)

    # Assume df_appointments is your DataFrame
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )

    # Filter out months with 0 appointments
    df_nonzero = df_appointments[df_appointments["total_appointments"] > 0]

    # Sort by month_year
    df_nonzero = df_nonzero.sort_values("year")

    # Plot the chart
    fig = px.line(
        df_nonzero,
        x="month_year",
        y="total_appointments",
        color="encounter_type",
        markers=True,
        title="Appointments Trend (Non-zero Years Only)",
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )

    # Optional: rotate x-axis for readability
    fig.update_layout(xaxis_tickangle=-45)

    # Set y-axis range 0–100 with ticks every 10
    fig.update_yaxes(range=[0, 100], dtick=10)

    st.plotly_chart(fig, use_container_width=True)

    # --- Preprocess ---
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )

    # Filter relevant data
    df_filtered = df_appointments[
        (df_appointments["year"] >= 2015) &
        (df_appointments["year"] <= 2020) &
        (df_appointments["total_appointments"] > 0)
    ]

    # Aggregate by month_year and encounter_type
    df_grouped = df_filtered.groupby(["month_year", "encounter_type"])["total_appointments"].sum().reset_index()

    # Pivot table for stacked bar
    df_pivot = df_grouped.pivot(index="month_year", columns="encounter_type", values="total_appointments").fillna(0)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(15,9))

    # Use stacked bar
    df_pivot.plot(kind="bar", stacked=True, ax=ax, width=0.8, colormap="tab20")

    # Reduce x-axis ticks to 1 per year to avoid clutter
    tick_positions = [i for i in range(0, len(df_pivot), 12)]
    tick_labels = [d.strftime("%b-%Y") for i,d in enumerate(df_pivot.index) if i % 12 == 0]

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=45, ha="right")

    # Labels and title
    ax.set_xlabel("Month-Year")
    ax.set_ylabel("Total Appointments")
    ax.set_title("Appointments Trend (2015 - 2020) - Stacked Bar Plot")

    # Legend outside the plot
    ax.legend(title="Encounter Type", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()

    # Display in Streamlit
    st.pyplot(fig)

    st.markdown('<h3 style="color:red;">📈 Cumulative Appointments Over Time</h3>', unsafe_allow_html=True)

    df_cum = df_nonzero.groupby("month_year")["total_appointments"].sum().cumsum().reset_index()

    fig_cum = px.line(
        df_cum,
        x="month_year",
        y="total_appointments",
        title="Cumulative Appointments Trend",
        template="plotly_white",
        markers=True
    )
    fig_cum.update_yaxes(title="Cumulative Appointments")
    fig_cum.update_xaxes(title="Month-Year")
    st.plotly_chart(fig_cum, use_container_width=True)

    # Optional: show raw data
    st.dataframe(df_appointments)

# --------------------------
# READMISSION ANALYSIS
# --------------------------
elif page == "Readmission Analysis":

    data = requests.get(f"{BASE_URL}/readmissions/rates").json()
    df = pd.DataFrame(data)

    st.markdown('<h3 style="color:red;">🏥 Readmission Rates by Hospital</h3>', unsafe_allow_html=True)

    fig = px.bar(
        df,
        x="hospital_name",
        y="readmission_rate",
        color="readmission_rate",
        title="Hospital Readmission Comparison"
    )

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df)

st.markdown("---")
st.caption("Built with FastAPI + BigQuery + Streamlit")