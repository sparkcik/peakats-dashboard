"""PEAKATS Dashboard v8 - Edit Modal for Editable Columns"""

import reflex as rx
from typing import List
from datetime import datetime

DB_URL = "postgresql://postgres.eyopvsmsvbgfuffscfom:peakats2026@aws-0-us-west-2.pooler.supabase.com:6543/postgres?sslmode=require"

# Password for dashboard access
DASHBOARD_PASSWORD = "peak2113"

# Client name mapping for polished display (alphabetical)
CLIENT_NAMES = {
    "cbm": "CBM",
    "dd_networks": "DD Networks",
    "excel_route": "Excel Route",
    "excellus": "Excellus",
    "excellus_delivery": "Excellus Delivery",
    "james_elite": "James Elite",
    "jcb": "JCB",
    "rm_iv": "RM IV",
    "smart_route": "Smart Route",
    "solpac": "Solpac",
    "star_one": "Star One",
    "woodstock": "Woodstock",
}


def format_client(client_id: str) -> str:
    """Convert client_id to polished display name"""
    return CLIENT_NAMES.get(client_id.lower(), client_id)


def format_date(dt_str: str) -> str:
    """Convert date string to YY/MM/DD format"""
    if not dt_str or len(dt_str) < 10:
        return ""
    try:
        return f"{dt_str[2:4]}/{dt_str[5:7]}/{dt_str[8:10]}"
    except:
        return dt_str[:10]


# Status normalization maps
BG_STATUS_MAP = {
    '': 'Not Started',
    'None': 'Not Started',
    'Not Started': 'Not Started',
    'In Progress': 'In Progress',
    'In Progress*': 'In Progress',
    'In Progress**': 'In Progress',
    'Needs further review**': 'Needs Review',
    'In-Eligible For Hire*': 'Ineligible',
    'Eligible': 'Eligible',
    'Case Canceled': 'Canceled',
    'Under Review': 'Under Review',
}

DRUG_STATUS_MAP = {
    '': 'Not Started',
    'None': 'Not Started',
    'Not Started': 'Not Started',
    'Negative/Pass': 'Pass',
    'Positive/Fail*': 'Fail',
    'Order Received': 'In Progress',
    'Collection Complete': 'In Progress',
    'Collection Event Review': 'In Progress',
    'Order Expired/Donor No Show**': 'Expired',
    'Cancel**': 'Canceled',
}


def normalize_bg_status(status: str) -> str:
    """Normalize background status for display"""
    return BG_STATUS_MAP.get(status, status)


def normalize_drug_status(status: str) -> str:
    """Normalize drug status for display"""
    return DRUG_STATUS_MAP.get(status, status)


def get_flag_type(flag_details: str) -> str:
    """Categorize flag by change type for filtering"""
    if not flag_details:
        return ""
    details_lower = flag_details.lower()
    if 'eligible' in details_lower:
        return "Eligible"
    if 'negative' in details_lower or 'pass' in details_lower:
        return "Pass"
    if 'needs' in details_lower or 'review' in details_lower:
        return "Needs Review"
    if 'ineligible' in details_lower or 'fail' in details_lower or 'positive' in details_lower:
        return "Failed"
    return "Other"


class Candidate(rx.Base):
    id: int = 0
    first_name: str = ""
    last_name: str = ""
    client_id: str = ""
    client_display: str = ""
    email: str = ""
    phone: str = ""
    fedex_id: str = ""
    rwp_score: float = 0.0
    rwp_classification: str = ""
    rwp_rationale: str = ""
    background_status: str = ""
    background_status_raw: str = ""
    background_id: str = ""
    bg_override: int = 0
    drug_test_status: str = ""
    drug_test_status_raw: str = ""
    drug_test_id: str = ""
    drug_override: int = 0
    profile_status: str = ""
    status: str = ""
    tag: str = "Driver"
    recruiter_notes: str = ""
    gcic: int = 0
    mec: int = 0
    qcert: int = 0
    rtest: int = 0
    dl: int = 0
    flag: int = 0
    flag_details: str = ""
    flag_type: str = ""
    reject_reason: str = ""
    created_at: str = ""
    updated_at: str = ""


