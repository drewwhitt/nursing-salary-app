#!/usr/bin/env python3
"""
Nursing Platform Streamlit MVP (Demo - No Auth)
City-based salary, cost of living, tax, and licensing explorer for new-grad nurses.
"""

import os
from datetime import datetime
from typing import Optional, Dict

import streamlit as st
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
import plotly.express as px
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

st.set_page_config(
    page_title="Nursing Job & Compensation Explorer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(ttl=3600)
def load_all_jobs():
    """Load all active jobs from Supabase."""
    try:
        response = supabase.table('jobs').select('*').eq('is_active', True).execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.error(f"Error loading jobs: {str(e)}")
        return []

@st.cache_data(ttl=3600)
def load_wage_benchmarks():
    """Load wage benchmarks from Supabase."""
    try:
        response = supabase.table('wages_benchmark').select('*').execute()
        if response.data:
            return response.data
        return []
    except Exception as e:
        st.warning(f"Error loading wage benchmarks: {str(e)}")
        return []

# ============================================================================
# CALCULATIONS
# ============================================================================

def calculate_federal_tax(gross_income: float, filing_status: str = "single", year: int = 2026) -> float:
    """Calculate federal income tax (simplified 2026 brackets for single filer)."""
    # 2026 federal brackets (simplified for single)
    brackets = [
        (11000, 0.10),
        (44725, 0.12),
        (95375, 0.22),
    ]
    standard_deduction = 16100

    taxable = max(0, gross_income - standard_deduction)
    tax = 0.0
    prev_limit = 0

    for limit, rate in brackets:
        if taxable <= prev_limit:
            break
        taxable_in_bracket = min(taxable, limit) - prev_limit
        tax += taxable_in_bracket * rate
        prev_limit = limit

    # If income exceeds last bracket, add remaining at 24%
    if taxable > prev_limit:
        tax += (taxable - prev_limit) * 0.24

    return tax

def calculate_state_tax(gross_income: float, state_rate: float = 0.0, state_deduction: float = 0.0) -> float:
    """Calculate state income tax based on state tax rate."""
    taxable = max(0, gross_income - state_deduction)
    return taxable * state_rate

def calculate_take_home(hourly_rate: float, state_rate: float = 0.0, hours_per_year: int = 2080) -> Dict[str, float]:
    """Calculate take-home pay from hourly rate."""
    gross = hourly_rate * hours_per_year

    federal_tax = calculate_federal_tax(gross)
    state_tax = calculate_state_tax(gross, state_rate)

    # FICA (Social Security 6.2% + Medicare 1.45%)
    fica = gross * 0.0765

    take_home = gross - federal_tax - state_tax - fica

    return {
        'gross': gross,
        'federal_tax': federal_tax,
        'state_tax': state_tax,
        'fica': fica,
        'take_home': take_home,
        'monthly_take_home': take_home / 12
    }

# ============================================================================
# MAIN UI
# ============================================================================

st.markdown("# 🏥 Nursing Job & Compensation Explorer")
st.markdown("Find your ideal nursing career by city — salary, cost of living, taxes, and licensing all in one place.")
st.markdown("---")

# Load data
jobs = load_all_jobs()
benchmarks = load_wage_benchmarks()

# Create a mapping of benchmarks
benchmark_map = {(b.get('city'), b.get('state')): b for b in benchmarks}

if not jobs:
    st.warning("No jobs loaded yet. Run the scraper first!")
    st.stop()

# Get unique cities
cities = sorted(set((j.get('city'), j.get('state')) for j in jobs if j.get('city') and j.get('state')))

st.markdown(f"### Found {len(jobs)} nursing jobs in {len(cities)} cities")

# Sidebar filters
st.sidebar.markdown("## 🔍 Filters")
selected_cities = st.sidebar.multiselect(
    "Select cities to explore",
    options=[f"{city}, {state}" for city, state in cities],
    default=[f"{city}, {state}" for city, state in cities[:3]]
)

if selected_cities:
    selected_cities_parsed = [tuple(c.split(", ")) for c in selected_cities]
else:
    selected_cities_parsed = cities

# Display jobs by city
for city, state in selected_cities_parsed:
    st.markdown(f"## {city}, {state}")

    # Filter jobs for this city
    city_jobs = [j for j in jobs if j.get('city') == city and j.get('state') == state]

    if not city_jobs:
        st.info("No jobs in this city yet.")
        continue

    # Get wage benchmark
    benchmark = benchmark_map.get((city, state), {})
    bls_hourly = benchmark.get('rn_hourly_median')

    if bls_hourly:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("BLS Median RN Wage", f"${bls_hourly:.2f}/hr")
        with col2:
            st.metric("BLS Annual", f"${bls_hourly * 2080:,.0f}")
        with col3:
            st.metric("Jobs Listed", len(city_jobs))
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Jobs Listed", len(city_jobs))
        with col2:
            st.info("BLS data not available")

    st.markdown("---")

    # Display jobs
    for job in city_jobs[:5]:  # Show top 5 jobs per city
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{job.get('title', 'Unknown')}**")
                st.markdown(f"*{job.get('company', 'Unknown Company')}*")

                if job.get('description'):
                    st.caption(job['description'][:200] + "..." if len(job['description']) > 200 else job['description'])

            with col2:
                salary_min = job.get('salary_min_hourly')
                salary_max = job.get('salary_max_hourly')
                if salary_min and salary_max:
                    st.markdown(f"**${salary_min:.2f} - ${salary_max:.2f}/hr**")
                    st.caption(f"Annual: ${salary_min * 2080:,.0f} - ${salary_max * 2080:,.0f}")
                else:
                    st.caption("Salary not listed")

            # Expandable details
            with st.expander("Details & Salary Calculation"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**Job Info**")
                    st.caption(f"Specialty: {job.get('specialty', 'N/A')}")
                    st.caption(f"Shift: {job.get('shift', 'N/A')}")
                    st.caption(f"Type: {job.get('employment_type', 'N/A')}")

                with col2:
                    st.write("**Compensation**")
                    if job.get('sign_on_bonus'):
                        st.caption(f"Sign-on: ${job['sign_on_bonus']:,}")
                    if job.get('shift_differential_hourly'):
                        st.caption(f"Shift Diff: ${job['shift_differential_hourly']:.2f}/hr")
                    if job.get('residency_program'):
                        st.caption("✓ Residency Program")

                with col3:
                    st.write("**Take-Home Calculation**")
                    if salary_min and salary_max:
                        avg_hourly = (salary_min + salary_max) / 2
                        calc = calculate_take_home(avg_hourly, state_rate=0.0)
                        st.caption(f"Gross (annual): ${calc['gross']:,.0f}")
                        st.caption(f"Take-home: ${calc['take_home']:,.0f}")
                        st.caption(f"Monthly: ${calc['monthly_take_home']:,.0f}")

st.markdown("---")
st.markdown("**Demo Mode** - No authentication required. Data loaded from Supabase sample jobs.")