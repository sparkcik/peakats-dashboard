#!/usr/bin/env python3
"""
PEAKATS CLIENT DASHBOARD v1.0 - CLOUD VERSION
View-only interface for clients to see their candidates

Access: Add ?client=client_id to URL
Example: https://your-app.streamlit.app/?client=cbm
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

# Page config
st.set_page_config(
    page_title="PEAK Candidate Status",
    page_icon="📋",
    layout="wide"
)

def get_database_connection():
    """Get database connection - supports both local and cloud"""
    try:
        # Try Streamlit secrets first (cloud)
        db_url = st.secrets["database"]["url"]
    except:
        # Fall back to environment variable (local)
        import os
        db_url = os.environ.get('SUPABASE_DB_URL')
    
    if not db_url:
        st.error("Database connection not configured")
        return None
    
    return create_engine(db_url)

def load_client_registry():
    """Load client registry for display names"""
    # Try multiple locations
    paths = [
        Path("client_registry.json"),  # Same directory (cloud)
        Path(__file__).parent / "client_registry.json",  # Script directory
        Path.home() / "Library/CloudStorage/GoogleDrive-charles@thefoundry.llc/My Drive/PEAK/#PEAKATS/00_SYSTEM/client_registry.json"  # Local
    ]
    
    for path in paths:
        if path.exists():
            try:
                with open(path, 'r') as f:
                    registry = json.load(f)
                return registry.get('clients', {})
            except:
                continue
    
    return {}

def get_client_display_name(client_id, registry):
    """Get display name for client dashboard header"""
    client_info = registry.get(client_id, {})
    # Priority: dashboard_title > display_name > client_id
    return client_info.get('dashboard_title', 
           client_info.get('display_name', 
           client_info.get('name', client_id.upper())))

def load_candidates(client_id):
    """Load candidates for specific client"""
    engine = get_database_connection()
    if not engine:
        return pd.DataFrame()
    
    query = """
        SELECT 
            first_name,
            last_name,
            COALESCE(fedex_id, '') as fedex_id,
            COALESCE(rwp_score, 0) as rwp_score,
            COALESCE(rwp_classification, '') as rwp_classification,
            COALESCE(rwp_rationale, '') as rwp_rationale,
            COALESCE(profile_status, '') as profile_status,
            COALESCE(background_status, '') as background_status,
            COALESCE(drug_test_status, '') as drug_test_status,
            COALESCE(gcic_uploaded, 0) as g,
            COALESCE(mec_uploaded, 0) as m,
            COALESCE(phone, '') as phone,
            COALESCE(email, '') as email,
            created_at
        FROM candidates
        WHERE client_id = :client_id
        ORDER BY created_at DESC
    """
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params={"client_id": client_id})
    
    return df

def main():
    # Get client from URL parameter
    query_params = st.query_params
    
    # Handle both old and new Streamlit query_params behavior
    client_id = query_params.get('client', [None])
    if isinstance(client_id, list):
        client_id = client_id[0] if client_id else None
    
    # Load registry
    registry = load_client_registry()
    
    # If no client specified, show error
    if not client_id:
        st.error("⚠️ No client specified")
        st.markdown("### How to access your dashboard")
        st.markdown("Add your client ID to the URL:")
        st.code("http://your-dashboard-url/?client=your_client_id")
        st.markdown("---")
        st.markdown("**Available clients:**")
        for cid, info in registry.items():
            display = info.get('display_name', info.get('name', cid))
            st.markdown(f"- `{cid}` → {display}")
        return
    
    # Validate client exists
    if client_id not in registry:
        st.error(f"⚠️ Unknown client: {client_id}")
        st.markdown("Please check your URL and try again.")
        return
    
    # Get display name
    display_name = get_client_display_name(client_id, registry)
    
    # Header
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2.2em;">
                📋 {display_name}
            </h1>
            <p style="color: #a0c4e8; margin: 5px 0 0 0; font-size: 1.1em;">
                Candidate Status Dashboard
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_candidates(client_id)
    
    if df.empty:
        st.info("No candidates found for this client.")
        return
    
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Candidates", len(df))
    
    with col2:
        cleared = len(df[df['background_status'].str.contains('Clear|Complete', case=False, na=False)])
        st.metric("Background Cleared", cleared)
    
    with col3:
        drug_passed = len(df[df['drug_test_status'].str.contains('Negative|Pass', case=False, na=False)])
        st.metric("Drug Test Passed", drug_passed)
    
    with col4:
        ready = len(df[(df['g'] == 1) & (df['m'] == 1)])
        st.metric("Forms Complete", ready)
    
    st.markdown("---")
    
    # Prepare display dataframe
    display_df = df.copy()
    
    # Rename columns
    display_df.columns = [
        'First Name', 'Last Name', 'FedEx ID', 'RWP', 'Classification', 'Rationale',
        'Profile Status', 'Background Status', 'Drug Status', 'G', 'M', 'Phone', 'Email', 'Added'
    ]
    
    # Format G/M as checkmarks
    display_df['G'] = display_df['G'].apply(lambda x: '✅' if x == 1 else '⬜')
    display_df['M'] = display_df['M'].apply(lambda x: '✅' if x == 1 else '⬜')
    
    # Format date
    display_df['Added'] = pd.to_datetime(display_df['Added']).dt.strftime('%m/%d/%Y')
    
    # Fill NaN
    display_df = display_df.fillna('')
    
    # Status filters
    st.markdown("### 🔍 Filter Candidates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bg_filter = st.selectbox("Background Status", 
            ['All'] + sorted(display_df['Background Status'].unique().tolist()))
    
    with col2:
        drug_filter = st.selectbox("Drug Status",
            ['All'] + sorted(display_df['Drug Status'].unique().tolist()))
    
    with col3:
        form_filter = st.selectbox("Forms Status",
            ['All', 'Both Complete', 'G Only', 'M Only', 'Neither'])
    
    # Apply filters
    filtered_df = display_df.copy()
    
    if bg_filter != 'All':
        filtered_df = filtered_df[filtered_df['Background Status'] == bg_filter]
    
    if drug_filter != 'All':
        filtered_df = filtered_df[filtered_df['Drug Status'] == drug_filter]
    
    if form_filter == 'Both Complete':
        filtered_df = filtered_df[(filtered_df['G'] == '✅') & (filtered_df['M'] == '✅')]
    elif form_filter == 'G Only':
        filtered_df = filtered_df[(filtered_df['G'] == '✅') & (filtered_df['M'] == '⬜')]
    elif form_filter == 'M Only':
        filtered_df = filtered_df[(filtered_df['G'] == '⬜') & (filtered_df['M'] == '✅')]
    elif form_filter == 'Neither':
        filtered_df = filtered_df[(filtered_df['G'] == '⬜') & (filtered_df['M'] == '⬜')]
    
    st.markdown(f"### 📋 Candidates ({len(filtered_df)})")
    
    # Display table
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'First Name': st.column_config.TextColumn('First Name', width='medium'),
            'Last Name': st.column_config.TextColumn('Last Name', width='medium'),
            'FedEx ID': st.column_config.TextColumn('FedEx ID', width='small'),
            'RWP': st.column_config.NumberColumn('RWP', width='small', format="%.1f"),
            'Classification': st.column_config.TextColumn('Classification', width='medium'),
            'Rationale': st.column_config.TextColumn('Rationale', width='large'),
            'Profile Status': st.column_config.TextColumn('Profile', width='medium'),
            'Background Status': st.column_config.TextColumn('Background', width='medium'),
            'Drug Status': st.column_config.TextColumn('Drug Test', width='medium'),
            'G': st.column_config.TextColumn('G', width='small'),
            'M': st.column_config.TextColumn('M', width='small'),
            'Phone': st.column_config.TextColumn('Phone', width='medium'),
            'Email': st.column_config.TextColumn('Email', width='large'),
            'Added': st.column_config.TextColumn('Added', width='small'),
        }
    )
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
        <div style="text-align: center; color: #888; font-size: 0.9em;">
            Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
            Powered by PEAK Recruiting
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
