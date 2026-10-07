#!/usr/bin/env python3
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from calculate_stats import get_city_stats
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="Nursing Job Listings",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Nursing Job Listings")
st.markdown("Browse registered nurse (RN) job postings across major US cities")

# Fetch all jobs from database
try:
    response = supabase.table('jobs').select('*').order('posted_at', desc=True).execute()
    jobs_data = response.data
except Exception as e:
    st.error(f"Error fetching jobs: {e}")
    st.stop()

if not jobs_data:
    st.warning("No job listings available yet. Please run the scraper first.")
    st.stop()

# Convert to DataFrame for easier handling
df = pd.DataFrame(jobs_data)

# Calculate posting age in days
df['posted_at'] = pd.to_datetime(df['posted_at'])
now = datetime.now(df['posted_at'].dt.tz)
df['days_old'] = (now - df['posted_at']).dt.days

# Filter: only show jobs posted in last 30 days
df = df[df['days_old'] <= 30].reset_index(drop=True)

if len(df) == 0:
    st.warning("No jobs posted in the last 30 days.")
    st.stop()

# Sidebar filters
st.sidebar.header("Filters")

# City filter
cities = sorted(df['city'].unique().tolist())
selected_cities = st.sidebar.multiselect("City", cities, default=cities)
df = df[df['city'].isin(selected_cities)]

# Employment type filter
employment_types = sorted([et for et in df['employment_type'].unique() if et and et.strip()])
if employment_types:
    selected_types = st.sidebar.multiselect("Employment Type", employment_types, default=employment_types)
    df = df[df['employment_type'].isin(selected_types)]

# Salary range filter
col1, col2 = st.sidebar.columns(2)
with col1:
    min_salary = st.number_input("Min Hourly ($)", value=20, step=5)
with col2:
    max_salary = st.number_input("Max Hourly ($)", value=100, step=5)

# Filter by salary range (show jobs where the range overlaps with user's filter)
df = df[
    (df['salary_min_hourly'].fillna(0) <= max_salary) &
    (df['salary_max_hourly'].fillna(200) >= min_salary)
]

# Sort options
sort_option = st.sidebar.selectbox(
    "Sort by",
    [
        "Newest First",
        "Oldest First",
        "Highest Salary",
        "Lowest Salary",
        "City (A-Z)",
        "Company (A-Z)",
    ]
)

if sort_option == "Newest First":
    df = df.sort_values('posted_at', ascending=False)
elif sort_option == "Oldest First":
    df = df.sort_values('posted_at', ascending=True)
elif sort_option == "Highest Salary":
    df = df.sort_values('salary_max_hourly', ascending=False, na_position='last')
elif sort_option == "Lowest Salary":
    df = df.sort_values('salary_min_hourly', ascending=True, na_position='last')
elif sort_option == "City (A-Z)":
    df = df.sort_values('city', ascending=True)
elif sort_option == "Company (A-Z)":
    df = df.sort_values('company', ascending=True)

# Stats cards
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Jobs", len(df))
with col2:
    st.metric("Cities", df['city'].nunique())
with col3:
    avg_salary = df['salary_min_hourly'].mean()
    st.metric("Avg Min Salary", f"${avg_salary:.2f}/hr" if pd.notna(avg_salary) else "N/A")
with col4:
    max_salary_max = df['salary_max_hourly'].max()
    st.metric("Top Salary", f"${max_salary_max:.2f}/hr" if pd.notna(max_salary_max) else "N/A")

st.divider()

# Job listings display
st.subheader(f"Job Listings ({len(df)} results)")

for idx, job in df.iterrows():
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])

        # Job title and company
        with col1:
            title = job['title']
            company = job['company'] if job['company'] else 'Unknown'
            st.markdown(f"### {title}")
            st.markdown(f"**{company}** • {job['city']}, {job['state']}")

        # Salary and employment type
        with col2:
            min_sal = job['salary_min_hourly']
            max_sal = job['salary_max_hourly']
            if pd.notna(min_sal) and pd.notna(max_sal):
                st.markdown(f"**${min_sal:.2f} - ${max_sal:.2f}/hr**")
            elif pd.notna(min_sal):
                st.markdown(f"**${min_sal:.2f}/hr**")
            else:
                st.markdown("**Salary not listed**")

            emp_type = job['employment_type'] if job['employment_type'] else 'Not specified'
            st.caption(f"📋 {emp_type}")

        # Posted date and link
        with col3:
            days = job['days_old']
            if days == 0:
                days_text = "Posted today"
            elif days == 1:
                days_text = "Posted yesterday"
            else:
                days_text = f"Posted {days} days ago"
            st.caption(days_text)

            if job['url']:
                st.markdown(f"[View Job →]({job['url']})")

        # Description (expandable)
        if job['description']:
            with st.expander("View Description"):
                st.text(job['description'][:500] + ("..." if len(job['description']) > 500 else ""))

st.divider()
st.caption(f"Data from {len(df)} nursing job postings. Last updated when dashboard was loaded.")
