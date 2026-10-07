#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from calculate_stats import get_city_stats, get_overall_stats
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Nursing Job Salary Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Nursing Job Salary Analytics")
st.markdown("Real-time analysis of registered nurse job listings across major US cities")

# Get data
overall_stats = get_overall_stats()
city_stats = get_city_stats()

if not overall_stats or not city_stats:
    st.error("No data available. Please run the scraper first.")
    st.stop()

# Overall stats cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Jobs", overall_stats['total_jobs'])

with col2:
    st.metric("Cities Tracked", len(city_stats))

with col3:
    st.metric("Mean Salary", f"${overall_stats['mean_hourly']:.2f}/hr")

with col4:
    st.metric("Median Salary", f"${overall_stats['median_hourly']:.2f}/hr")

with col5:
    st.metric("Salary Range", f"${overall_stats['min_hourly']:.2f} - ${overall_stats['max_hourly']:.2f}")

st.divider()

# Prepare data for charts
city_names = []
median_salaries = []
mean_salaries = []
job_counts = []

sorted_cities = sorted(
    city_stats.items(),
    key=lambda x: x[1]['median_hourly'] if x[1]['median_hourly'] else 0,
    reverse=True
)

for city, stats in sorted_cities:
    if stats['median_hourly']:
        city_names.append(city)
        median_salaries.append(stats['median_hourly'])
        mean_salaries.append(stats['mean_hourly'])
        job_counts.append(stats['job_count'])

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["Salary Comparison", "Job Distribution", "City Details"])

with tab1:
    st.subheader("Median & Mean Hourly Rate by City")

    # Create bar chart with both median and mean
    df_chart = pd.DataFrame({
        'City': city_names,
        'Median': median_salaries,
        'Mean': mean_salaries,
    })

    fig = go.Figure(data=[
        go.Bar(name='Median', x=df_chart['City'], y=df_chart['Median'], marker_color='#1f77b4'),
        go.Bar(name='Mean', x=df_chart['City'], y=df_chart['Mean'], marker_color='#ff7f0e')
    ])

    fig.update_layout(
        barmode='group',
        title="Median vs Mean Hourly Rates",
        xaxis_title="City",
        yaxis_title="Hourly Rate ($)",
        hovermode='x unified',
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Job Postings by City")

    df_jobs = pd.DataFrame({
        'City': city_names,
        'Jobs': job_counts,
    }).sort_values('Jobs', ascending=False)

    fig = px.bar(
        df_jobs,
        x='City',
        y='Jobs',
        title="Number of Job Postings by City",
        color='Jobs',
        color_continuous_scale='Viridis'
    )

    fig.update_layout(height=500, hovermode='x')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Detailed City Statistics")

    # Create detailed table
    detailed_data = []
    for city, stats in sorted_cities:
        if stats['median_hourly']:
            detailed_data.append({
                'City': city,
                'Jobs': stats['job_count'],
                'With Salary': stats['jobs_with_salary'],
                'Median': f"${stats['median_hourly']:.2f}",
                'Mean': f"${stats['mean_hourly']:.2f}",
                'Min': f"${stats['min_hourly']:.2f}",
                'Max': f"${stats['max_hourly']:.2f}",
                'Std Dev': f"${stats['stdev_hourly']:.2f}",
            })

    df_detailed = pd.DataFrame(detailed_data)
    st.dataframe(df_detailed, use_container_width=True, hide_index=True)

    # Download button
    csv = df_detailed.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="nursing_salary_stats.csv",
        mime="text/csv"
    )

st.divider()

# Footer with refresh info
st.caption(f"Data includes {overall_stats['total_jobs']} job listings across {len(city_stats)} cities. Last updated when dashboard was loaded.")