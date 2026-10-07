#!/usr/bin/env python3
"""
Nursing Platform Streamlit MVP
City-based salary, cost of living, tax, and licensing explorer for new-grad nurses.
"""

import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

import streamlit as st
from streamlit_option_menu import option_menu
import polars as pl
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
# SUPABASE & AUTH
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    """Initialize Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def signup_user(email: str, password: str, first_name: str, specialty: str) -> Tuple[bool, str]:
    """
    Sign up a new user.
    Returns (success, message)
    """
    try:
        hashed_pwd = hash_password(password)
        response = supabase.table('users').insert({
            'email': email,
            'password_hash': hashed_pwd,
            'first_name': first_name,
            'specialty': specialty,
            'subscription_plan': 'free',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).execute()

        return True, "Signup successful! Please log in."
    except Exception as e:
        if "duplicate" in str(e).lower():
            return False, "Email already registered."
        return False, f"Signup error: {str(e)}"

def login_user(email: str, password: str) -> Tuple[bool, Optional[Dict], str]:
    """
    Authenticate user.
    Returns (success, user_data, message)
    """
    try:
        hashed_pwd = hash_password(password)
        response = supabase.table('users').select('*').eq('email', email).execute()

        if not response.data:
            return False, None, "Email not found."

        user = response.data[0]

        if user['password_hash'] != hashed_pwd:
            return False, None, "Incorrect password."

        return True, user, "Login successful!"

    except Exception as e:
        return False, None, f"Login error: {str(e)}"

# ============================================================================
# AUTHENTICATION UI
# ============================================================================

def show_auth_page():
    """Display login/signup page."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## 🏥 Nursing Job & Compensation Explorer")
        st.markdown("Find your ideal nursing career by city — salary, cost of living, taxes, and licensing all in one place.")

        auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])

        with auth_tab1:
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                success, user, message = login_user(email, password)

                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

        with auth_tab2:
            st.subheader("Create Account")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            first_name = st.text_input("First Name", key="signup_first_name")
            specialty = st.selectbox(
                "Nursing Specialty (optional)",
                ["Any", "Med-Surg", "ICU", "ER", "PACU", "L&D", "Psych", "Pediatrics"],
                key="signup_specialty"
            )

            if st.button("Sign Up", use_container_width=True):
                if not new_email or not new_password:
                    st.error("Email and password required.")
                else:
                    success, message = signup_user(new_email, new_password, first_name, specialty if specialty != "Any" else None)

                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data(ttl=3600)
def load_jobs_by_city(city: str, state: str) -> pl.DataFrame:
    """Load jobs for a city from Supabase."""
    try:
        response = supabase.table('jobs').select('*').eq('city', city).eq('state', state).eq('is_active', True).execute()

        if response.data:
            return pl.DataFrame(response.data)
        return pl.DataFrame()
    except Exception as e:
        st.error(f"Error loading jobs: {str(e)}")
        return pl.DataFrame()

@st.cache_data(ttl=3600)
def load_cities_stats() -> pl.DataFrame:
    """Load aggregated stats for all cities from new_grad_jobs_by_city view."""
    try:
        response = supabase.table('new_grad_jobs_by_city').select('*').execute()

        if response.data:
            return pl.DataFrame(response.data)
        return pl.DataFrame()
    except Exception as e:
        st.error(f"Error loading city stats: {str(e)}")
        return pl.DataFrame()

@st.cache_data(ttl=3600)
def load_cost_of_living(city: str, state: str, year: int = 2026) -> Optional[Dict]:
    """Load cost of living data for a city."""
    try:
        response = supabase.table('cost_of_living').select('*').eq('city', city).eq('state', state).eq('year', year).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.warning(f"Cost of living data not available for {city}, {state}")
        return None

@st.cache_data(ttl=3600)
def load_tax_data(state: str, year: int = 2026) -> Optional[Dict]:
    """Load tax data for a state."""
    try:
        response = supabase.table('tax_rates').select('*').eq('state', state).eq('year', year).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.warning(f"Tax data not available for {state}")
        return None

@st.cache_data(ttl=3600)
def load_license_data(state: str) -> Optional[Dict]:
    """Load nursing license data for a state."""
    try:
        response = supabase.table('nursing_licenses').select('*').eq('state', state).execute()

        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.warning(f"License data not available for {state}")
        return None

# ============================================================================
# CALCULATIONS
# ============================================================================

def calculate_federal_tax(gross_income: float, filing_status: str = "single", year: int = 2026) -> float:
    """
    Calculate federal income tax (simplified 2026 brackets for single filer).
    """
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

def calculate_state_tax(gross_income: float, state: str, year: int = 2026) -> float:
    """Calculate state income tax based on state tax rate."""
    tax_data = load_tax_data(state, year)

    if not tax_data:
        return 0.0

    state_rate = tax_data.get('state_income_tax_rate', 0.0) or 0.0
    standard_deduction = tax_data.get('state_standard_deduction', 0) or 0

    taxable = max(0, gross_income - standard_deduction)
    return taxable * state_rate

