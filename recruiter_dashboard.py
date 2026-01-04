"""
PEAKATS Recruiter Dashboard - CLOUD VERSION
Custom column layout with G/M form tracking
Connects to Supabase PostgreSQL
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import os
from sqlalchemy import create_engine, text

# Page config
st.set_page_config(
    page_title="PEAKATS Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
def get_db_url():
    """Get database URL from secrets or environment"""
    try:
        return st.secrets["database"]["url"]
    except:
        return os.environ.get('SUPABASE_DB_URL')

@st.cache_resource
def get_database_engine():
    """Get SQLAlchemy engine for cloud database"""
    db_url = get_db_url()
    if not db_url:
        st.error("❌ Database not configured. Check secrets or SUPABASE_DB_URL.")
        return None
    return create_engine(db_url)

def get_connection():
    """Get a new database connection"""
    engine = get_database_engine()
    if engine:
        return engine.connect()
    return None

# Data loading
def load_candidates():
    """Load all candidates from database - NO CACHING"""
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    query = """
    SELECT 
        id,
        first_name,
        last_name,
        client_id,
        email,
        phone,
        COALESCE(fedex_id, '') as fedex_id,
        COALESCE(application_date, '') as initiated,
        COALESCE(rwp_score, 0) as rwp_score,
        COALESCE(rwp_classification, 'N/A') as rwp_classification,
        COALESCE(resume_notes, '') as ai_notes,
        COALESCE(background_status, 'Not Started') as bg_status,
        COALESCE(background_id, '') as bg_id,
        COALESCE(drug_test_status, 'Not Started') as drug_status,
        COALESCE(drug_test_id, '') as drug_id,
        COALESCE(profile_status, 'Not Started') as profile_status,
        COALESCE(legacy_order_status, 'Not Started') as order_status,
        COALESCE(recruiter_notes, '') as recruiter_notes,
        COALESCE(gcic_uploaded, 0) as g,
        COALESCE(mec_uploaded, 0) as m,
        COALESCE(gcic_upload_date, '') as g_date,
        COALESCE(mec_upload_date, '') as m_date,
        COALESCE(status, 'new') as status,
        COALESCE(intake_date, '') as intake_date,
        COALESCE(updated_at, '') as updated,
        COALESCE(fadv_change_flag, 0) as flag,
        COALESCE(fadv_change_details, '') as flag_details,
        COALESCE(fadv_last_updated, '') as flag_date,
        resume_filename
    FROM candidates
    ORDER BY fadv_change_flag DESC, intake_date DESC
    """
    
    df = pd.read_sql_query(text(query), conn)
    conn.close()
    return df

def update_candidate_notes(candidate_id, notes):
    """Update recruiter notes for a candidate and auto-clear FADV flag"""
    conn = get_connection()
    if not conn:
        return
    conn.execute(text("""
        UPDATE candidates 
        SET recruiter_notes = :notes,
            fadv_change_flag = 0,
            updated_at = NOW()
        WHERE id = :id
    """), {"notes": notes, "id": candidate_id})
    conn.commit()
    conn.close()

def clear_fadv_flag(candidate_id):
    """Manually clear FADV change flag"""
    conn = get_connection()
    if not conn:
        return
    conn.execute(text("""
        UPDATE candidates 
        SET fadv_change_flag = 0,
            updated_at = NOW()
        WHERE id = :id
    """), {"id": candidate_id})
    conn.commit()
    conn.close()

def update_candidate_status(candidate_id, status):
    """Update candidate status"""
    conn = get_connection()
    if not conn:
        return
    conn.execute(text("""
        UPDATE candidates 
        SET status = :status,
            updated_at = NOW()
        WHERE id = :id
    """), {"status": status, "id": candidate_id})
    conn.commit()
    conn.close()

def update_gcic(candidate_id, checked):
    """Update GCIC form upload status"""
    conn = get_connection()
    if not conn:
        return
    upload_date = datetime.now().isoformat() if checked else None
    conn.execute(text("""
        UPDATE candidates 
        SET gcic_uploaded = :uploaded,
            gcic_upload_date = :upload_date,
            updated_at = NOW()
        WHERE id = :id
    """), {"uploaded": 1 if checked else 0, "upload_date": upload_date, "id": candidate_id})
    conn.commit()
    conn.close()

def update_mec(candidate_id, checked):
    """Update MEC form upload status"""
    conn = get_connection()
    if not conn:
        return
    upload_date = datetime.now().isoformat() if checked else None
    conn.execute(text("""
        UPDATE candidates 
        SET mec_uploaded = :uploaded,
            mec_upload_date = :upload_date,
            updated_at = NOW()
        WHERE id = :id
    """), {"uploaded": 1 if checked else 0, "upload_date": upload_date, "id": candidate_id})
    conn.commit()
    conn.close()

def update_fedex_id(candidate_id, fedex_id):
    """Update FedEx ID for a candidate"""
    conn = get_connection()
    if not conn:
        return
    conn.execute(text("""
        UPDATE candidates 
        SET fedex_id = :fedex_id,
            updated_at = NOW()
        WHERE id = :id
    """), {"fedex_id": fedex_id if fedex_id else None, "id": candidate_id})
    conn.commit()
    conn.close()

# Initialize session state
if 'selected_candidate' not in st.session_state:
    st.session_state.selected_candidate = None
if 'show_detail' not in st.session_state:
    st.session_state.show_detail = False

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .stCheckbox label {
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">📊 PEAKATS Recruiter Dashboard</h1>', unsafe_allow_html=True)
    
    # Load data
    df = load_candidates()
    
    # Sidebar - Filters
    with st.sidebar:
        st.header("🔍 Filters")
        
        # Search
        search = st.text_input("Search", placeholder="Name, email, phone...")
        
        # Client filter
        clients = ['All'] + sorted(df['client_id'].unique().tolist())
        client_filter = st.selectbox("Client", clients)
        
        # RWP filter
        rwp_range = st.slider("RWP Score Range", 0, 10, (0, 10))
        
        # Status filter
        statuses = ['All'] + sorted(df['status'].unique().tolist())
        status_filter = st.selectbox(
            "Recruiting Status",
            statuses,
            help="Track recruiting pipeline: New → Contacted → Scheduled → Hired/Rejected"
        )
        
        st.divider()
        st.subheader("FADV Filters")
        
        # Flag filter
        show_flagged_only = st.checkbox("🚩 Show only FADV changes", value=False)
        
        # Order Status filter
        order_statuses = ['All'] + sorted(df['order_status'].unique().tolist())
        order_filter = st.selectbox("Order Status", order_statuses)
        
        # Profile Status filter
        profile_statuses = ['All'] + sorted(df['profile_status'].unique().tolist())
        profile_filter = st.selectbox("Profile Status", profile_statuses)
        
        # Background Status filter
        bg_statuses = ['All'] + sorted(df['bg_status'].unique().tolist())
        bg_filter = st.selectbox("Background Status", bg_statuses)
        
        # Drug Status filter
        drug_statuses = ['All'] + sorted(df['drug_status'].unique().tolist())
        drug_filter = st.selectbox("Drug Status", drug_statuses)
        
        st.divider()
        
        # G/M filters
        st.subheader("Form Status")
        show_g = st.checkbox("Has GCIC (G)", value=True)
        show_no_g = st.checkbox("No GCIC", value=True)
        show_m = st.checkbox("Has MEC (M)", value=True)
        show_no_m = st.checkbox("No MEC", value=True)
        
        st.divider()
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
    
    # Apply filters
    filtered_df = df.copy()
    
    # Search filter
    if search:
        mask = (
            filtered_df['first_name'].str.contains(search, case=False, na=False) |
            filtered_df['last_name'].str.contains(search, case=False, na=False) |
            filtered_df['email'].str.contains(search, case=False, na=False) |
            filtered_df['phone'].str.contains(search, case=False, na=False) |
            filtered_df['client_id'].str.contains(search, case=False, na=False)
        )
        filtered_df = filtered_df[mask]
    
    # Client filter
    if client_filter != 'All':
        filtered_df = filtered_df[filtered_df['client_id'] == client_filter]
    
    # RWP filter
    filtered_df = filtered_df[
        (filtered_df['rwp_score'] >= rwp_range[0]) & 
        (filtered_df['rwp_score'] <= rwp_range[1])
    ]
    
    # Status filter
    if status_filter != 'All':
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    # Order Status filter
    if order_filter != 'All':
        filtered_df = filtered_df[filtered_df['order_status'] == order_filter]
    
    # Profile Status filter
    if profile_filter != 'All':
        filtered_df = filtered_df[filtered_df['profile_status'] == profile_filter]
    
    # Background Status filter
    if bg_filter != 'All':
        filtered_df = filtered_df[filtered_df['bg_status'] == bg_filter]
    
    # Drug Status filter
    if drug_filter != 'All':
        filtered_df = filtered_df[filtered_df['drug_status'] == drug_filter]
    
    # Flag filter
    if show_flagged_only:
        filtered_df = filtered_df[filtered_df['flag'] == 1]
    
    # G/M filters
    g_m_conditions = []
    if show_g:
        g_m_conditions.append(filtered_df['g'] == 1)
    if show_no_g:
        g_m_conditions.append(filtered_df['g'] == 0)
    if show_m:
        g_m_conditions.append(filtered_df['m'] == 1)
    if show_no_m:
        g_m_conditions.append(filtered_df['m'] == 0)
    
    if g_m_conditions:
        filtered_df = filtered_df[pd.concat(g_m_conditions, axis=1).any(axis=1)]
    
    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Candidates", len(df))
    
    with col2:
        st.metric("Showing", len(filtered_df))
    
    with col3:
        avg_rwp = filtered_df[filtered_df['rwp_score'] > 0]['rwp_score'].mean()
        st.metric("Avg RWP", f"{avg_rwp:.1f}" if not pd.isna(avg_rwp) else "N/A")
    
    with col4:
        flagged = len(df[df['flag'] == 1])
        st.metric("🚩 FADV Changes", flagged)
    
    st.divider()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 Candidate List", "📊 Analytics", "📥 Export"])
    
    with tab1:
        # Candidate table
        if len(filtered_df) == 0:
            st.warning("No candidates match your filters.")
        else:
            st.subheader(f"Candidates ({len(filtered_df)})")
            
            # Prepare display dataframe with custom columns including G/M and Flag
            display_df = filtered_df[[
                'flag', 'first_name', 'last_name', 'client_id', 'fedex_id', 'initiated', 'recruiter_notes',
                'g', 'm', 'rwp_score', 'order_status', 'profile_status',
                'bg_id', 'bg_status', 'drug_id', 'drug_status', 'phone', 'email'
            ]].copy()
            
            # Rename columns
            display_df.columns = [
                '🚩', 'First Name', 'Last Name', 'Client', 'FedEx ID', 'Initiated', 'Notes',
                'G', 'M', 'RWP', 'Order Status', 'Profile Status',
                'Background-ID', 'Background-Status', 'Drug-ID', 'Drug-Status', 'Phone', 'Email'
            ]
            
            # Store original IDs and raw values for reference
            display_df.insert(0, '_id', filtered_df['id'].values)
            display_df.insert(1, '_g_raw', filtered_df['g'].values)
            display_df.insert(2, '_m_raw', filtered_df['m'].values)
            display_df.insert(3, '_flag_raw', filtered_df['flag'].values)
            
            # Convert flag to emoji
            display_df['🚩'] = filtered_df['flag'].apply(lambda x: '⚠️' if x == 1 else '')
            
            # Convert G/M to boolean for checkboxes
            display_df['G'] = filtered_df['g'].apply(lambda x: bool(x))
            display_df['M'] = filtered_df['m'].apply(lambda x: bool(x))
            
            # Truncate notes for table display
            display_df['Notes'] = display_df['Notes'].apply(
                lambda x: (x[:50] + '...') if len(str(x)) > 50 else x
            )
            
            # Make table editable with data_editor
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=600,
                disabled=['_id', '_g_raw', '_m_raw', '_flag_raw', '🚩', 'First Name', 'Last Name', 'Client', 'Initiated',
                         'RWP', 'Order Status', 'Profile Status', 'Background-ID',
                         'Background-Status', 'Drug-ID', 'Drug-Status', 'Phone', 'Email'],
                column_config={
                    '_id': None,  # Hide ID column
                    '_g_raw': None,  # Hide raw G value
                    '_m_raw': None,  # Hide raw M value
                    '_flag_raw': None,  # Hide raw flag value
                    '🚩': st.column_config.TextColumn(
                        '🚩',
                        help='FADV status changed - click candidate to see details',
                        width='small'
                    ),
                    'FedEx ID': st.column_config.TextColumn(
                        'FedEx ID',
                        help='Enter FedEx ID when assigned',
                        max_chars=20,
                        width='small'
                    ),
                    'Notes': st.column_config.TextColumn(
                        'Notes',
                        help='Click to edit recruiter notes (auto-clears flag)',
                        max_chars=500,
                        width='large'
                    ),
                    'G': st.column_config.CheckboxColumn(
                        'G',
                        help='GCIC Form uploaded to FADV',
                        default=False
                    ),
                    'M': st.column_config.CheckboxColumn(
                        'M',
                        help='MEC Form uploaded to FADV',
                        default=False
                    )
                }
            )
            
            # Detect changes and save
            if edited_df is not None:
                changes_made = False
                
                for idx in range(len(edited_df)):
                    candidate_id = int(edited_df.iloc[idx]['_id'])
                    
                    # Check for note changes
                    # Get FULL original notes from filtered_df (not truncated display)
                    original_notes_full = str(filtered_df.iloc[idx]['recruiter_notes']).strip()
                    edited_notes = str(edited_df.iloc[idx]['Notes']).strip()
                    
                    # Remove "nan" from comparison
                    if original_notes_full == 'nan':
                        original_notes_full = ''
                    if edited_notes == 'nan':
                        edited_notes = ''
                    
                    # Save if actually different
                    if edited_notes != original_notes_full:
                        update_candidate_notes(candidate_id, edited_notes)
                        changes_made = True
                        print(f"DEBUG: Saved notes for candidate {candidate_id}: '{edited_notes}'")
                    
                    # Check for FedEx ID changes
                    original_fedex = str(filtered_df.iloc[idx]['fedex_id']).strip()
                    edited_fedex = str(edited_df.iloc[idx]['FedEx ID']).strip()
                    
                    if original_fedex == 'nan':
                        original_fedex = ''
                    if edited_fedex == 'nan':
                        edited_fedex = ''
                    
                    if edited_fedex != original_fedex:
                        update_fedex_id(candidate_id, edited_fedex)
                        changes_made = True
                        print(f"DEBUG: Saved FedEx ID for candidate {candidate_id}: '{edited_fedex}'")
                    
                    # Check for G checkbox changes
                    original_g = bool(int(edited_df.iloc[idx]['_g_raw']))
                    edited_g = bool(edited_df.iloc[idx]['G'])
                    
                    if edited_g != original_g:
                        update_gcic(candidate_id, edited_g)
                        changes_made = True
                    
                    # Check for M checkbox changes
                    original_m = bool(int(edited_df.iloc[idx]['_m_raw']))
                    edited_m = bool(edited_df.iloc[idx]['M'])
                    
                    if edited_m != original_m:
                        update_mec(candidate_id, edited_m)
                        changes_made = True
                
                if changes_made:
                    st.success("✓ Changes saved to cloud database!")
                    # Don't auto-refresh - let user continue editing
                    # User can click "Refresh Data" button when ready
            
            # Manual refresh button
            col_refresh, col_tip = st.columns([1, 4])
            with col_refresh:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.rerun()
            with col_tip:
                st.caption("💡 Tip: ⚠️ = FADV status changed. Edits save instantly. Click 'Refresh Data' to see latest from all users.")
            
            # Add row selector for detail view
            st.divider()
            col1, col2 = st.columns([3, 1])
            with col1:
                candidate_names = [f"{row['first_name']} {row['last_name']}" for _, row in filtered_df.iterrows()]
                selected_name = st.selectbox(
                    "View candidate details:",
                    ['Select a candidate...'] + candidate_names,
                    key='candidate_selector'
                )
            
            with col2:
                if st.button("View Details", disabled=(selected_name == 'Select a candidate...'), use_container_width=True):
                    # Find candidate ID
                    for idx, row in filtered_df.iterrows():
                        if f"{row['first_name']} {row['last_name']}" == selected_name:
                            st.session_state.selected_candidate = row['id']
                            st.session_state.show_detail = True
                            st.rerun()
    
    with tab2:
        # Analytics
        st.subheader("📊 Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # RWP Distribution
            st.markdown("**RWP Score Distribution**")
            rwp_dist = filtered_df[filtered_df['rwp_score'] > 0]['rwp_score'].value_counts().sort_index()
            st.bar_chart(rwp_dist)
        
        with col2:
            # Client Breakdown
            st.markdown("**Candidates by Client**")
            client_dist = filtered_df['client_id'].value_counts()
            st.bar_chart(client_dist)
        
        col3, col4 = st.columns(2)
        
        with col3:
            # G/M Status
            st.markdown("**FADV Forms Uploaded**")
            form_data = pd.DataFrame({
                'Form': ['GCIC (G)', 'MEC (M)'],
                'Count': [
                    len(filtered_df[filtered_df['g'] == 1]),
                    len(filtered_df[filtered_df['m'] == 1])
                ]
            })
            st.bar_chart(form_data.set_index('Form'))
        
        with col4:
            # Background Status
            st.markdown("**Background Check Status**")
            bg_dist = filtered_df['bg_status'].value_counts()
            st.bar_chart(bg_dist)
    
    with tab3:
        # Export
        st.subheader("📥 Export Data")
        
        st.write(f"Exporting {len(filtered_df)} candidates with current filters applied.")
        
        # Prepare export with specified columns
        export_df = filtered_df[[
            'client_id', 'first_name', 'last_name', 'initiated', 
            'recruiter_notes', 'g', 'm', 'rwp_score', 'order_status',
            'updated', 'profile_status', 'bg_id', 'bg_status',
            'drug_id', 'drug_status', 'phone'
        ]].copy()
        
        # Rename columns for export
        export_df.columns = [
            'Client Name', 'First Name', 'Last Name', 'Initiated',
            'Notes', 'G', 'M', 'RWP', 'Order Status',
            'Updated', 'Profile Status', 'Background-ID', 'Background-Status',
            'Drug-ID', 'Drug-Status', 'Phone'
        ]
        
        # Convert G/M to Yes/No
        export_df['G'] = export_df['G'].apply(lambda x: 'Yes' if x == 1 else 'No')
        export_df['M'] = export_df['M'].apply(lambda x: 'Yes' if x == 1 else 'No')
        
        # Download button
        csv = export_df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"PEAKATS_Export_{timestamp}.csv"
        
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
        # Preview
        st.markdown("**Preview:**")
        st.dataframe(export_df.head(10), use_container_width=True)
    
    # Candidate detail modal (sidebar)
    if st.session_state.show_detail and st.session_state.selected_candidate:
        candidate = df[df['id'] == st.session_state.selected_candidate].iloc[0]
        
        with st.sidebar:
            st.divider()
            st.header("👤 Candidate Details")
            
            # Close button
            if st.button("✕ Close", use_container_width=True):
                st.session_state.show_detail = False
                st.session_state.selected_candidate = None
                st.rerun()
            
            st.subheader(f"{candidate['first_name']} {candidate['last_name']}")
            st.caption(f"Client: {candidate['client_id']}")
            
            # FADV Change Flag (if present)
            if candidate['flag'] == 1:
                with st.expander("🚩 FADV STATUS CHANGED", expanded=True):
                    st.warning(candidate['flag_details'])
                    if candidate['flag_date']:
                        st.caption(f"Updated: {candidate['flag_date'][:19]}")
                    
                    if st.button("✓ Mark as Reviewed", use_container_width=True, type="primary"):
                        clear_fadv_flag(candidate['id'])
                        st.success("Flag cleared!")
                        st.rerun()
                    
                    st.info("💡 Flag auto-clears when you add/edit notes below")
            
            # Contact Info
            with st.expander("📧 Contact Information", expanded=True):
                st.write(f"**Email:** {candidate['email']}")
                st.write(f"**Phone:** {candidate['phone']}")
                st.write(f"**Applied:** {candidate['initiated']}")
            
            # RWP Intelligence
            with st.expander("🎯 Resume Intelligence", expanded=True):
                rwp = int(candidate['rwp_score'])
                st.metric("RWP Score", rwp)
                st.write(f"**Classification:** {candidate['rwp_classification']}")
                if candidate['ai_notes']:
                    st.write("**AI Notes:**")
                    st.info(candidate['ai_notes'])
            
            # FADV Status
            with st.expander("✅ Background Check", expanded=True):
                st.write(f"**Profile:** {candidate['profile_status']}")
                st.write(f"**Order:** {candidate['order_status']}")
                st.write(f"**Background ID:** {candidate['bg_id'] or 'Not Assigned'}")
                st.write(f"**Background:** {candidate['bg_status']}")
                st.write(f"**Drug ID:** {candidate['drug_id'] or 'Not Assigned'}")
                st.write(f"**Drug Screen:** {candidate['drug_status']}")
            
            # FADV Forms (G/M) - EDITABLE
            with st.expander("📋 FADV Forms", expanded=True):
                st.write("**Form Upload Status:**")
                
                # GCIC checkbox
                g_checked = st.checkbox(
                    "✓ GCIC Form Uploaded (G)",
                    value=bool(candidate['g']),
                    key=f"g_{candidate['id']}"
                )
                if g_checked != bool(candidate['g']):
                    update_gcic(candidate['id'], g_checked)
                    st.success("GCIC status updated!")
                    st.rerun()
                
                if candidate['g_date']:
                    st.caption(f"Uploaded: {candidate['g_date'][:10]}")
                
                # MEC checkbox
                m_checked = st.checkbox(
                    "✓ MEC Form Uploaded (M)",
                    value=bool(candidate['m']),
                    key=f"m_{candidate['id']}"
                )
                if m_checked != bool(candidate['m']):
                    update_mec(candidate['id'], m_checked)
                    st.success("MEC status updated!")
                    st.rerun()
                
                if candidate['m_date']:
                    st.caption(f"Uploaded: {candidate['m_date'][:10]}")
            
            # Recruiter Notes (Editable)
            with st.expander("📝 Recruiter Notes", expanded=True):
                notes = st.text_area(
                    "Notes",
                    value=candidate['recruiter_notes'],
                    height=150,
                    key=f"notes_{candidate['id']}",
                    label_visibility="collapsed"
                )
                
                if st.button("💾 Save Notes", use_container_width=True):
                    update_candidate_notes(candidate['id'], notes)
                    st.success("Notes saved!")
                    st.rerun()
            
            # Status Update
            with st.expander("🏷️ Update Status", expanded=True):
                new_status = st.selectbox(
                    "Status",
                    ['new', 'contacted', 'scheduled', 'hired', 'rejected'],
                    index=['new', 'contacted', 'scheduled', 'hired', 'rejected'].index(candidate['status']),
                    key=f"status_{candidate['id']}",
                    label_visibility="collapsed"
                )
                
                if st.button("💾 Update Status", use_container_width=True):
                    update_candidate_status(candidate['id'], new_status)
                    st.success("Status updated!")
                    st.rerun()

if __name__ == "__main__":
    main()
