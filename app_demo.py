#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="Nursing Job Listings - Salary Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Brand color system
PRIMARY_BLUE = "#0066cc"
DARK_BLUE = "#0052a3"
BG_LIGHT = "#f8f9fa"
WHITE = "#ffffff"
TEXT_DARK = "#111"
TEXT_GRAY = "#666"
BORDER_GRAY = "#e0e0e0"

# Custom CSS to match landing page design
st.markdown(f"""
<style>
    /* Root styling */
    html, body, [data-testid="stAppViewContainer"] {{
        background-color: {BG_LIGHT};
    }}

    /* Header/top bar styling */
    [data-testid="stHeader"] {{
        background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {DARK_BLUE} 100%);
    }}

    /* Main content area */
    [data-testid="stAppViewContainer"] > div:first-child {{
        background-color: {BG_LIGHT};
    }}

    /* Text styling */
    h1, h2, h3 {{
        color: {TEXT_DARK};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-weight: 700;
    }}

    p, span, div {{
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: {TEXT_DARK};
    }}

    /* Cards and containers */
    [data-testid="stVerticalBlock"] > [style*="border"] {{
        background-color: {WHITE};
        border: 1px solid {BORDER_GRAY} !important;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }}

    /* Metric cards */
    [data-testid="metric-container"] {{
        background-color: {WHITE};
        border: 1px solid {BORDER_GRAY};
        border-radius: 8px;
        padding: 20px;
    }}

    /* Buttons */
    button {{
        background-color: {PRIMARY_BLUE} !important;
        color: {WHITE} !important;
        border-radius: 6px;
        font-weight: 600;
        border: none !important;
    }}

    button:hover {{
        background-color: {DARK_BLUE} !important;
    }}

    /* Input fields */
    input, select, textarea {{
        border: 1px solid {BORDER_GRAY} !important;
        border-radius: 6px;
        background-color: {WHITE} !important;
        color: {TEXT_DARK} !important;
    }}

    input:focus, select:focus {{
        border-color: {PRIMARY_BLUE} !important;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1) !important;
    }}

    /* Links */
    a {{
        color: {PRIMARY_BLUE} !important;
        text-decoration: none;
    }}

    a:hover {{
        color: {DARK_BLUE} !important;
        text-decoration: underline;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {WHITE};
        border-right: 1px solid {BORDER_GRAY};
    }}

    /* Dividers */
    hr {{
        border-color: {BORDER_GRAY} !important;
        margin: 24px 0;
    }}
</style>
""", unsafe_allow_html=True)