def calculate_take_home(hourly_rate: float, state: str, hours_per_year: int = 2080) -> Dict[str, float]:
    """
    Calculate take-home pay from hourly rate.
    Returns dict with gross, federal_tax, state_tax, fica, take_home.
    """
    gross = hourly_rate * hours_per_year

    federal_tax = calculate_federal_tax(gross)
    state_tax = calculate_state_tax(gross, state)

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
# UI COMPONENTS
# ============================================================================

def show_city_card(city: str, state: str, jobs_df: pl.DataFrame, col: any):
    """Display a summary card for a city."""
    with col:
        st.markdown(f"### {city}, {state}")

        if jobs_df.is_empty():
            st.info("No job data available yet")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                job_count = len(jobs_df)
                st.metric("Total Jobs", job_count)

            with col2:
                new_grad_count = len(jobs_df.filter(pl.col('new_grad_keywords') == True))
                st.metric("New Grad Friendly", new_grad_count)

            with col3:
                if 'salary_max_hourly' in jobs_df.columns:
                    median_salary = jobs_df['salary_max_hourly'].mean()
                    st.metric("Median Pay", f"${median_salary:.2f}/hr" if median_salary else "N/A")

def show_city_detail(city: str, state: str):
    """Display detailed view for a city."""
    st.markdown(f"# {city}, {state}")

    jobs_df = load_jobs_by_city(city, state)
    col_data = load_cost_of_living(city, state)
    tax_data = load_tax_data(state)
    license_data = load_license_data(state)

    # Job Overview
    st.markdown("## Job Market")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Jobs", len(jobs_df))

    with col2:
        new_grad = len(jobs_df.filter(pl.col('new_grad_keywords') == True)) if not jobs_df.is_empty() else 0
        st.metric("New Grad Friendly", new_grad)

    with col3:
        if not jobs_df.is_empty() and 'salary_min_hourly' in jobs_df.columns:
            min_sal = jobs_df['salary_min_hourly'].mean()
            st.metric("Avg Min", f"${min_sal:.2f}/hr" if min_sal else "N/A")

    with col4:
        if not jobs_df.is_empty() and 'salary_max_hourly' in jobs_df.columns:
            max_sal = jobs_df['salary_max_hourly'].mean()
            st.metric("Avg Max", f"${max_sal:.2f}/hr" if max_sal else "N/A")

    # Jobs Table
    if not jobs_df.is_empty():
        st.subheader("Recent Job Postings")

        # Filter to show new grad friendly by default
        show_all = st.checkbox("Show all jobs (including experienced roles)")

        if show_all:
            display_df = jobs_df
        else:
            display_df = jobs_df.filter(pl.col('new_grad_keywords') == True)

        # Select columns for display
        cols_to_show = ['title', 'company', 'employment_type', 'salary_min_hourly', 'salary_max_hourly', 'posted_at']
        cols_available = [c for c in cols_to_show if c in display_df.columns]

        st.dataframe(
            display_df.select(cols_available).head(25),
            use_container_width=True,
            height=400
        )

    # Compensation Analysis
    st.markdown("## Compensation & Cost of Living Analysis")

    if not jobs_df.is_empty() and 'salary_max_hourly' in jobs_df.columns:
        typical_hourly = jobs_df['salary_max_hourly'].mean()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Your Take-Home Pay")

            paycheck = calculate_take_home(typical_hourly, state)

            metric_col1, metric_col2 = st.columns(2)

            with metric_col1:
                st.metric("Gross Annual", f"${paycheck['gross']:,.0f}")
                st.metric("Take-Home Annual", f"${paycheck['take_home']:,.0f}")

            with metric_col2:
                st.metric("Monthly Net", f"${paycheck['monthly_take_home']:,.0f}")
                st.metric("Federal Tax", f"${paycheck['federal_tax']:,.0f}")

            st.caption(f"Based on {typical_hourly:.2f}/hr, 2080 hours/year (40 hrs/week)")

        with col2:
            st.markdown("### Cost of Living")

            if col_data:
                st.metric("Monthly Housing (Median Rent)", f"${col_data.get('housing_median_rent', 'N/A')}")
                st.metric("Monthly Total Living Costs", f"${col_data.get('monthly_total', 'N/A')}")
                st.metric("Annual Living Costs", f"${col_data.get('annual_total', 'N/A')}")

                if paycheck['take_home'] > 0 and col_data.get('annual_total'):
                    disposable = paycheck['take_home'] - col_data['annual_total']
                    st.metric("Estimated Disposable Income", f"${disposable:,.0f}", delta="after living costs")
            else:
                st.info("Cost of living data not available for this city yet.")

    # Licensing Info
    st.markdown("## Nursing License Requirements")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### {state}")

        if license_data:
            compact = "✅ Yes" if license_data.get('compact_state') else "❌ No"
            st.metric("Compact State", compact)

            if license_data.get('endorsement_fee'):
                st.metric("Endorsement Fee", f"${license_data['endorsement_fee']}")

            if license_data.get('endorsement_processing_days'):
                st.metric("Processing Time", f"{license_data['endorsement_processing_days']} days")
        else:
            st.info("License data not available.")

    with col2:
        st.markdown("### Tax Summary")

        if tax_data:
            state_rate = tax_data.get('state_income_tax_rate', 0) or 0
            st.metric("State Income Tax Rate", f"{state_rate*100:.2f}%")

            if tax_data.get('state_standard_deduction'):
                st.metric("State Standard Deduction", f"${tax_data['state_standard_deduction']:,}")
        else:
            st.info("Tax data not available.")

# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application."""

    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None

    # Show auth page if not authenticated
    if not st.session_state.authenticated:
        show_auth_page()
        return

    # Authenticated user navigation
    st.sidebar.markdown(f"### Welcome, {st.session_state.user.get('first_name', 'User')}!")
    st.sidebar.markdown(f"Plan: **{st.session_state.user.get('subscription_plan', 'free').upper()}**")

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    st.sidebar.divider()

    # Main navigation
    page = option_menu(
        menu_title="Navigation",
        options=["Explore Cities", "City Comparison", "Job Search", "Saved Jobs"],
        icons=["map", "bar-chart", "briefcase", "bookmark"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

    st.sidebar.divider()

    # Plan info
    if st.session_state.user.get('subscription_plan') == 'free':
        st.sidebar.info(
            "📌 **Upgrade to Premium** to unlock:\n\n"
            "• Detailed salary comparisons\n"
            "• Advanced filtering\n"
            "• Job alerts\n"
            "• Career recommendations"
        )

    # Page routing
    if page == "Explore Cities":
        st.title("🏥 Nursing Job & Compensation Explorer")

        # Load city stats
        cities_df = load_cities_stats()

        if cities_df.is_empty():
            st.warning("No city data available yet. Check back soon!")
        else:
            # City search
            col1, col2 = st.columns([2, 1])

            with col1:
                city_search = st.selectbox(
                    "Select a city to explore",
                    sorted(cities_df['city'].unique().to_list()) if 'city' in cities_df.columns else []
                )

            if city_search:
                # Find state for selected city
                city_data = cities_df.filter(pl.col('city') == city_search)

                if not city_data.is_empty():
                    state = city_data['state'].to_list()[0]
                    show_city_detail(city_search, state)
                else:
                    st.error("City not found")

    elif page == "City Comparison":
        st.title("📊 Compare Cities")

        cities_df = load_cities_stats()

        if cities_df.is_empty():
            st.warning("No city data available yet.")
        else:
            # Multi-select cities
            available_cities = sorted(cities_df['city'].unique().to_list()) if 'city' in cities_df.columns else []

            selected_cities = st.multiselect(
                "Select cities to compare (max 5)",
                available_cities,
                max_selections=5
            )

            if selected_cities and len(selected_cities) >= 2:
                # Build comparison table
                comparison_data = []

                for city in selected_cities:
                    city_row = cities_df.filter(pl.col('city') == city)

                    if not city_row.is_empty():
                        state = city_row['state'].to_list()[0]
                        jobs = load_jobs_by_city(city, state)
                        col_data = load_cost_of_living(city, state)

                        if not jobs.is_empty() and 'salary_max_hourly' in jobs.columns:
                            avg_hourly = jobs['salary_max_hourly'].mean()
                            paycheck = calculate_take_home(avg_hourly, state)

                            comparison_data.append({
                                'City': f"{city}, {state}",
                                'Jobs': len(jobs),
                                'Avg Salary': f"${avg_hourly:.2f}/hr",
                                'Annual Gross': f"${paycheck['gross']:,.0f}",
                                'Annual Take-Home': f"${paycheck['take_home']:,.0f}",
                                'Monthly COL': f"${col_data.get('monthly_total', 'N/A')}" if col_data else "N/A"
                            })

                if comparison_data:
                    comparison_df = pl.DataFrame(comparison_data)
                    st.dataframe(comparison_df, use_container_width=True)

    elif page == "Job Search":
        st.title("💼 Job Search")
        st.info("Search and filter nursing jobs across cities.")

        col1, col2, col3 = st.columns(3)

        with col1:
            cities_df = load_cities_stats()
            city = st.selectbox("City", sorted(cities_df['city'].unique().to_list()) if 'city' in cities_df.columns else [])

        with col2:
            if city:
                state_row = cities_df.filter(pl.col('city') == city)
                state = state_row['state'].to_list()[0] if not state_row.is_empty() else ""

        with col3:
            new_grad_only = st.checkbox("New Grad Friendly Only", value=True)

        if city:
            jobs_df = load_jobs_by_city(city, state)

            if new_grad_only:
                jobs_df = jobs_df.filter(pl.col('new_grad_keywords') == True)

            if not jobs_df.is_empty():
                st.subheader(f"Jobs in {city}, {state}")
                st.dataframe(jobs_df, use_container_width=True, height=500)
            else:
                st.info("No jobs found matching your criteria.")

    elif page == "Saved Jobs":
        st.title("📌 Saved Jobs")
        st.info("Premium feature: Save and track jobs you're interested in.")

        if st.session_state.user.get('subscription_plan') == 'free':
            st.warning("❌ This feature is available in Premium. Upgrade to unlock!")
        else:
            st.success("✅ Loading your saved jobs...")

if __name__ == "__main__":
    main()