class State(rx.State):
    candidates: List[Candidate] = []
    filtered_candidates: List[Candidate] = []
    loading: bool = False
    error: str = ""
    success_message: str = ""
    
    # Filters (all single-select)
    search_query: str = ""
    client_filter: str = "All"
    profile_filter: str = "All"
    flag_filter: str = "All"
    rwp_filter: str = "All"
    status_filter: str = "⚡ All Active"  # Default excludes Intake
    bg_filter: str = "All"
    drug_filter: str = "All"
    tag_filter: str = "All"
    created_filter: str = "All"
    
    # Authentication
    authenticated: bool = False
    password_input: str = ""
    auth_error: str = ""
    
    def check_password(self):
        """Verify password and authenticate"""
        if self.password_input == DASHBOARD_PASSWORD:
            self.authenticated = True
            self.auth_error = ""
            self.load_data()
        else:
            self.auth_error = "Invalid password"
            self.password_input = ""
    
    # Filter options
    client_options: List[str] = ["All"]
    status_options: List[str] = ["All", "⚡ All Active", "Intake", "Unranked", "Active", "On Deck", "Followup", "Hired", "Transferred", "Rejected"]
    tag_options: List[str] = ["All", "Driver", "Manager"]
    bg_options: List[str] = ["All"]
    drug_options: List[str] = ["All"]
    profile_options: List[str] = ["All"]
    flag_options: List[str] = ["All", "Flagged", "Eligible", "Pass", "Needs Review", "Failed", "Other"]
    rwp_options: List[str] = ["All", "11.0", "10.0", "9.0", "6.0", "3.0", "0.0"]
    created_options: List[str] = ["All", "< 30 days", "< 60 days", "< 90 days", "> 30 days", "> 60 days", "> 90 days"]
    
    # Sorting
    sort_column: str = ""
    sort_ascending: bool = True
    
    # Stats
    bg_eligible_count: int = 0
    drug_eligible_count: int = 0
    
    # Multi-select
    selected_ids: List[int] = []
    
    # Batch action state
    show_batch_status: bool = False
    show_batch_note: bool = False
    show_batch_tag: bool = False
    batch_status_value: str = "Active"
    batch_note_value: str = ""
    batch_tag_value: str = "Driver"
    
    # Merge modal state
    show_merge_modal: bool = False
    merge_candidate_1: dict = {}
    merge_candidate_2: dict = {}
    merge_primary: int = 0  # ID of primary record to keep
    
    # Pagination
    page: int = 0
    page_size: int = 50
    
    # Edit modal state
    show_edit_modal: bool = False
    editing_id: int = 0
    editing_name: str = ""
    edit_notes: str = ""
    edit_phone: str = ""
    edit_email: str = ""
    edit_client: str = ""
    edit_gcic: bool = False
    edit_mec: bool = False
    edit_qcert: bool = False
    edit_rtest: bool = False
    edit_dl: bool = False
    edit_bg_override: bool = False
    edit_drug_override: bool = False
    edit_fedex: str = ""
    edit_status: str = "Active"
    edit_reject_reason: str = ""
    edit_tag: str = "Driver"
    edit_clear_flag: bool = False
    editing_has_flag: bool = False
    confirm_delete: bool = False
    
    def toggle_confirm_delete(self):
        self.confirm_delete = not self.confirm_delete
    
    def load_data(self):
        print(">>> LOAD_DATA CALLED <<<")
        self.loading = True
        self.error = ""
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            query = """
                SELECT 
                    id, first_name, last_name, client_id, email, phone,
                    COALESCE(fedex_id, '') as fedex_id,
                    COALESCE(rwp_score, 0) as rwp_score,
                    COALESCE(rwp_classification, 'N/A') as rwp_classification,
                    COALESCE(rwp_rationale, '') as rwp_rationale,
                    COALESCE(background_status, 'Not Started') as background_status,
                    COALESCE(background_id, '') as background_id,
                    COALESCE(bg_override, 0) as bg_override,
                    COALESCE(drug_test_status, 'Not Started') as drug_test_status,
                    COALESCE(drug_test_id, '') as drug_test_id,
                    COALESCE(drug_override, 0) as drug_override,
                    COALESCE(profile_status, 'Not Started') as profile_status,
                    COALESCE(status, 'Active') as status,
                    COALESCE(tag, 'Driver') as tag,
                    COALESCE(recruiter_notes, '') as recruiter_notes,
                    COALESCE(gcic_uploaded, 0) as gcic,
                    COALESCE(mec_uploaded, 0) as mec,
                    COALESCE(qcert_uploaded, 0) as qcert,
                    COALESCE(rtest_completed, 0) as rtest,
                    COALESCE(dl_verified, 0) as dl,
                    COALESCE(fadv_change_flag, 0) as flag,
                    COALESCE(fadv_change_details, '') as flag_details,
                    COALESCE(created_at::text, '') as created_at,
                    COALESCE(updated_at::text, '') as updated_at,
                    COALESCE(reject_reason, '') as reject_reason
                FROM candidates
                ORDER BY fadv_change_flag DESC, id DESC
            """
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                print(f">>> GOT {len(rows)} ROWS <<<")
                
                self.candidates = []
                clients_set = set()
                bg_set = set()
                drug_set = set()
                profile_set = set()
                
                bg_eligible = 0
                drug_eligible = 0
                
                for row in rows:
                    client_id = row[3] or ""
                    bg_status_raw = row[10] or ""
                    bg_override = int(row[12] or 0)
                    drug_status_raw = row[13] or ""
                    drug_override = int(row[15] or 0)
                    flag_details = row[26] or ""
                    
                    status_val = row[17] or "Active"
                    # Normalize 'new' to 'Active'
                    if status_val.lower() == "new":
                        status_val = "Active"
                    
                    # Normalize statuses for display
                    bg_status = normalize_bg_status(bg_status_raw)
                    drug_status = normalize_drug_status(drug_status_raw)
                    
                    c = Candidate(
                        id=row[0],
                        first_name=row[1] or "",
                        last_name=row[2] or "",
                        client_id=client_id,
                        client_display=format_client(client_id),
                        email=row[4] or "",
                        phone=row[5] or "",
                        fedex_id=row[6] or "",
                        rwp_score=float(row[7] or 0),
                        rwp_classification=row[8] or "",
                        rwp_rationale=row[9] or "",
                        background_status=bg_status,
                        background_status_raw=bg_status_raw,
                        background_id=row[11] or "",
                        bg_override=bg_override,
                        drug_test_status=drug_status,
                        drug_test_status_raw=drug_status_raw,
                        drug_test_id=row[14] or "",
                        drug_override=drug_override,
                        profile_status=row[16] or "",
                        status=status_val,
                        tag=row[18] or "Driver",
                        recruiter_notes=row[19] or "",
                        gcic=int(row[20] or 0),
                        mec=int(row[21] or 0),
                        qcert=int(row[22] or 0),
                        rtest=int(row[23] or 0),
                        dl=int(row[24] or 0),
                        flag=int(row[25] or 0),
                        flag_details=flag_details,
                        flag_type=get_flag_type(flag_details),
                        created_at=format_date(row[27] or ""),
                        updated_at=format_date(row[28] or ""),
                        reject_reason=row[29] or "",
                    )
                    self.candidates.append(c)
                    
                    # Count eligibles (using normalized values OR overrides)
                    if bg_status == "Eligible" or bg_override == 1:
                        bg_eligible += 1
                    if drug_status == "Pass" or drug_override == 1:
                        drug_eligible += 1
                    
                    if c.client_display:
                        clients_set.add(c.client_display)
                    if c.background_status:
                        bg_set.add(c.background_status)
                    if c.drug_test_status:
                        drug_set.add(c.drug_test_status)
                    if c.profile_status:
                        profile_set.add(c.profile_status)
                
                self.bg_eligible_count = bg_eligible
                self.drug_eligible_count = drug_eligible
                self.client_options = ["All"] + sorted(list(clients_set), key=str.lower)
                # Add combo option at top, then individual values
                self.bg_options = ["All", "⚡ All Active"] + sorted(list(bg_set))
                self.drug_options = ["All", "⚡ All Active"] + sorted(list(drug_set))
                self.profile_options = ["All"] + sorted(list(profile_set))
                self.filtered_candidates = self.candidates
                    
        except Exception as e:
            print(f">>> ERROR: {e} <<<")
            self.error = str(e)
        
        self.loading = False
    
    def apply_filters(self):
        filtered = self.candidates
        
        if self.search_query:
            q = self.search_query.lower()
            filtered = [c for c in filtered if 
                q in c.first_name.lower() or
                q in c.last_name.lower() or
                q in c.email.lower() or
                q in c.phone or
                q in c.fedex_id.lower() or
                q in c.recruiter_notes.lower()]
        
        if self.client_filter != "All":
            filtered = [c for c in filtered if c.client_display == self.client_filter]
        
        if self.status_filter == "⚡ All Active":
            # Combo: Active statuses (excludes Unranked, Transferred, Hired, Rejected)
            filtered = [c for c in filtered if c.status not in ["Unranked", "Transferred", "Hired", "Rejected"]]
        elif self.status_filter != "All":
            filtered = [c for c in filtered if c.status == self.status_filter]
        
        if self.tag_filter != "All":
            filtered = [c for c in filtered if c.tag == self.tag_filter]
        
        # Background filter with combo option (includes overrides)
        if self.bg_filter == "⚡ All Active":
            # Combo: Eligible, In Progress, Needs Review, Needs further review** + overrides
            active_statuses = ["Eligible", "In Progress", "In Progress*", "In Progress**", 
                              "Needs Review", "Needs further review**", "Order Received"]
            filtered = [c for c in filtered if c.background_status in active_statuses or c.bg_override == 1]
        elif self.bg_filter == "Eligible":
            # Eligible status OR override checked
            filtered = [c for c in filtered if c.background_status == "Eligible" or c.bg_override == 1]
        elif self.bg_filter != "All":
            filtered = [c for c in filtered if c.background_status == self.bg_filter]
        
        # Drug filter with combo option (includes overrides)
        if self.drug_filter == "⚡ All Active":
            # Combo: Eligible (Negative/Pass), In Progress, Order Received + overrides
            active_statuses = ["Negative/Pass", "In Progress", "Order Received", "Collection Complete"]
            filtered = [c for c in filtered if c.drug_test_status in active_statuses or c.drug_override == 1]
        elif self.drug_filter == "Negative/Pass":
            # Pass status OR override checked
            filtered = [c for c in filtered if c.drug_test_status == "Negative/Pass" or c.drug_override == 1]
        elif self.drug_filter != "All":
            filtered = [c for c in filtered if c.drug_test_status == self.drug_filter]
        
        if self.profile_filter != "All":
            filtered = [c for c in filtered if c.profile_status == self.profile_filter]
        
        # Flag filter
        if self.flag_filter == "Flagged":
            filtered = [c for c in filtered if c.flag == 1]
        elif self.flag_filter != "All":
            filtered = [c for c in filtered if c.flag_type == self.flag_filter]
        
        # RWP filter
        if self.rwp_filter != "All":
            rwp_val = float(self.rwp_filter)
            filtered = [c for c in filtered if c.rwp_score == rwp_val]
        
        # Created date filter
        if self.created_filter != "All":
            from datetime import datetime, timedelta
            today = datetime.now()
            
            def parse_date(date_str):
                """Parse YY/MM/DD format to datetime"""
                if not date_str or len(date_str) < 8:
                    return None
                try:
                    # Format is YY/MM/DD
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        year = int('20' + parts[0])
                        month = int(parts[1])
                        day = int(parts[2])
                        return datetime(year, month, day)
                except:
                    pass
                return None
            
            if self.created_filter == "< 30 days":
                cutoff = today - timedelta(days=30)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) >= cutoff]
            elif self.created_filter == "< 60 days":
                cutoff = today - timedelta(days=60)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) >= cutoff]
            elif self.created_filter == "< 90 days":
                cutoff = today - timedelta(days=90)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) >= cutoff]
            elif self.created_filter == "> 30 days":
                cutoff = today - timedelta(days=30)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) < cutoff]
            elif self.created_filter == "> 60 days":
                cutoff = today - timedelta(days=60)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) < cutoff]
            elif self.created_filter == "> 90 days":
                cutoff = today - timedelta(days=90)
                filtered = [c for c in filtered if parse_date(c.created_at) and parse_date(c.created_at) < cutoff]
        
        self.filtered_candidates = filtered
        self.page = 0  # Reset to first page when filters change
        self._apply_sort()
    
    def _apply_sort(self):
        if not self.sort_column:
            return
        
        def get_sort_key(c):
            col = self.sort_column
            if col == "flag":
                return c.flag
            elif col == "client":
                return c.client_display.lower()
            elif col == "created":
                return c.created_at
            elif col == "last_name":
                return c.last_name.lower()
            elif col == "first_name":
                return c.first_name.lower()
            elif col == "phone":
                return c.phone
            elif col == "rwp":
                return c.rwp_score
            elif col == "class":
                return c.rwp_classification
            elif col == "rationale":
                return c.rwp_rationale.lower()
            elif col == "updated":
                return c.updated_at
            elif col == "profile":
                return c.profile_status
            elif col == "background":
                return c.background_status
            elif col == "bg_id":
                return c.background_id
            elif col == "drug":
                return c.drug_test_status
            elif col == "drug_id":
                return c.drug_test_id
            elif col == "notes":
                return c.recruiter_notes.lower()
            elif col == "gcic":
                return c.gcic
            elif col == "mec":
                return c.mec
            elif col == "fedex_id":
                return c.fedex_id
            elif col == "status":
                return c.status
            elif col == "email":
                return c.email.lower()
            return ""
        
        self.filtered_candidates = sorted(
            self.filtered_candidates, 
            key=get_sort_key, 
            reverse=not self.sort_ascending
        )
    
    def sort_by(self, column: str):
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        self._apply_sort()
    
    def set_search(self, value: str):
        self.search_query = value
        self.apply_filters()
    
    def set_client_filter(self, value: str):
        self.client_filter = value
        self.apply_filters()
    
    def set_status_filter(self, value: str):
        self.status_filter = value
        self.apply_filters()
    
    def set_tag_filter(self, value: str):
        self.tag_filter = value
        self.apply_filters()
    
    def set_bg_filter(self, value: str):
        self.bg_filter = value
        self.apply_filters()
    
    def set_drug_filter(self, value: str):
        self.drug_filter = value
        self.apply_filters()
    
    def set_profile_filter(self, value: str):
        self.profile_filter = value
        self.apply_filters()
    
    def set_flag_filter(self, value: str):
        self.flag_filter = value
        self.apply_filters()
    
    def set_rwp_filter(self, value: str):
        self.rwp_filter = value
        self.apply_filters()
    
    def set_created_filter(self, value: str):
        self.created_filter = value
        self.apply_filters()
    
    # Multi-select methods (for candidate selection, not filters)
    def toggle_select(self, candidate_id: int):
        """Toggle selection of a candidate"""
        if candidate_id in self.selected_ids:
            self.selected_ids = [id for id in self.selected_ids if id != candidate_id]
        else:
            self.selected_ids = self.selected_ids + [candidate_id]
    
    def select_all(self, checked: bool):
        """Select or deselect all filtered candidates"""
        if checked:
            self.selected_ids = [c.id for c in self.filtered_candidates]
        else:
            self.selected_ids = []
    
    def clear_selection(self):
        """Clear all selections"""
        self.selected_ids = []
    
    # Batch action methods
    def toggle_batch_status(self):
        self.show_batch_status = not self.show_batch_status
        self.show_batch_note = False
        self.show_batch_tag = False
    
    def toggle_batch_note(self):
        self.show_batch_note = not self.show_batch_note
        self.show_batch_status = False
        self.show_batch_tag = False
    
    def toggle_batch_tag(self):
        self.show_batch_tag = not self.show_batch_tag
        self.show_batch_status = False
        self.show_batch_note = False
    
    def set_batch_status_value(self, value: str):
        self.batch_status_value = value
    
    def set_batch_note_value(self, value: str):
        self.batch_note_value = value
    
    def set_batch_tag_value(self, value: str):
        self.batch_tag_value = value
    
    def apply_batch_status(self):
        """Apply status change to all selected candidates"""
        if not self.selected_ids:
            return
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            with engine.connect() as conn:
                # Update all selected candidates
                for cid in self.selected_ids:
                    conn.execute(text("""
                        UPDATE candidates 
                        SET status = :status, updated_at = NOW()
                        WHERE id = :id
                    """), {"status": self.batch_status_value, "id": cid})
                conn.commit()
            
            # Update in-memory
            for i, c in enumerate(self.candidates):
                if c.id in self.selected_ids:
                    updated = Candidate(
                        **{**c.__dict__, "status": self.batch_status_value}
                    )
                    self.candidates[i] = updated
            
            self.success_message = f"Updated {len(self.selected_ids)} candidates to '{self.batch_status_value}'"
            self.selected_ids = []
            self.show_batch_status = False
            self.apply_filters()
            
        except Exception as e:
            self.error = f"Batch update failed: {str(e)}"
    
    def apply_batch_note(self):
        """Append note to all selected candidates"""
        if not self.selected_ids or not self.batch_note_value.strip():
            return
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            timestamp = datetime.now().strftime("%m/%d")
            note_with_date = f"[{timestamp}] {self.batch_note_value.strip()}"
            
            with engine.connect() as conn:
                for cid in self.selected_ids:
                    conn.execute(text("""
                        UPDATE candidates 
                        SET recruiter_notes = CASE 
                            WHEN recruiter_notes IS NULL OR recruiter_notes = '' THEN :note
                            ELSE recruiter_notes || ' | ' || :note
                        END,
                        updated_at = NOW()
                        WHERE id = :id
                    """), {"note": note_with_date, "id": cid})
                conn.commit()
            
            # Update in-memory
            for i, c in enumerate(self.candidates):
                if c.id in self.selected_ids:
                    new_notes = c.recruiter_notes + " | " + note_with_date if c.recruiter_notes else note_with_date
                    updated = Candidate(
                        **{**c.__dict__, "recruiter_notes": new_notes}
                    )
                    self.candidates[i] = updated
            
            self.success_message = f"Added note to {len(self.selected_ids)} candidates"
            self.selected_ids = []
            self.show_batch_note = False
            self.batch_note_value = ""
            self.apply_filters()
            
        except Exception as e:
            self.error = f"Batch note failed: {str(e)}"
    
    def apply_batch_tag(self):
        """Apply tag change to all selected candidates"""
        if not self.selected_ids:
            return
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            with engine.connect() as conn:
                for cid in self.selected_ids:
                    conn.execute(text("""
                        UPDATE candidates 
                        SET tag = :tag, updated_at = NOW()
                        WHERE id = :id
                    """), {"tag": self.batch_tag_value, "id": cid})
                conn.commit()
            
            # Update in-memory
            for i, c in enumerate(self.candidates):
                if c.id in self.selected_ids:
                    updated = Candidate(
                        **{**c.__dict__, "tag": self.batch_tag_value}
                    )
                    self.candidates[i] = updated
            
            self.success_message = f"Updated {len(self.selected_ids)} candidates to '{self.batch_tag_value}'"
            self.selected_ids = []
            self.show_batch_tag = False
            self.apply_filters()
            
        except Exception as e:
            self.error = f"Batch update failed: {str(e)}"
    
    @rx.var
    def selected_count(self) -> int:
        return len(self.selected_ids)
    
    @rx.var
    def can_merge(self) -> bool:
        """Can only merge when exactly 2 candidates selected"""
        return len(self.selected_ids) == 2
    
    @rx.var
    def selected_phones(self) -> str:
        """Get phone numbers of selected candidates, comma separated"""
        phones = []
        for c in self.candidates:
            if c.id in self.selected_ids and c.phone:
                phones.append(c.phone)
        return ", ".join(phones)
    
    def open_merge_modal(self):
        """Open merge modal with the two selected candidates"""
        if len(self.selected_ids) != 2:
            self.error = "Select exactly 2 candidates to merge"
            return
        
        id1, id2 = self.selected_ids[0], self.selected_ids[1]
        
        for c in self.candidates:
            if c.id == id1:
                self.merge_candidate_1 = {
                    "id": c.id,
                    "name": f"{c.first_name} {c.last_name}",
                    "client": c.client_display,
                    "client_id": c.client_id,
                    "created": c.created_at,
                    "phone": c.phone,
                    "email": c.email,
                    "rwp_score": c.rwp_score,
                    "rwp_classification": c.rwp_classification,
                    "rwp_rationale": c.rwp_rationale,
                    "background_status": c.background_status,
                    "background_id": c.background_id,
                    "drug_test_status": c.drug_test_status,
                    "drug_test_id": c.drug_test_id,
                    "profile_status": c.profile_status,
                    "status": c.status,
                    "notes": c.recruiter_notes,
                    "fedex_id": c.fedex_id,
                    "bg_override": c.bg_override,
                    "drug_override": c.drug_override,
                    "gcic": c.gcic,
                    "mec": c.mec,
                }
            elif c.id == id2:
                self.merge_candidate_2 = {
                    "id": c.id,
                    "name": f"{c.first_name} {c.last_name}",
                    "client": c.client_display,
                    "client_id": c.client_id,
                    "created": c.created_at,
                    "phone": c.phone,
                    "email": c.email,
                    "rwp_score": c.rwp_score,
                    "rwp_classification": c.rwp_classification,
                    "rwp_rationale": c.rwp_rationale,
                    "background_status": c.background_status,
                    "background_id": c.background_id,
                    "drug_test_status": c.drug_test_status,
                    "drug_test_id": c.drug_test_id,
                    "profile_status": c.profile_status,
                    "status": c.status,
                    "notes": c.recruiter_notes,
                    "fedex_id": c.fedex_id,
                    "bg_override": c.bg_override,
                    "drug_override": c.drug_override,
                    "gcic": c.gcic,
                    "mec": c.mec,
                }
        
        # Default primary to the one with more FADV data
        if self.merge_candidate_1.get("background_id") or self.merge_candidate_1.get("drug_test_id"):
            self.merge_primary = id1
        elif self.merge_candidate_2.get("background_id") or self.merge_candidate_2.get("drug_test_id"):
            self.merge_primary = id2
        else:
            # Default to newer record
            self.merge_primary = id1
        
        self.show_merge_modal = True
    
    def close_merge_modal(self):
        self.show_merge_modal = False
        self.merge_candidate_1 = {}
        self.merge_candidate_2 = {}
        self.merge_primary = 0
    
    def set_merge_primary(self, candidate_id: int):
        self.merge_primary = candidate_id
    
    def execute_merge(self):
        """Execute the merge - keep primary, pull data from secondary, archive secondary"""
        if not self.merge_primary:
            self.error = "Select which record to keep as primary"
            return
        
        primary_id = self.merge_primary
        secondary_id = self.merge_candidate_1["id"] if self.merge_candidate_2["id"] == primary_id else self.merge_candidate_2["id"]
        primary = self.merge_candidate_1 if self.merge_candidate_1["id"] == primary_id else self.merge_candidate_2
        secondary = self.merge_candidate_1 if self.merge_candidate_1["id"] == secondary_id else self.merge_candidate_2
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            with engine.connect() as conn:
                # Build update for primary - pull non-empty fields from secondary
                updates = []
                params = {"id": primary_id}
                
                # Pull RWP data if primary doesn't have it
                if not primary.get("rwp_score") and secondary.get("rwp_score"):
                    updates.append("rwp_score = :rwp_score")
                    updates.append("rwp_classification = :rwp_class")
                    updates.append("rwp_rationale = :rwp_rationale")
                    params["rwp_score"] = secondary["rwp_score"]
                    params["rwp_class"] = secondary["rwp_classification"]
                    params["rwp_rationale"] = secondary["rwp_rationale"]
                
                # Pull phone if primary doesn't have it
                if not primary.get("phone") and secondary.get("phone"):
                    updates.append("phone = :phone")
                    params["phone"] = secondary["phone"]
                
                # Pull email if primary doesn't have it
                if not primary.get("email") and secondary.get("email"):
                    updates.append("email = :email")
                    params["email"] = secondary["email"]
                
                # Pull FedEx ID if primary doesn't have it
                if not primary.get("fedex_id") and secondary.get("fedex_id"):
                    updates.append("fedex_id = :fedex_id")
                    params["fedex_id"] = secondary["fedex_id"]
                
                # Merge notes
                merged_notes = primary.get("notes", "") or ""
                if secondary.get("notes"):
                    if merged_notes:
                        merged_notes += f" | [Merged from {secondary['client']}] {secondary['notes']}"
                    else:
                        merged_notes = f"[Merged from {secondary['client']}] {secondary['notes']}"
                    updates.append("recruiter_notes = :notes")
                    params["notes"] = merged_notes
                
                # Pull FADV status fields if primary is missing them
                fadv_statuses = [
                    ("background_status", "bg_status", "background_status"),
                    ("drug_test_status",  "drug_status", "drug_test_status"),
                    ("profile_status",    "profile_status", "profile_status"),
                ]
                for src_key, param_key, db_col in fadv_statuses:
                    pval = primary.get(src_key, "") or ""
                    sval = secondary.get(src_key, "") or ""
                    if pval in ("Not Started", "") and sval not in ("Not Started", ""):
                        updates.append(f"{db_col} = :{param_key}")
                        params[param_key] = sval

                # Pull FADV IDs if primary is missing them
                if not primary.get("background_id") and secondary.get("background_id"):
                    updates.append("background_id = :bg_id")
                    params["bg_id"] = secondary["background_id"]

                if not primary.get("drug_test_id") and secondary.get("drug_test_id"):
                    updates.append("drug_test_id = :drug_id")
                    params["drug_id"] = secondary["drug_test_id"]

                # Pull override locks if secondary has them and primary doesn't
                if not primary.get("bg_override") and secondary.get("bg_override"):
                    updates.append("bg_override = :bg_override")
                    params["bg_override"] = secondary["bg_override"]

                if not primary.get("drug_override") and secondary.get("drug_override"):
                    updates.append("drug_override = :drug_override")
                    params["drug_override"] = secondary["drug_override"]

                # Pull form upload flags if primary is missing them
                if not primary.get("gcic") and secondary.get("gcic"):
                    updates.append("gcic_uploaded = :gcic")
                    params["gcic"] = secondary["gcic"]

                if not primary.get("mec") and secondary.get("mec"):
                    updates.append("mec_uploaded = :mec")
                    params["mec"] = secondary["mec"]

                # Always add merge tracking
                updates.append("updated_at = NOW()")
                
                if updates:
                    query = f"UPDATE candidates SET {', '.join(updates)} WHERE id = :id"
                    conn.execute(text(query), params)
                
                # Archive/delete secondary record (set status to 'Rejected')
                conn.execute(text("""
                    UPDATE candidates 
                    SET status = 'Transferred',
                        reject_reason = 'Merged - duplicate record',
                        recruiter_notes = COALESCE(recruiter_notes, '') || :merge_note,
                        updated_at = NOW()
                    WHERE id = :id
                """), {
                    "id": secondary_id,
                    "merge_note": f" | [MERGED into {primary['client']} record ID:{primary_id} on {datetime.now().strftime('%m/%d/%y')}]"
                })
                
                conn.commit()
            
            self.success_message = f"Merged records. Primary: {primary['name']} ({primary['client']}). Secondary archived."
            self.show_merge_modal = False
            self.selected_ids = []
            self.merge_candidate_1 = {}
            self.merge_candidate_2 = {}
            self.merge_primary = 0
            
            # Reload data to reflect changes
            self.load_data()
            
        except Exception as e:
            self.error = f"Merge failed: {str(e)}"
    
    # Pagination computed vars
    @rx.var
    def total_pages(self) -> int:
        total = len(self.filtered_candidates)
        if total == 0:
            return 1
        return (total + self.page_size - 1) // self.page_size
    
    @rx.var
    def paged_candidates(self) -> List[Candidate]:
        """Return only candidates for current page"""
        start = self.page * self.page_size
        end = start + self.page_size
        return self.filtered_candidates[start:end]
    
    @rx.var
    def page_display(self) -> str:
        return f"Page {self.page + 1} of {self.total_pages}"
    
    @rx.var 
    def can_prev(self) -> bool:
        return self.page > 0
    
    @rx.var
    def can_next(self) -> bool:
        return self.page < self.total_pages - 1
    
    def next_page(self):
        if self.page < self.total_pages - 1:
            self.page += 1
    
    def prev_page(self):
        if self.page > 0:
            self.page -= 1
    
    def first_page(self):
        self.page = 0
    
    def last_page(self):
        self.page = self.total_pages - 1
    
    # Edit modal methods
    def open_edit_modal(self, candidate_id: int):
        """Open edit modal for a candidate"""
        self.success_message = ""
        for c in self.candidates:
            if c.id == candidate_id:
                self.editing_id = c.id
                self.editing_name = f"{c.first_name} {c.last_name}"
                self.edit_notes = c.recruiter_notes
                self.edit_phone = c.phone
                self.edit_email = c.email
                self.edit_client = c.client_id
                self.edit_gcic = c.gcic == 1
                self.edit_mec = c.mec == 1
                self.edit_qcert = c.qcert == 1
                self.edit_rtest = c.rtest == 1
                self.edit_dl = c.dl == 1
                self.edit_bg_override = c.bg_override == 1
                self.edit_drug_override = c.drug_override == 1
                self.edit_fedex = c.fedex_id
                self.edit_status = c.status
                self.edit_reject_reason = getattr(c, "reject_reason", "") or ""
                self.edit_tag = c.tag
                self.editing_has_flag = c.flag == 1
                self.edit_clear_flag = False
                self.show_edit_modal = True
                break
    
    def close_edit_modal(self):
        """Close the edit modal"""
        self.show_edit_modal = False
        self.editing_id = 0
        self.edit_clear_flag = False
        self.confirm_delete = False
    
    def set_edit_notes(self, value: str):
        self.edit_notes = value
    
    def set_edit_phone(self, value: str):
        self.edit_phone = value
    
    def set_edit_email(self, value: str):
        self.edit_email = value
    
    def set_edit_client(self, value: str):
        self.edit_client = value
    
    def set_edit_gcic(self, value: bool):
        self.edit_gcic = value
    
    def set_edit_mec(self, value: bool):
        self.edit_mec = value
    
    def set_edit_qcert(self, value: bool):
        self.edit_qcert = value
    
    def set_edit_rtest(self, value: bool):
        self.edit_rtest = value
    
    def set_edit_dl(self, value: bool):
        self.edit_dl = value
    
    def set_edit_bg_override(self, value: bool):
        self.edit_bg_override = value
    
    def set_edit_drug_override(self, value: bool):
        self.edit_drug_override = value
    
    def set_edit_fedex(self, value: str):
        self.edit_fedex = value
    
    def set_edit_status(self, value: str):
        self.edit_status = value
    
    def set_edit_tag(self, value: str):
        self.edit_tag = value
    
    def set_edit_clear_flag(self, value: bool):
        self.edit_clear_flag = value
    
    def save_edits(self):
        """Save edits to database"""
        if not self.editing_id:
            return
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            gcic_val = 1 if self.edit_gcic else 0
            mec_val = 1 if self.edit_mec else 0
            qcert_val = 1 if self.edit_qcert else 0
            rtest_val = 1 if self.edit_rtest else 0
            dl_val = 1 if self.edit_dl else 0
            bg_override_val = 1 if self.edit_bg_override else 0
            drug_override_val = 1 if self.edit_drug_override else 0
            
            # Build query based on whether to clear flag
            # Use NULL for empty email to avoid unique constraint issues
            email_val = self.edit_email.strip() if self.edit_email.strip() else None
            
            if self.edit_clear_flag:
                query = text("""
                    UPDATE candidates 
                    SET recruiter_notes = :notes,
                        phone = :phone,
                        email = :email,
                        client_id = :client_id,
                        gcic_uploaded = :gcic,
                        mec_uploaded = :mec,
                        qcert_uploaded = :qcert,
                        rtest_completed = :rtest,
                        dl_verified = :dl,
                        bg_override = :bg_override,
                        drug_override = :drug_override,
                        fedex_id = :fedex,
                        status = :status,
                        tag = :tag,
                        reject_reason = :reject_reason,
                        fadv_change_flag = 0,
                        fadv_change_details = '',
                        updated_at = NOW()
                    WHERE id = :id
                """)
            else:
                query = text("""
                    UPDATE candidates 
                    SET recruiter_notes = :notes,
                        phone = :phone,
                        email = :email,
                        client_id = :client_id,
                        gcic_uploaded = :gcic,
                        mec_uploaded = :mec,
                        qcert_uploaded = :qcert,
                        rtest_completed = :rtest,
                        dl_verified = :dl,
                        bg_override = :bg_override,
                        drug_override = :drug_override,
                        fedex_id = :fedex,
                        status = :status,
                        tag = :tag,
                        updated_at = NOW()
                        reject_reason = :reject_reason,
                    WHERE id = :id
                """)
            
            with engine.connect() as conn:
                conn.execute(query, {
                    "notes": self.edit_notes,
                    "phone": self.edit_phone,
                    "email": email_val,
                    "client_id": self.edit_client,
                    "gcic": gcic_val,
                    "mec": mec_val,
                    "qcert": qcert_val,
                    "rtest": rtest_val,
                    "dl": dl_val,
                    "bg_override": bg_override_val,
                    "drug_override": drug_override_val,
                    "fedex": self.edit_fedex,
                    "status": self.edit_status,
                    "tag": self.edit_tag,
                    "reject_reason": self.edit_reject_reason if self.edit_status in ("Rejected", "Transferred") else None,
                    "id": self.editing_id,
                })
                conn.commit()
            
            # Update in-memory instead of full reload (preserves filters/sort)
            for i, c in enumerate(self.candidates):
                if c.id == self.editing_id:
                    updated = Candidate(
                        id=c.id,
                        first_name=c.first_name,
                        last_name=c.last_name,
                        client_id=self.edit_client,
                        client_display=format_client(self.edit_client),
                        email=self.edit_email,
                        phone=self.edit_phone,
                        fedex_id=self.edit_fedex,
                        rwp_score=c.rwp_score,
                        rwp_classification=c.rwp_classification,
                        rwp_rationale=c.rwp_rationale,
                        background_status=c.background_status,
                        background_status_raw=c.background_status_raw,
                        background_id=c.background_id,
                        bg_override=bg_override_val,
                        drug_test_status=c.drug_test_status,
                        drug_test_status_raw=c.drug_test_status_raw,
                        drug_test_id=c.drug_test_id,
                        drug_override=drug_override_val,
                        profile_status=c.profile_status,
                        status=self.edit_status,
                        tag=self.edit_tag,
                        recruiter_notes=self.edit_notes,
                        gcic=gcic_val,
                        mec=mec_val,
                        qcert=qcert_val,
                        rtest=rtest_val,
                        dl=dl_val,
                        flag=0 if self.edit_clear_flag else c.flag,
                        flag_details="" if self.edit_clear_flag else c.flag_details,
                        flag_type="" if self.edit_clear_flag else c.flag_type,
                        created_at=c.created_at,
                        updated_at=c.updated_at,
                    )
                    self.candidates[i] = updated
                    break
            
            # Update filtered_candidates too
            for i, c in enumerate(self.filtered_candidates):
                if c.id == self.editing_id:
                    self.filtered_candidates[i] = updated
                    break
            
            msg = f"Saved changes for {self.editing_name}"
            if self.edit_clear_flag:
                msg += " (flag cleared)"
            self.success_message = msg
            self.show_edit_modal = False
            self.edit_clear_flag = False
            
        except Exception as e:
            self.error = f"Save failed: {str(e)}"
    
    def delete_candidate(self):
        """Permanently delete the current candidate record"""
        if not self.editing_id:
            return
        
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(DB_URL)
            
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM candidates WHERE id = :id"), {"id": self.editing_id})
                conn.commit()
            
            # Remove from in-memory lists
            self.candidates = [c for c in self.candidates if c.id != self.editing_id]
            self.filtered_candidates = [c for c in self.filtered_candidates if c.id != self.editing_id]
            
            self.success_message = f"Deleted {self.editing_name}"
            self.show_edit_modal = False
            self.editing_id = 0
            
        except Exception as e:
            self.error = f"Delete failed: {str(e)}"
    
    @rx.var
    def csv_data(self) -> str:
        """Generate properly formatted CSV string for clipboard
        If records are selected, export only those. Otherwise export all filtered."""
        lines = []
        # Header - tab separated for proper Excel paste
        lines.append("Client\tFlag\tCreated\tLast\tFirst\tPhone\tRWP\tClass\tRationale\tUpdated\tProfile\tBG Status\tBG ID\tDrug Status\tDrug ID\tNotes\tGCIC\tMEC\tFedEx\tStatus\tEmail")
        
        # Use selected candidates if any are selected, otherwise use all filtered
        candidates_to_export = [c for c in self.filtered_candidates if c.id in self.selected_ids] if self.selected_ids else self.filtered_candidates
        
        # Data rows - tab separated
        for c in candidates_to_export:
            notes_clean = c.recruiter_notes.replace('\t', ' ').replace('\n', ' ')
            rationale_clean = c.rwp_rationale.replace('\t', ' ').replace('\n', ' ')
            row = [
                c.client_display,
                "Yes" if c.flag == 1 else "",
                c.created_at,
                c.last_name,
                c.first_name,
                c.phone,
                str(c.rwp_score),
                c.rwp_classification,
                rationale_clean,
                c.updated_at,
                c.profile_status,
                c.background_status,
                c.background_id,
                c.drug_test_status,
                c.drug_test_id,
                notes_clean,
                str(c.gcic),
                str(c.mec),
                c.fedex_id,
                c.status,
                c.email,
            ]
            lines.append("\t".join(row))
        return "\n".join(lines)