# Header matching landing page design
st.markdown(f"""
<div style="background: linear-gradient(135deg, {PRIMARY_BLUE} 0%, {DARK_BLUE} 100%); padding: 24px 0; margin: -3rem -1.5rem 0 -1.5rem; padding-left: 1.5rem; padding-right: 1.5rem;">
    <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">🧭 Nursing Job Listings</h1>
    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 16px;">Real registered nurse jobs across America. Updated daily from LinkedIn & Indeed.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("")  # Breathing room

# Fetch all jobs from database
try:
    response = supabase.table('jobs').select('*').order('posted_at', desc=True).execute()
    jobs_data = response.data
except Exception as e:
    st.error(f"Unable to load job data. Please try again later.")
    st.stop()

if not jobs_data:
    st.warning("No job listings available yet. Check back soon as we're adding new jobs daily.")
    st.stop()

# Convert to DataFrame
df = pd.DataFrame(jobs_data)

# Calculate posting age
df['posted_at'] = pd.to_datetime(df['posted_at'])
now = datetime.now(df['posted_at'].dt.tz)
df['days_old'] = (now - df['posted_at']).dt.days

# Filter to last 30 days
df = df[df['days_old'] <= 30].reset_index(drop=True)

if len(df) == 0:
    st.info("No jobs posted in the last 30 days. New listings arrive daily.")
    st.stop()

# Filters in columns (top of page, not sidebar)
st.markdown("### Find Your Next Opportunity")

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    cities = sorted(df['city'].unique().tolist())
    selected_cities = st.multiselect("City", cities, default=cities, key="city_filter")
    df = df[df['city'].isin(selected_cities)]

with filter_col2:
    employment_types = sorted([et for et in df['employment_type'].unique() if et and et.strip()])
    if employment_types:
        selected_types = st.multiselect("Employment Type", employment_types, default=employment_types, key="type_filter")
        df = df[df['employment_type'].isin(selected_types)]

with filter_col3:
    min_salary = st.number_input("Min Hourly ($)", value=20, step=5, key="min_sal")

with filter_col4:
    max_salary = st.number_input("Max Hourly ($)", value=100, step=5, key="max_sal")

df = df[
    (df['salary_min_hourly'].fillna(0) <= max_salary) &
    (df['salary_max_hourly'].fillna(200) >= min_salary)
]

# Sort option
sort_col1, sort_col2 = st.columns([3, 1])
with sort_col2:
    sort_option = st.selectbox(
        "Sort by",
        ["Newest First", "Highest Salary", "Lowest Salary", "City", "Company"],
        label_visibility="collapsed"
    )

if sort_option == "Newest First":
    df = df.sort_values('posted_at', ascending=False)
elif sort_option == "Highest Salary":
    df = df.sort_values('salary_max_hourly', ascending=False, na_position='last')
elif sort_option == "Lowest Salary":
    df = df.sort_values('salary_min_hourly', ascending=True, na_position='last')
elif sort_option == "City":
    df = df.sort_values('city', ascending=True)
else:  # Company
    df = df.sort_values('company', ascending=True)

# Stats overview
st.markdown("---")

stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)

with stats_col1:
    st.metric("Jobs Available", len(df))
with stats_col2:
    st.metric("Cities", df['city'].nunique())
with stats_col3:
    avg_salary = df['salary_min_hourly'].mean()
    st.metric("Avg Starting", f"${avg_salary:.2f}/hr" if pd.notna(avg_salary) else "N/A")
with stats_col4:
    top_salary = df['salary_max_hourly'].max()
    st.metric("Top Salary", f"${top_salary:.2f}/hr" if pd.notna(top_salary) else "N/A")

st.markdown("---")

# Job listings
st.markdown(f"### Job Listings ({len(df)} results)")

for idx, job in df.iterrows():
    col_left, col_right = st.columns([3, 1], gap="large")

    with col_left:
        title = job['title']
        company = job['company'] if job['company'] else 'Unknown'
        st.markdown(f"**{title}**")
        st.markdown(f"{company} • {job['city']}, {job['state']}")

        # Salary and type
        min_sal = job['salary_min_hourly']
        max_sal = job['salary_max_hourly']
        if pd.notna(min_sal) and pd.notna(max_sal):
            salary_text = f"${min_sal:.2f} - ${max_sal:.2f}/hr"
        elif pd.notna(min_sal):
            salary_text = f"${min_sal:.2f}/hr"
        else:
            salary_text = "Salary not listed"

        emp_type = job['employment_type'] if job['employment_type'] else 'Full-time'
        st.markdown(f"{salary_text} • {emp_type}")

        # Description preview
        if job['description']:
            desc_preview = job['description'][:150]
            if len(job['description']) > 150:
                desc_preview += "..."
            st.caption(desc_preview)

    with col_right:
        days = job['days_old']
        if days == 0:
            days_text = "Posted today"
        elif days == 1:
            days_text = "Posted yesterday"
        else:
            days_text = f"{days}d ago"

        st.caption(days_text)

        if job['url']:
            st.markdown(f"[Apply Now →]({job['url']})")

    st.markdown("---")

st.caption(f"Data from {len(df)} nursing job postings across {df['city'].nunique()} cities. Updated daily with fresh listings from LinkedIn & Indeed.")