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

    response = requests.get(f"{BASE_URL}/appointments/analytics")
    try:
        appointments = response.json()
    except requests.exceptions.JSONDecodeError:
        st.error("Failed to load appointment analytics. Response is not valid JSON.")
        st.write("Response content:", response.text)
        appointments = []
    
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
            label="💉 Total Encounter Classes",  # Updated label
            value=df_appointments["encounter_class"].nunique(),  # use encounter_class
        )

    # Convert month_year to datetime for better x-axis handling
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )

    # Filter for years 2015 to 2019
    df_filtered = df_appointments[(df_appointments["year"] >= 2015) & (df_appointments["year"] <= 2019)]

    # Create the line chart
    fig = px.line(
        df_filtered,
        x="month_year",
        y="total_appointments",
        color="encounter_class",
        markers=True,
        title="📊 Appointments Trend (2015 - 2020)"
    )

    # Set y-axis from 0 to 50 with ticks every 10
    fig.update_yaxes(range=[0, 75], dtick=15)

    # Optional: make x-axis show years clearly
    fig.update_xaxes(
        tickformat="%Y",
        dtick="M12"  # roughly every year
    )

    # Display chart
    st.plotly_chart(fig, use_container_width=True)

    df_heat = df_appointments.groupby(["year", "month"])["total_appointments"].sum().reset_index()
    fig_heat = px.density_heatmap(
        df_heat,
        x="month",
        y="year",
        z="total_appointments",
        title="🔥 Monthly Appointments Heatmap",
        color_continuous_scale="Viridis",
        template="plotly_white"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Group and sort
    if "encounter_class" in df_appointments.columns:
        df_pie = df_appointments.groupby("encounter_class")["total_appointments"].sum().reset_index()
        df_pie = df_pie.sort_values("total_appointments", ascending=False)
    else:
        st.warning("'encounter_class' column not found. Showing total by speciality instead.")
        df_pie = df_appointments.groupby("speciality")["total_appointments"].sum().reset_index()
    df_pie = df_pie.sort_values("total_appointments", ascending=False)

    # Keep Top 5
    top_n = 5
    df_top = df_pie.head(top_n)
    df_others = df_pie.iloc[top_n:]

    # Combine others
    if not df_others.empty:
        others_sum = df_others["total_appointments"].sum()
        df_top = pd.concat([
            df_top,
            pd.DataFrame([{
                "encounter_class": "Others",
                "total_appointments": others_sum
            }])
        ])

    # Create pie chart
    fig_pie = px.pie(
        df_top,
        names="encounter_class",
        values="total_appointments",
        title="🥧 Top Encounter Classes (Others Combined)",
    )

    fig_pie.update_traces(textinfo='percent+label')
    fig_pie.update_layout(height=450)

    st.plotly_chart(fig_pie, use_container_width=True)

        

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

    # --------------------------
    # 📊 KPI Metrics
    # --------------------------
    st.markdown('<h3 style="color: red;">📈 Key Metrics</h3>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👨‍⚕️ Total Providers", df["provider_name"].nunique())
    col2.metric("📅 Total Encounters", df["total_encounters"].sum() if "total_encounters" in df.columns else 0)
    col3.metric("🧑‍🤝‍🧑 Unique Patients", df["unique_patients"].sum() if "unique_patients" in df.columns else 0)
    total_revenue = df['total_revenue'].sum() if "total_revenue" in df.columns else 0
    total_revenue_million = total_revenue / 1_000_000
    col4.metric(
        label="💰 Total Revenue (Million $)", 
        value=f"${total_revenue_million:,.2f}M"
    )

    # --------------------------
    # 📊 Visualizations
    # --------------------------

    # 1️⃣ Total Encounters by Provider (Top 10)
    top10_df = df.sort_values("total_encounters", ascending=False).head(10)

    fig1 = px.bar(
        top10_df,
        y="provider_name",
        x="total_encounters",
        color="total_encounters",
        orientation="h",
        hover_data=["unique_patients", "total_revenue", "avg_encounter_duration_hrs"],
        title="🧑‍⚕️ Top 10 Providers by Total Encounters"
    )
    fig1.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=500
    )
    st.plotly_chart(fig1, use_container_width=True)

    # 2️⃣ Revenue by Provider (Top 10)
    top10_revenue = df.sort_values("total_revenue", ascending=False).head(10)

    fig2 = px.bar(
        top10_revenue,
        y="provider_name",
        x="total_revenue",
        color="total_revenue",
        orientation="h",
        hover_data=["total_encounters", "avg_cost_per_encounter"],
        title="💵  Top 10 Providers by Revenue",
        color_continuous_scale="Viridis"  # Different color scale for better visualization
    )
    fig2.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=500
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 3️⃣ Average Encounter Duration (Top 10)
    top10_enc = df.sort_values("total_encounters", ascending=False).head(10)

    fig_enc = px.bar(
        top10_enc,
        y="provider_name",
        x=["total_encounters", "unique_patients"],  # Stacked
        orientation="h",
        title="🚹 Total Encounters and Unique Patients by Provider",
        text_auto=True
    )
    fig_enc.update_layout(yaxis={'categoryorder':'total ascending'}, barmode='stack', height=500)
    st.plotly_chart(fig_enc, use_container_width=True)

    # Remove unwanted columns safely
    columns_to_drop = ["provider_id", "organization", "organization_id","provider_key","total_encounters","unique_patients","avg_cost_per_encounter","total_revenue","avg_cost_per_encounter","avg_encounter_duration_hrs"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])

    # Add first_encounter and last_encounter columns (if they exist in data)
    if "first_encounter" in df.columns:
        df["first_encounter"] = pd.to_datetime(df["first_encounter"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    if "last_encounter" in df.columns:
        df["last_encounter"] = pd.to_datetime(df["last_encounter"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    st.markdown('<h3 style="color:red;">👨‍⚕️ Provider Productivity</h3>', unsafe_allow_html=True)

    # 🔍 Search Box
    search = st.text_input("Search Provider")

    if search:
        df = df[df["provider_name"].str.contains(search, case=False, na=False)]

    # --------------------------
    # 📊 Chart Section
    # --------------------------
    if "total_appointments" in df.columns:
        fig = px.bar(
            df.sort_values("total_appointments", ascending=False),
            y="provider_name",
            x="total_appointments",
            color="total_appointments",
            orientation="h",
            hover_data=["first_encounter", "last_encounter"],
            title="Appointments by Provider"
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    # --------------------------
    # 📋 Table Section (Normal Table)
    # --------------------------
    st.dataframe(df)  # Streamlit's normal, interactive table
    
# --------------------------
# APPOINTMENT ANALYTICS
# --------------------------
elif page == "Appointment Trends":

    data = requests.get(f"{BASE_URL}/appointments/analytics").json()
    df_appointments = pd.DataFrame(data)
    
    st.markdown('<h3 style="color:red;">📅 Appointment Trends Dashboard</h3>', unsafe_allow_html=True)

     # --- Fetch KPIs ---
    try:
        summary_data = requests.get(f"{BASE_URL}/appointments/summary").json()
        summary = summary_data[0] if isinstance(summary_data, list) and len(summary_data) > 0 else {}
    except:
        summary = {}

    # --- Fetch Reasons ---
    try:
        reasons_data = requests.get(f"{BASE_URL}/appointments/reasons").json()
        if isinstance(reasons_data, dict):
            reasons_data = [reasons_data]
    except:
        reasons_data = []

    col1, col2, col3, col4, col5 = st.columns(5)

    def format_k_m(num):
        if num >= 1_000_000:
            return f"{num/1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num/1_000:.2f}K"
        return str(num)

    col1.metric("📅 Total Encounters", format_k_m(summary.get("total_encounters",0)))
    col2.metric("🧑‍🤝‍🧑 Unique Patients", format_k_m(summary.get("unique_patients",0)))
    col3.metric("👨‍⚕️ Unique Providers", format_k_m(summary.get("unique_providers",0)))
    col4.metric("⏱ Avg Duration (hrs)", f"{summary.get('avg_duration',0):.2f}")
    col5.metric("💰 Total Cost ($)", f"{summary.get('total_cost',0)/1_000_000:.2f}M")

    
    # Convert month_year to datetime for better x-axis handling
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )
    
    # Filter out months with 0 appointments
    df_nonzero = df_appointments[df_appointments["total_appointments"] > 0]
    
    # Filter for years 2000 to 2020
    df_nonzero = df_nonzero[(df_nonzero["year"] >= 2000) & (df_nonzero["year"] <= 2020)]
    
    # Sort by month_year
    df_nonzero = df_nonzero.sort_values("month_year")
    
    # --- Preprocess ---
    df_appointments["month_year"] = pd.to_datetime(
        df_appointments["year"].astype(str) + "-" + df_appointments["month"].astype(str) + "-01"
    )

    # Filter relevant data
    df_filtered = df_appointments[
        (df_appointments["year"] >= 2017) &
        (df_appointments["year"] <= 2020) &
        (df_appointments["total_appointments"] > 0)
    ]

    # Aggregate by month_year and encounter_type
    df_grouped = df_filtered.groupby(["month_year", "encounter_class"])["total_appointments"].sum().reset_index()
    
    # Pivot table for stacked bar
    df_pivot = df_grouped.pivot(index="month_year", columns="encounter_class", values="total_appointments").fillna(0)
    
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
    ax.legend(title="Encounter Class", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()

    # Display in Streamlit
    st.pyplot(fig)

    df_cum = df_nonzero.groupby("month_year")["total_appointments"].sum().cumsum().reset_index()

    fig_cum = px.line(
        df_cum,
        x="month_year",
        y="total_appointments",
        title="📈 Cumulative Appointments Trend",
        template="plotly_white",
        markers=True
    )
    fig_cum.update_yaxes(title="Cumulative Appointments")
    fig_cum.update_xaxes(title="Month-Year")
    st.plotly_chart(fig_cum, use_container_width=True)

    df_reasons = pd.DataFrame(reasons_data)
    for col in ["reason_code", "reason_description", "total_appointments", "unique_patients", "total_cost"]:
        if col not in df_reasons.columns:
            df_reasons[col] = 0

    if not df_reasons.empty:
        fig_reason = px.bar(
            df_reasons.sort_values("total_appointments", ascending=False).head(10),
            x="reason_description",
            y="total_appointments",
            color="total_appointments",
            title="🧪 Top 10 Reasons for Appointments",
            template="plotly_white"
        )
        fig_reason.update_xaxes(tickangle=-45)
        # Set y-axis range 0–1000 with tick every 100
        fig_reason.update_yaxes(range=[0, 1000], dtick=100)

        st.plotly_chart(fig_reason, use_container_width=True)
    else:
        st.warning("No appointment reasons available.")


    df_reason_cost = df_reasons.sort_values("total_appointments", ascending=False).head(10)
    df_melt = df_reason_cost.melt(id_vars=["reason_description"], value_vars=["total_appointments", "total_cost"],
                                  var_name="metric", value_name="value")

    fig = px.bar(
        df_melt,
        x="reason_description",
        y="value",
        color="metric",
        barmode="group",
        text="value",
        title="Top 10 Appointment Reasons: Count vs Cost",
        template="plotly_white"
    )
    fig.update_xaxes(tickangle=-45)
    # Set y-axis range up to 150k
    fig.update_yaxes(range=[0, 150000])
    st.plotly_chart(fig, use_container_width=True)

    df_duration = df_appointments.groupby("encounter_class").agg(
    avg_duration=("avg_duration", "mean"),
    total_appointments=("total_appointments", "sum")
    ).reset_index()

    fig_duration = px.scatter(
        df_duration,
        x="total_appointments",
        y="avg_duration",
        size="total_appointments",
        color="encounter_class",
        hover_name="encounter_class",
        title="Average Duration vs Total Appointments by Encounter Class",
        template="plotly_white"
    )
    st.plotly_chart(fig_duration, use_container_width=True)

# --------------------------
# READMISSION ANALYSIS
# --------------------------
elif page == "Readmission Analysis":

    data = requests.get(f"{BASE_URL}/readmissions/rates").json()
    df = pd.DataFrame(data)

    # --------------------------
    # 🏥 Readmission KPI Metrics
    # --------------------------
    st.markdown('<h2 style="color:darkred;">🏥 Readmission Analysis Dashboard</h2>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    # Total Hospitals
    col1.metric(
        label="🏨 Total Hospitals",
        value=f"{df['hospital_name'].nunique()}" if "hospital_name" in df.columns else "0"
    )

    # Average Readmission Rate
    avg_rate = df['readmission_rate'].mean() if "readmission_rate" in df.columns else 0
    col2.metric(
        label="📊 Average Readmission Rate (%)",
        value=f"{avg_rate:.2f}%"
    )

    # Helper function to format numbers in K/M
    def format_k_m(number):
        if number >= 1_000_000:
            return f"{number/1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number/1_000:.2f}K"
        else:
            return str(number)
    
    # Total Readmissions
    total_readmissions = df['number_of_readmissions'].sum() if "number_of_readmissions" in df.columns else 0
    col3.metric(
        label="🧪 Total Readmissions",
        value=format_k_m(total_readmissions)
    )

    # Highest Readmission Rate
    max_rate = df['readmission_rate'].max() if "readmission_rate" in df.columns else 0
    col4.metric(
        label="⚠️ Highest Readmission Rate (%)",
        value=f"{max_rate:.2f}%"
    )

    # Sort and take top 10
    df = df.sort_values(by="readmission_rate", ascending=False).head(10)

    fig = px.bar(
        df,
        x="hospital_name",
        y="readmission_rate",
        color="readmission_rate",
        title="🏥 Top 10 Hospital Readmission Comparison"
    )

    fig.update_layout(xaxis_tickangle=-45)  # Rotate labels
    st.plotly_chart(fig, use_container_width=True)
    
    
    # ---------------- Expected vs Predicted Readmissions ----------------

    fig_compare = px.scatter(
        df,
        x='expected_readmission_rate',
        y='predicted_readmission_rate',
        color='hospital_name',
        hover_data=['measure_name'],
        title="⚖️ Expected vs Predicted Readmission Rate",
        size_max=20,           # maximum bubble size
        size='number_of_readmissions'  # optional: scale by readmissions
    )

    # Set x-axis and y-axis ticks without showing 0
    fig_compare.update_xaxes(
        title="Expected Rate",
        dtick=1,           # gap of 1
        range=[0.5, 7],    # start slightly above 0 so 0 tick is hidden
        showticklabels=True
    )

    fig_compare.update_yaxes(
        title="Predicted Rate",
        dtick=1,           # gap of 2
        range=[0.5, 9],    # start slightly above 0 so 0 tick is hidden
        showticklabels=True
    )

    # Increase marker size manually if you don’t want size scaling
    fig_compare.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))

    st.plotly_chart(fig_compare, use_container_width=True)
    
    # ---------------- Distribution of Excess Readmission Ratios ----------------
    fig_hist = px.histogram(df, x="readmission_rate", nbins=20,
                            title="📊 Excess Readmission Ratio Distribution",
                            color_discrete_sequence=["orange"])
    fig_hist.update_layout(xaxis_title="Excess Readmission Ratio", yaxis_title="Count")
    st.plotly_chart(fig_hist, use_container_width=True)

    df_measure = df.groupby("measure_name")["number_of_readmissions"].sum().sort_values(ascending=False).reset_index()

    fig_measure = px.bar(df_measure, x="measure_name", y="number_of_readmissions",
                         color="number_of_readmissions",
                         title="🧪 Number of Readmissions by Measure",
                         text="number_of_readmissions",
                         color_continuous_scale="Blues")
    fig_measure.update_layout(xaxis_tickangle=-45, yaxis_title="Number of Readmissions")
    st.plotly_chart(fig_measure, use_container_width=True)