def sortable_header(label: str, column: str) -> rx.Component:
    return rx.table.column_header_cell(
        rx.hstack(
            rx.text(label, weight="bold", size="1"),
            rx.cond(
                State.sort_column == column,
                rx.cond(
                    State.sort_ascending,
                    rx.text("▲", size="1", color="blue"),
                    rx.text("▼", size="1", color="blue"),
                ),
                rx.text("◇", size="1", color="gray"),
            ),
            spacing="1",
            cursor="pointer",
            align="center",
        ),
        on_click=lambda: State.sort_by(column),
        white_space="nowrap",
    )


def check_badge(value: int) -> rx.Component:
    return rx.cond(
        value == 1,
        rx.badge("✓", color_scheme="green", size="1"),
        rx.badge("—", color_scheme="gray", size="1"),
    )


def status_badge(status: str) -> rx.Component:
    return rx.match(
        status,
        ("Hired", rx.badge(status, color_scheme="green", size="1")),
        ("Rejected", rx.badge(status, color_scheme="red", size="1")),
        ("Transferred", rx.badge(status, color_scheme="red", size="1")),
        ("On Deck", rx.badge(status, color_scheme="blue", size="1")),
        ("Followup", rx.badge(status, color_scheme="yellow", size="1")),
        rx.badge(status, color_scheme="gray", size="1"),
    )


