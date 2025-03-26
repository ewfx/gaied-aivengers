import streamlit as st
import time
from extractor import extract_text_from_file
from gmail_service import (
    get_gmail_service, get_email_details, fetch_all_emails, save_email_attachments
)
from crew import process_email_with_crew
from storage import (
    save_last_processed_id, get_last_processed_id,
    save_processed_emails, load_processed_emails
)
from ui_styles import get_css_styles
from config import MAX_EMAILS_TO_FETCH
import os
from datetime import datetime
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

email_store=[]
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")  # Lightweight embedding model
dimension = 384  # Model embedding size
index = faiss.IndexFlatL2(dimension)  # FAISS index

# Page configuration
st.set_page_config(layout="wide", page_title="Loan Servicing Email Processor")

# Ensure the attachments directory exists
ATTACHMENTS_DIR = "../../venv/attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# Initialize session state
if "processed_emails" not in st.session_state:
    try:
        st.session_state["processed_emails"] = load_processed_emails()
    except:
        st.session_state["processed_emails"] = set()

if "email_data" not in st.session_state:
    st.session_state["email_data"] = []

if "last_processed_time" not in st.session_state:
    st.session_state["last_processed_time"] = None

if "auto_refresh" not in st.session_state:
    st.session_state["auto_refresh"] = False

# Initialize Gmail service
gmail_service = get_gmail_service()
if not gmail_service:
    st.error("❌ Gmail API authentication failed. Please check your credentials.")
    st.stop()


def fetch_and_process_emails():
    """Fetch and process all emails, regardless of attachments."""
    with st.spinner("📥 Fetching emails..."):
        # Get all emails from inbox
        email_ids = fetch_all_emails(gmail_service, max_results=MAX_EMAILS_TO_FETCH)

        if not email_ids:
            st.info("No emails found in inbox.")
            return

        total_emails = len(email_ids)
        processed_count = 0
        progress_bar = st.progress(0)
        status_text = st.empty()

        for email_id in email_ids:
            if email_id in st.session_state["processed_emails"]:
                continue

            # Update progress
            processed_count += 1
            progress_bar.progress(processed_count / total_emails)
            status_text.text(f"Processing email {processed_count} of {total_emails}")

            email_data = get_email_details(gmail_service, email_id)
            if not email_data:
                continue

            # Save attachments if they exist
            attachment_paths = save_email_attachments(gmail_service, email_id, ATTACHMENTS_DIR)
            email_data["attachments"] = [{"path": path} for path in attachment_paths]

            # Process with CrewAI
            result = process_email_with_crew(
                email_data,
                index,
                email_store,
                [e["email"] for e in st.session_state["email_data"][-10:]],

            )

            st.session_state["processed_emails"].add(email_id)
            st.session_state["email_data"].insert(0, {"email": email_data, "result": result})
            st.session_state["last_processed_time"] = datetime.now()

            save_last_processed_id(email_id)
            save_processed_emails(st.session_state["processed_emails"])

        progress_bar.empty()
        status_text.empty()
        st.success(f"✅ Processed {processed_count} emails")


# UI Header
st.markdown("<h1 style='text-align: center; color: red;'>📩 Email Notifications</h1>", unsafe_allow_html=True)

# CSS Styles
st.markdown(get_css_styles(), unsafe_allow_html=True)

# Control Panel
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("Fetch & Process All Emails"):
        fetch_and_process_emails()
with col2:
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=st.session_state["auto_refresh"])
    st.session_state["auto_refresh"] = auto_refresh
with col3:
    refresh_interval = st.slider("Refresh Interval (seconds)", 10, 300, 60)

st.divider()