def tag_badge(tag: str) -> rx.Component:
    return rx.match(
        tag,
        ("Manager", rx.badge(tag, color_scheme="purple", size="1")),
        rx.badge(tag, color_scheme="gray", size="1"),
    )


# Column order: Select, Client, Flag, Created, Last, First, Phone, RWP, Class, Rationale, Updated, Profile, BG, BG ID, BG OvrR, Drug, Drug ID, Drug OvrR, Edit, [EDITABLE], Email
def candidate_row(candidate: Candidate) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.checkbox(
                checked=State.selected_ids.contains(candidate.id),
                on_change=lambda _: State.toggle_select(candidate.id),
            ),
            white_space="nowrap",
        ),
        rx.table.cell(rx.text(candidate.client_display, size="1"), white_space="nowrap"),
        rx.table.cell(
            rx.cond(
                candidate.flag == 1,
                rx.tooltip(
                    rx.text("🚩", size="2"),
                    content=rx.cond(candidate.flag_details != "", candidate.flag_details, "Status changed"),
                ),
                rx.text("", size="1"),
            ),
            white_space="nowrap",
        ),
        rx.table.cell(rx.text(candidate.created_at, size="1", color="gray"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.last_name, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.first_name, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.phone, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.rwp_score, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.rwp_classification, size="1"), white_space="nowrap"),
        rx.table.cell(
            rx.tooltip(
                rx.text("📋", size="1", cursor="pointer"),
                content=rx.cond(candidate.rwp_rationale != "", candidate.rwp_rationale, "No rationale"),
            ),
            white_space="nowrap",
        ),
        rx.table.cell(rx.text(candidate.updated_at, size="1", color="gray"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.profile_status, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.background_status, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.background_id, size="1"), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.bg_override), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.drug_test_status, size="1"), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.drug_test_id, size="1"), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.drug_override), white_space="nowrap"),
        # Edit button
        rx.table.cell(
            rx.button(
                "✏️",
                size="1",
                variant="ghost",
                on_click=lambda: State.open_edit_modal(candidate.id),
            ),
            white_space="nowrap",
        ),
        # EDITABLE COLUMNS GROUP START
        rx.table.cell(
            rx.tooltip(
                rx.text("📝", size="1", cursor="pointer"),
                content=rx.cond(candidate.recruiter_notes != "", candidate.recruiter_notes, "No notes"),
            ),
            white_space="nowrap",
        ),
        rx.table.cell(check_badge(candidate.gcic), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.mec), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.qcert), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.rtest), white_space="nowrap"),
        rx.table.cell(check_badge(candidate.dl), white_space="nowrap"),
        rx.table.cell(rx.text(candidate.fedex_id, size="1"), white_space="nowrap"),
        rx.table.cell(status_badge(candidate.status), white_space="nowrap"),
        rx.table.cell(tag_badge(candidate.tag), white_space="nowrap"),
        # EDITABLE COLUMNS GROUP END
        rx.table.cell(rx.text(candidate.email, size="1"), white_space="nowrap"),
        bg=rx.cond(
            candidate.status == "Hired", "var(--green-3)",
            rx.cond(candidate.status == "Rejected", "var(--red-2)",
            rx.cond(candidate.status == "Transferred", "var(--red-2)",
            rx.cond(candidate.status == "Intake", "var(--gray-2)",
            rx.cond(candidate.status == "Followup", "var(--yellow-2)",
            rx.cond(candidate.status == "On Deck", "var(--blue-2)",
            "white"
        ))))))
    )

            ),

        },

    )



def filter_with_label(label: str, options, value, on_change) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="1", weight="medium", color="gray"),
        rx.select(
            options,
            value=value,
            on_change=on_change,
            size="2",
        ),
        spacing="1",
        align="start",
    )


def stat_card(label: str, value, color: str = "blue") -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.text(label, size="2", color="gray"),
            rx.text(value, size="3", weight="bold", color=color),
            spacing="2",
        ),
        padding="2",
    )


def edit_modal() -> rx.Component:
    """Edit modal for editable fields"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(f"Edit: {State.editing_name}"),
            rx.vstack(
                # Phone and Email row
                rx.hstack(
                    rx.vstack(
                        rx.text("Phone", size="2", weight="medium"),
                        rx.input(
                            value=State.edit_phone,
                            on_change=State.set_edit_phone,
                            placeholder="Phone number...",
                            width="100%",
                        ),
                        width="50%",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Email", size="2", weight="medium"),
                        rx.input(
                            value=State.edit_email,
                            on_change=State.set_edit_email,
                            placeholder="Email address...",
                            width="100%",
                        ),
                        width="50%",
                        align="start",
                    ),
                    width="100%",
                    spacing="4",
                ),
                
                # Notes
                rx.vstack(
                    rx.text("Recruiter Notes", size="2", weight="medium"),
                    rx.text_area(
                        value=State.edit_notes,
                        on_change=State.set_edit_notes,
                        placeholder="Enter notes...",
                        width="100%",
                        rows="4",
                    ),
                    width="100%",
                    align="start",
                ),
                
                # Checkboxes row
                rx.hstack(
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_gcic,
                            on_change=State.set_edit_gcic,
                        ),
                        rx.text("GCIC", size="2"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_mec,
                            on_change=State.set_edit_mec,
                        ),
                        rx.text("MEC", size="2"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_qcert,
                            on_change=State.set_edit_qcert,
                        ),
                        rx.text("QCert", size="2"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_rtest,
                            on_change=State.set_edit_rtest,
                        ),
                        rx.text("RTest", size="2"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_dl,
                            on_change=State.set_edit_dl,
                        ),
                        rx.text("DL", size="2"),
                        spacing="2",
                    ),
                    spacing="6",
                ),
                
                # Override checkboxes row
                rx.hstack(
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_bg_override,
                            on_change=State.set_edit_bg_override,
                        ),
                        rx.text("BG Override", size="2", color="orange"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_drug_override,
                            on_change=State.set_edit_drug_override,
                        ),
                        rx.text("Drug Override", size="2", color="orange"),
                        spacing="2",
                    ),
                    spacing="6",
                ),
                
                # FedEx ID
                rx.vstack(
                    rx.text("FedEx#", size="2", weight="medium"),
                    rx.input(
                        value=State.edit_fedex,
                        on_change=State.set_edit_fedex,
                        placeholder="Enter FedEx#...",
                        width="100%",
                    ),
                    width="100%",
                    align="start",
                ),
                
                # Status
                rx.vstack(
                    rx.text("Status", size="2", weight="medium"),
                    rx.select(
                        ["Intake", "Unranked", "Active", "On Deck", "Followup", "Hired", "Transferred", "Rejected"],
                        value=State.edit_status,
                        on_change=State.set_edit_status,
                        width="100%",
                    ),
                    width="100%",
                    align="start",
                ),
                
                # Reject reason (conditional on status)
                rx.cond(
                    (State.edit_status == "Rejected") | (State.edit_status == "Transferred"),
                    rx.vstack(
                        rx.text("Reject / Transfer Reason", size="2", weight="medium"),
                        rx.input(
                            value=State.edit_reject_reason,
                            on_change=State.set_edit_reject_reason,
                            placeholder="e.g. No-show, Failed BG, Transferred to CBM...",
                            width="100%",
                        ),
                        width="100%",
                        align="start",
                    ),
                ),

                # Tag
                rx.vstack(
                    rx.text("Tag", size="2", weight="medium"),
                    rx.select(
                        ["Driver", "Manager"],
                        value=State.edit_tag,
                        on_change=State.set_edit_tag,
                        width="100%",
                    ),
                    width="100%",
                    align="start",
                ),
                
                # Clear flag (only show if flagged)
                rx.cond(
                    State.editing_has_flag,
                    rx.hstack(
                        rx.checkbox(
                            checked=State.edit_clear_flag,
                            on_change=State.set_edit_clear_flag,
                        ),
                        rx.text("🚩 Clear flag (mark as reviewed)", size="2", color="orange"),
                        spacing="2",
                    ),
                ),
                
                # Delete section
                rx.box(
                    rx.cond(
                        State.confirm_delete,
                        rx.hstack(
                            rx.text("⚠️ Permanently delete?", size="2", color="red"),
                            rx.button(
                                "Yes, Delete",
                                color_scheme="red",
                                size="1",
                                on_click=State.delete_candidate,
                            ),
                            rx.button(
                                "Cancel",
                                variant="outline",
                                size="1",
                                on_click=State.toggle_confirm_delete,
                            ),
                            spacing="2",
                        ),
                        rx.button(
                            "🗑️ Delete Record",
                            variant="ghost",
                            color_scheme="red",
                            size="1",
                            on_click=State.toggle_confirm_delete,
                        ),
                    ),
                    padding_top="2",
                ),
                
                # Buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        on_click=State.close_edit_modal,
                    ),
                    rx.button(
                        "Save",
                        on_click=State.save_edits,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                
                spacing="4",
                width="100%",
            ),
            padding="4",
        ),
        open=State.show_edit_modal,
    )


def merge_modal() -> rx.Component:
    """Modal for merging two candidate records"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("🔀 Merge Candidates"),
            rx.dialog.description(
                "Click a card to select it as PRIMARY (the record to keep). Data from the other record will be merged in.",
                size="2",
            ),
            rx.vstack(
                # Side by side comparison
                rx.hstack(
                    # Candidate 1 - clickable card
                    rx.box(
                        rx.vstack(
                            rx.cond(
                                State.merge_primary == State.merge_candidate_1["id"],
                                rx.badge("✓ KEEP THIS", color_scheme="green", size="2"),
                                rx.badge("Click to select", color_scheme="gray", size="1"),
                            ),
                            rx.text(State.merge_candidate_1["name"], weight="bold", size="3"),
                            rx.text(State.merge_candidate_1["client"], size="2", color="blue"),
                            rx.text(State.merge_candidate_1["created"], size="1", color="gray"),
                            rx.divider(),
                            rx.hstack(
                                rx.text("Phone:", size="1", color="gray"),
                                rx.text(State.merge_candidate_1["phone"], size="1"),
                            ),
                            rx.hstack(
                                rx.text("RWP:", size="1", color="gray"),
                                rx.text(State.merge_candidate_1["rwp_score"], size="1", weight="bold"),
                            ),
                            rx.hstack(
                                rx.text("BG ID:", size="1", color="gray"),
                                rx.text(State.merge_candidate_1["background_id"], size="1"),
                            ),
                            rx.hstack(
                                rx.text("Drug ID:", size="1", color="gray"),
                                rx.text(State.merge_candidate_1["drug_test_id"], size="1"),
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        padding="3",
                        border="3px solid",
                        border_color=rx.cond(
                            State.merge_primary == State.merge_candidate_1["id"],
                            "green",
                            "#ddd"
                        ),
                        border_radius="md",
                        width="220px",
                        cursor="pointer",
                        _hover={"border_color": "blue"},
                        on_click=lambda: State.set_merge_primary(State.merge_candidate_1["id"]),
                    ),
                    
                    rx.text("→", size="5", color="gray"),
                    
                    # Candidate 2 - clickable card
                    rx.box(
                        rx.vstack(
                            rx.cond(
                                State.merge_primary == State.merge_candidate_2["id"],
                                rx.badge("✓ KEEP THIS", color_scheme="green", size="2"),
                                rx.badge("Click to select", color_scheme="gray", size="1"),
                            ),
                            rx.text(State.merge_candidate_2["name"], weight="bold", size="3"),
                            rx.text(State.merge_candidate_2["client"], size="2", color="blue"),
                            rx.text(State.merge_candidate_2["created"], size="1", color="gray"),
                            rx.divider(),
                            rx.hstack(
                                rx.text("Phone:", size="1", color="gray"),
                                rx.text(State.merge_candidate_2["phone"], size="1"),
                            ),
                            rx.hstack(
                                rx.text("RWP:", size="1", color="gray"),
                                rx.text(State.merge_candidate_2["rwp_score"], size="1", weight="bold"),
                            ),
                            rx.hstack(
                                rx.text("BG ID:", size="1", color="gray"),
                                rx.text(State.merge_candidate_2["background_id"], size="1"),
                            ),
                            rx.hstack(
                                rx.text("Drug ID:", size="1", color="gray"),
                                rx.text(State.merge_candidate_2["drug_test_id"], size="1"),
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        padding="3",
                        border="3px solid",
                        border_color=rx.cond(
                            State.merge_primary == State.merge_candidate_2["id"],
                            "green",
                            "#ddd"
                        ),
                        border_radius="md",
                        width="220px",
                        cursor="pointer",
                        _hover={"border_color": "blue"},
                        on_click=lambda: State.set_merge_primary(State.merge_candidate_2["id"]),
                    ),
                    spacing="3",
                    align="center",
                ),
                
                rx.callout(
                    "The selected card will be kept. Missing data (RWP, phone, email) will be pulled from the other record. The other record will be archived.",
                    icon="info",
                    size="1",
                ),
                
                # Action buttons
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        on_click=State.close_merge_modal,
                    ),
                    rx.button(
                        "🔀 Execute Merge",
                        color_scheme="purple",
                        on_click=State.execute_merge,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            max_width="550px",
        ),
        open=State.show_merge_modal,
    )


def login_page() -> rx.Component:
    """Login screen"""
    return rx.center(
        rx.vstack(
            rx.heading("🔐 PEAKATS Dashboard", size="6"),
            rx.text("Enter password to access", color="gray"),
            rx.input(
                placeholder="Password",
                type="password",
                value=State.password_input,
                on_change=State.set_password_input,
                width="300px",
            ),
            rx.button(
                "Login",
                on_click=State.check_password,
                width="300px",
            ),
            rx.cond(
                State.auth_error != "",
                rx.text(State.auth_error, color="red", size="2"),
            ),
            spacing="4",
            padding="8",
            border="1px solid #ccc",
            border_radius="8px",
            background="white",
        ),
        height="100vh",
        background="#f5f5f5",
    )


def dashboard() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("📊 PEAKATS Dashboard", size="6"),
                rx.spacer(),
                rx.cond(
                    State.selected_ids.length() > 0,
                    rx.button(
                        rx.text(f"📋 Copy Selected (", State.selected_ids.length(), ")"),
                        on_click=rx.set_clipboard(State.csv_data),
                        variant="solid",
                        color_scheme="green",
                        size="2",
                    ),
                    rx.button(
                        "📋 Copy All CSV",
                        on_click=rx.set_clipboard(State.csv_data),
                        variant="outline",
                        size="2",
                    ),
                ),
                rx.button(
                    "🔄 Refresh",
                    on_click=State.load_data,
                    loading=State.loading,
                    size="2",
                ),
                width="100%",
                padding="3",
                align="center",
            ),
            
            # Success message
            rx.cond(
                State.success_message != "",
                rx.callout(State.success_message, color_scheme="green", size="1"),
            ),
            
            # Stats row
            rx.hstack(
                stat_card("Total:", State.candidates.length(), "blue"),
                stat_card("Showing:", State.filtered_candidates.length(), "blue"),
                stat_card("BG Eligible:", State.bg_eligible_count, "green"),
                stat_card("Drug Eligible:", State.drug_eligible_count, "green"),
                spacing="3",
                padding_x="3",
                wrap="wrap",
            ),
            
            # Filters with labels - ordered to match columns
            rx.hstack(
                rx.vstack(
                    rx.text("Search", size="1", weight="medium", color="gray"),
                    rx.input(
                        placeholder="🔍 Name, email, phone...",
                        value=State.search_query,
                        on_change=State.set_search,
                        width="200px",
                        size="2",
                    ),
                    spacing="1",
                    align="start",
                ),
                filter_with_label("Client", State.client_options, State.client_filter, State.set_client_filter),
                filter_with_label("🚩 Flag", State.flag_options, State.flag_filter, State.set_flag_filter),
                filter_with_label("RWP", State.rwp_options, State.rwp_filter, State.set_rwp_filter),
                filter_with_label("Created", State.created_options, State.created_filter, State.set_created_filter),
                filter_with_label("Profile", State.profile_options, State.profile_filter, State.set_profile_filter),
                filter_with_label("Background", State.bg_options, State.bg_filter, State.set_bg_filter),
                filter_with_label("Drug Test", State.drug_options, State.drug_filter, State.set_drug_filter),
                filter_with_label("Status", State.status_options, State.status_filter, State.set_status_filter),
                filter_with_label("Tag", State.tag_options, State.tag_filter, State.set_tag_filter),
                # Selection actions inline with filters
                rx.cond(
                    State.selected_count > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.text(State.selected_count, size="2", weight="bold"),
                            rx.text("selected", size="2"),
                            rx.button(
                                "📞 Copy Phones",
                                size="1",
                                variant="outline",
                                on_click=rx.set_clipboard(State.selected_phones),
                            ),
                            rx.button(
                                "📝 Status",
                                size="1",
                                variant="soft",
                                color_scheme="blue",
                                on_click=State.toggle_batch_status,
                            ),
                            rx.button(
                                "📋 Note",
                                size="1",
                                variant="soft",
                                color_scheme="green",
                                on_click=State.toggle_batch_note,
                            ),
                            rx.button(
                                "🏷️ Tag",
                                size="1",
                                variant="soft",
                                color_scheme="orange",
                                on_click=State.toggle_batch_tag,
                            ),
                            rx.button(
                                "🔀 Merge (2)",
                                size="1",
                                variant="soft",
                                color_scheme="purple",
                                on_click=State.open_merge_modal,
                                disabled=State.selected_count != 2,
                            ),
                            rx.button(
                                "✕",
                                size="1",
                                variant="ghost",
                                on_click=State.clear_selection,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        # Batch Status dropdown
                        rx.cond(
                            State.show_batch_status,
                            rx.hstack(
                                rx.select(
                                    ["Intake", "Unranked", "Active", "On Deck", "Followup", "Hired", "Transferred", "Rejected"],
                                    value=State.batch_status_value,
                                    on_change=State.set_batch_status_value,
                                    size="1",
                                ),
                                rx.button(
                                    "Apply",
                                    size="1",
                                    color_scheme="blue",
                                    on_click=State.apply_batch_status,
                                ),
                                spacing="2",
                            ),
                        ),
                        # Batch Note input
                        rx.cond(
                            State.show_batch_note,
                            rx.hstack(
                                rx.input(
                                    value=State.batch_note_value,
                                    on_change=State.set_batch_note_value,
                                    placeholder="Note to add...",
                                    size="1",
                                    width="200px",
                                ),
                                rx.button(
                                    "Add",
                                    size="1",
                                    color_scheme="green",
                                    on_click=State.apply_batch_note,
                                ),
                                spacing="2",
                            ),
                        ),
                        # Batch Tag dropdown
                        rx.cond(
                            State.show_batch_tag,
                            rx.hstack(
                                rx.select(
                                    ["Driver", "Manager"],
                                    value=State.batch_tag_value,
                                    on_change=State.set_batch_tag_value,
                                    size="1",
                                ),
                                rx.button(
                                    "Apply",
                                    size="1",
                                    color_scheme="orange",
                                    on_click=State.apply_batch_tag,
                                ),
                                spacing="2",
                            ),
                        ),
                        padding="2",
                        background="var(--blue-3)",
                        border_radius="md",
                        spacing="2",
                    ),
                ),
                spacing="4",
                padding="3",
                wrap="wrap",
                align="end",
            ),
            
            # Error display
            rx.cond(
                State.error != "",
                rx.callout(State.error, color_scheme="red"),
            ),
            
            # Table with sticky header
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                rx.checkbox(
                                    on_change=State.select_all,
                                ),
                            ),
                            sortable_header("Client", "client"),
                            sortable_header("🚩", "flag"),
                            sortable_header("Created", "created"),
                            sortable_header("Last", "last_name"),
                            sortable_header("First", "first_name"),
                            sortable_header("Phone", "phone"),
                            sortable_header("RWP", "rwp"),
                            sortable_header("Class", "class"),
                            sortable_header("Rationale", "rationale"),
                            sortable_header("Updated", "updated"),
                            sortable_header("Profile", "profile"),
                            sortable_header("BG", "background"),
                            sortable_header("BG ID", "bg_id"),
                            sortable_header("BG OvrR", "bg_override"),
                            sortable_header("Drug", "drug"),
                            sortable_header("Drug ID", "drug_id"),
                            sortable_header("Drug OvrR", "drug_override"),
                            rx.table.column_header_cell(rx.text("Edit", weight="bold", size="1")),
                            sortable_header("Notes", "notes"),
                            sortable_header("GCIC", "gcic"),
                            sortable_header("MEC", "mec"),
                            sortable_header("QCert", "qcert"),
                            sortable_header("RTest", "rtest"),
                            sortable_header("DL", "dl"),
                            sortable_header("FedEx#", "fedex_id"),
                            sortable_header("Status", "status"),
                            sortable_header("Tag", "tag"),
                            sortable_header("Email", "email"),
                            background="var(--gray-2)",
                            style={"position": "sticky", "top": "0", "z_index": "10"},
                        ),
                        style={"position": "sticky", "top": "0", "z_index": "10", "background": "var(--gray-1)"},
                    ),
                    rx.table.body(
                        rx.foreach(State.paged_candidates, candidate_row),
                    ),
                    width="100%",
                    size="1",
                ),
                overflow_x="auto",
                overflow_y="auto",
                max_height="calc(100vh - 280px)",
                padding="3",
            ),
            
            # Pagination controls
            rx.hstack(
                rx.button(
                    "« First",
                    size="1",
                    variant="outline",
                    on_click=State.first_page,
                    disabled=~State.can_prev,
                ),
                rx.button(
                    "‹ Prev",
                    size="1",
                    variant="outline",
                    on_click=State.prev_page,
                    disabled=~State.can_prev,
                ),
                rx.text(State.page_display, size="2", weight="medium"),
                rx.button(
                    "Next ›",
                    size="1",
                    variant="outline",
                    on_click=State.next_page,
                    disabled=~State.can_next,
                ),
                rx.button(
                    "Last »",
                    size="1",
                    variant="outline",
                    on_click=State.last_page,
                    disabled=~State.can_next,
                ),
                spacing="2",
                padding="3",
                justify="center",
                width="100%",
            ),
            
            spacing="2",
            width="100%",
        ),
        edit_modal(),
        merge_modal(),
        min_height="100vh",
        background="var(--gray-1)",
    )


def index() -> rx.Component:
    """Main entry point - shows login or dashboard"""
    return rx.cond(
        State.authenticated,
        dashboard(),
        login_page(),
    )


app = rx.App(
    theme=rx.theme(
        accent_color="blue",
        gray_color="slate",
        radius="medium",
    ),
)
app.add_page(index, title="PEAKATS Dashboard")