# Email Display Section
if st.session_state["email_data"]:
    # Table Header
    st.markdown(
        """
        <style>
            .email-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background-color: #ffe5e5;
                padding: 5px; /* Reduce padding */
                margin: 0px; /* Remove extra margin */
                gap: 5px; /* Reduce spacing between elements */
                border-radius: 5px;
            }
            .email-row div {
                flex: 1;
                color: red;
                text-align: left;
                font-weight: bold;
            }
            .email-row div:nth-child(1) { flex: 2; } /* Email Subject should take more space */
            .email-row div:last-child { text-align: center; } /* Center align Actions column */
        </style>

        <div class="email-row">
            <div>Subject</div>
            <div>Request Type</div>
            <div>Sub Request Type</div>
            <div>Duplicate Flag</div>
            <div>Confidence</div>
            <div>Actions</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Display emails in rows
    # Initialize session state for toggling email body
    if "show_email_body" not in st.session_state:
        st.session_state["show_email_body"] = {}

# Initialize session state for edit mode if not exists
if "edit_mode" not in st.session_state:
    st.session_state["edit_mode"] = {}


# Define your request types and subtypes at the top of your script (outside the loop)
REQUEST_TYPES = ["Adjustment", "AU Transfer", "Closing Notice", "Commitment Change", "Fee Payment",
                 "Money Movement Inbound", "Money Movement Outbound"]
SUB_TYPES = ["Reallocation Fees", "Amendment Fees", "Reallocation Principal", "Cashless Roll",
             "Decrease", "Increase", "Ongoing Fee", "Letter of Credit Fee", "Principal",
             "Interest", "Principal+Interest", "Principal+Interest+Fee", "Timebound",
             "Foreign Currency"]


for idx, item in enumerate(st.session_state["email_data"]):
    email = item["email"]
    result = item["result"]

    if not result:
        continue

    classification = result["classification"]
    extraction = result["extraction"]
    duplicate = result["duplicate"]

    confidence = classification.confidence_score
    primary_type = classification.primary_request_type
    sub_type = classification.sub_request_type or ""
    is_duplicate = duplicate.duplicate_flag  # True if duplicate, False otherwise

    email_id = email['id']

    if f"edit_{email_id}" not in st.session_state["edit_mode"]:
        st.session_state["edit_mode"][f"edit_{email_id}"] = False

    with st.expander(f"{email['subject']}", expanded=False):
        st.write(f"**Date:** {email['date']}")
        st.write(f"**From:** {email['from']}")

        if st.button(f"View Full Email", key=f"toggle_{idx}"):
            st.session_state["show_email_body"][idx] = not st.session_state["show_email_body"].get(idx, False)

        if st.session_state["show_email_body"].get(idx, False):
            st.write(email["full_body"])

        if email["attachments"]:
            st.write("**Attachments:**")
            for attachment in email["attachments"]:
                file_name = os.path.basename(attachment["path"])
                with open(attachment["path"], "rb") as file:
                    file_bytes = file.read()
                st.download_button(label=f"{file_name}", data=file_bytes, file_name=file_name, mime="application/octet-stream")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("Classification Details")
            st.markdown(
                f"""
                - **Primary Request Type:** {primary_type}
                - **Additional Request Type:** {classification.additional_request_types or "N/A"}
                - **Sub Request Type:** {sub_type}
                - **Confidence Score:** {confidence:.2f}
                - **Classification Reason:** {classification.reason or "N/A"}
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.write("Extraction Details")
            if extraction:
                st.markdown(
                    f"""
                    - **Deal Name:** {extraction.deal_name or "Unknown"}
                    - **Borrower:** {extraction.borrower or "Unknown"}
                    - **Amount:** {extraction.amount or "N/A"}
                    - **Payment Date:** {extraction.payment_date or "N/A"}
                    - **Transaction Reference:** {extraction.transaction_reference or "N/A"}
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.write("No extraction data available.")

        with col3:
            st.write("Duplicate Details")
            st.markdown(
                f"""
                - **Duplicate:** {is_duplicate}
                - **Reason:** {duplicate.duplicate_reason or "N/A"}
                """,
                unsafe_allow_html=True
            )

    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 1.5, 1.5, 2])  # Adjusted spacing


    col1.text(email['subject'])
    is_editing = st.session_state["edit_mode"][f"edit_{email_id}"]

    if is_editing:
        current_primary_idx = REQUEST_TYPES.index(primary_type) if primary_type in REQUEST_TYPES else 0
        current_sub_idx = SUB_TYPES.index(sub_type) if sub_type in SUB_TYPES else 0

        new_primary = col2.selectbox("Request Type", REQUEST_TYPES, index=current_primary_idx, key=f"edit_req_type_{email_id}")
        new_sub = col3.selectbox("Sub Request Type", SUB_TYPES, index=current_sub_idx, key=f"edit_sub_req_{email_id}")
    else:
        col2.text_input("Request Type", value=primary_type, key=f"req_type_{email_id}", disabled=True)
        col3.text_input("Sub Request Type", value=sub_type, key=f"sub_req_{email_id}", disabled=True)

    # Flag Column (Red Dot for Duplicate, Green Dot for Unique)
    col4.markdown("🔴" if is_duplicate else "")

    col5.text(f"{confidence:.2f}")

    with col6:
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("✅", key=f"approve_{email_id}"):
                pass  # Handle approval logic

        with btn_col2:
            if st.button("✏️", key=f"edit_btn_{email_id}"):
                if st.session_state["edit_mode"][f"edit_{email_id}"]:
                    st.session_state["email_data"][idx]["result"]["classification"].primary_request_type = st.session_state[f"edit_req_type_{email_id}"]
                    st.session_state["email_data"][idx]["result"]["classification"].sub_request_type = st.session_state[f"edit_sub_req_{email_id}"]
                st.session_state["edit_mode"][f"edit_{email_id}"] = not st.session_state["edit_mode"][f"edit_{email_id}"]
                st.rerun()

#
# for idx, item in enumerate(st.session_state["email_data"]):
#     email = item["email"]
#     result = item["result"]
#
#     if not result:
#         continue
#
#     classification = result["classification"]
#     extraction = result["extraction"]
#     duplicate = result["duplicate"]
#
#     confidence = classification.confidence_score
#     primary_type = classification.primary_request_type
#     sub_type = classification.sub_request_type or ""
#
#     email_id = email['id']
#
#     # Initialize edit mode if not set
#     if f"edit_{email_id}" not in st.session_state["edit_mode"]:
#         st.session_state["edit_mode"][f"edit_{email_id}"] = False
#
#     with st.expander(f"{email['subject']}", expanded=False):
#         st.write(f"**Date:** {email['date']}")
#         st.write(f"**From:** {email['from']}")
#
#         # Toggle button for viewing full email body
#         if st.button(f"View Full Email", key=f"toggle_{idx}"):
#             st.session_state["show_email_body"][idx] = not st.session_state["show_email_body"].get(idx, False)
#
#         if st.session_state["show_email_body"].get(idx, False):
#             st.write(email["full_body"])
#
#         # Display attachments with download links
#         if email["attachments"]:
#             st.write("**Attachments:**")
#             for attachment in email["attachments"]:
#                 file_name = os.path.basename(attachment["path"])
#                 with open(attachment["path"], "rb") as file:
#                     file_bytes = file.read()
#                 st.download_button(label=f"{file_name}", data=file_bytes, file_name=file_name,
#                                    mime="application/octet-stream")
#
#         # Extracted Data Display
#         if extraction:
#             st.write("Extracted Data")
#             st.markdown(
#                 f"""
#                 - **Deal Name:** {extraction.deal_name or "Unknown"}
#                 - **Borrower:** {extraction.borrower or "Unknown"}
#                 - **Amount:** {extraction.amount or "N/A"}
#                 - **Payment Date:** {extraction.payment_date or "N/A"}
#                 - **Transaction Reference:** {extraction.transaction_reference or "N/A"}
#                 - **Duplicate:** {duplicate.duplicate_flag or "N/A"}
#                 - **Classificaton reason:** {classification.reason or "N/A"}
#                 """,
#                 unsafe_allow_html=True
#             )
#
#         # Classification Details
#         st.write("Classification Results")
#         st.markdown(
#             f"""
#             - **Primary Request Type:** {primary_type}
#             - **Sub Request Type:** {sub_type}
#             - **Confidence Score:** {confidence:.2f}
#             """,
#             unsafe_allow_html=True
#         )
#
#     col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 2])
#
#     col1.text(email['subject'])
#
#     # Get edit mode state
#     is_editing = st.session_state["edit_mode"][f"edit_{email_id}"]
#
#     if is_editing:
#         # Show dropdowns in edit mode
#         current_primary_idx = REQUEST_TYPES.index(primary_type) if primary_type in REQUEST_TYPES else 0
#         current_sub_idx = SUB_TYPES.index(sub_type) if sub_type in SUB_TYPES else 0
#
#         new_primary = col2.selectbox(
#             "Request Type",
#             options=REQUEST_TYPES,
#             index=current_primary_idx,
#             key=f"edit_req_type_{email_id}"
#         )
#
#         new_sub = col3.selectbox(
#             "Sub Request Type",
#             options=SUB_TYPES,
#             index=current_sub_idx,
#             key=f"edit_sub_req_{email_id}"
#         )
#     else:
#         # Show text in view mode
#         col2.text_input(
#             "Request Type",
#             value=primary_type,
#             key=f"req_type_{email_id}",
#             disabled=True
#         )
#         col3.text_input(
#             "Sub Request Type",
#             value=sub_type,
#             key=f"sub_req_{email_id}",
#             disabled=True
#         )
#
#     col4.text(f"{confidence:.2f}")
#
#     with col5:
#         btn_col1, btn_col2 = st.columns(2)
#         with btn_col1:
#             if st.button("✅", key=f"approve_{email_id}"):
#                 pass  # Handle approval logic
#
#         with btn_col2:
#             if st.button("✏️", key=f"edit_btn_{email_id}"):
#                 # Toggle edit mode
#                 if st.session_state["edit_mode"][f"edit_{email_id}"]:
#                     # Save the edited values
#                     st.session_state["email_data"][idx]["result"]["classification"].primary_request_type = \
#                     st.session_state[f"edit_req_type_{email_id}"]
#                     st.session_state["email_data"][idx]["result"]["classification"].sub_request_type = st.session_state[
#                         f"edit_sub_req_{email_id}"]
#
#                 # Toggle edit mode
#                 st.session_state["edit_mode"][f"edit_{email_id}"] = not st.session_state["edit_mode"][
#                     f"edit_{email_id}"]
#                 st.rerun()  # Refresh UI to reflect changes
#

# Footer
st.markdown("---")
st.markdown(f"**Total emails processed:** {len(st.session_state['processed_emails'])}")
if st.session_state["last_processed_time"]:
    st.markdown(f"**Last processed at:** {st.session_state['last_processed_time'].strftime('%Y-%m-%d %H:%M:%S')}")