# # gmail_service.py - Gmail API integration
# import os
# import base64
# import re
# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials
# from config import CREDENTIALS_FILE
#
#
# def get_gmail_service():
#     """Initialize and return Gmail API service"""
#     creds = None
#     if os.path.exists(CREDENTIALS_FILE):
#         creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE)
#         return build("gmail", "v1", credentials=creds)
#     return None
#
#
# def save_email_attachments(service, message_id, attachments_dir="attachments"):
#     """Fetch and store attachments from an email. Returns list of saved file paths."""
#     attachment_paths = []
#     try:
#         # Ensure attachments directory exists
#         os.makedirs(attachments_dir, exist_ok=True)
#
#         message = service.users().messages().get(userId="me", id=message_id).execute()
#         payload = message.get("payload", {})
#
#         if "parts" in payload:
#             for part in payload["parts"]:
#                 if part.get("filename"):
#                     attachment_id = part["body"].get("attachmentId")
#                     if attachment_id:
#                         attachment = service.users().messages().attachments().get(
#                             userId="me", messageId=message_id, id=attachment_id
#                         ).execute()
#
#                         file_data = base64.urlsafe_b64decode(attachment["data"])
#                         file_path = os.path.join(attachments_dir, part["filename"])
#
#                         with open(file_path, "wb") as f:
#                             f.write(file_data)
#                         attachment_paths.append(file_path)
#                         print(f"Saved: {file_path}")
#     except Exception as e:
#         print(f"Error fetching attachments: {e}")
#
#     return attachment_paths
#
#
# def extract_email_address(sender):
#     """Extract email address from sender string"""
#     match = re.search(r"<(.*?)>", sender)
#     return match.group(1) if match else sender
#
#
# def get_email_body(payload):
#     """Recursively extract email body from nested parts"""
#     if "parts" in payload:
#         for part in payload["parts"]:
#             if part["mimeType"] == "text/plain":
#                 return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
#             elif part["mimeType"] == "text/html":
#                 return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
#             elif "parts" in part:
#                 return get_email_body(part)  # Recursive call
#     elif "body" in payload and "data" in payload["body"]:
#         return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
#     return "No content available"
#
#
# def get_email_details(service, message_id):
#     """Get detailed information about a specific email"""
#     try:
#         message = service.users().messages().get(userId="me", id=message_id).execute()
#         payload = message["payload"]
#         headers = payload["headers"]
#
#         # Extract email metadata
#         subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
#         sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
#         sender_email = extract_email_address(sender)
#         date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")
#
#         # Get full email body
#         body = get_email_body(payload)
#         snippet = message.get("snippet", "")
#
#         # Initialize email data
#         email_data = {
#             "id": message_id,
#             "subject": subject,
#             "from": sender_email,
#             "date": date,
#             "full_body": body.strip() if body else "No content available",
#             "snippet": snippet
#         }
#
#         return email_data
#     except Exception as e:
#         print(f"Error fetching email details: {e}")
#         return None
#
#
# def fetch_emails(service, max_results=50, label_ids=None):
#     """Fetch emails from inbox (all emails, not just those with attachments)"""
#     if not service:
#         return []
#
#     try:
#         query_params = {
#             "userId": "me",
#             "maxResults": max_results,
#             "labelIds": label_ids if label_ids else ["INBOX"]  # Default to inbox
#         }
#
#         response = service.users().messages().list(**query_params).execute()
#         message_ids = response.get("messages", [])
#         return [msg["id"] for msg in message_ids]
#     except Exception as e:
#         print(f"Error fetching emails: {e}")
#         return []
#
#
# def fetch_emails_after_id(service, last_processed_id=None, max_results=50):
#     """Fetch emails after a specific email ID"""
#     if not service:
#         return []
#
#     try:
#         query = ""
#         if last_processed_id:
#             # Get timestamp of the last processed email
#             last_msg = service.users().messages().get(userId="me", id=last_processed_id).execute()
#             last_internal_date = int(last_msg.get('internalDate', 0))
#             # Fetch newer emails based on timestamp
#             query = f"after:{last_internal_date // 1000}"
#
#         response = service.users().messages().list(
#             userId="me",
#             maxResults=max_results,
#             q=query
#         ).execute()
#
#         message_ids = response.get("messages", [])
#         return [msg["id"] for msg in message_ids]
#     except Exception as e:
#         print(f"Error fetching emails: {e}")
#         return []
# gmail_service.py - Gmail API integration
import os
import base64
import re
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import CREDENTIALS_FILE


def get_gmail_service():
    """Initialize and return Gmail API service"""
    creds = None
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE)
        return build("gmail", "v1", credentials=creds)
    return None


def save_email_attachments(service, message_id, attachments_dir="attachments"):
    """Fetch and store attachments from an email. Returns list of saved file paths."""
    attachment_paths = []
    try:
        # Ensure attachments directory exists
        os.makedirs(attachments_dir, exist_ok=True)

        message = service.users().messages().get(userId="me", id=message_id).execute()
        payload = message.get("payload", {})

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    attachment_id = part["body"].get("attachmentId")
                    if attachment_id:
                        attachment = service.users().messages().attachments().get(
                            userId="me", messageId=message_id, id=attachment_id
                        ).execute()

                        file_data = base64.urlsafe_b64decode(attachment["data"])
                        file_path = os.path.join(attachments_dir, part["filename"])

                        with open(file_path, "wb") as f:
                            f.write(file_data)
                        attachment_paths.append(file_path)
                        print(f"Saved: {file_path}")
    except Exception as e:
        print(f"Error fetching attachments: {e}")

    return attachment_paths


def extract_email_address(sender):
    """Extract email address from sender string"""
    match = re.search(r"<(.*?)>", sender)
    return match.group(1) if match else sender


def get_email_body(payload):
    """Recursively extract email body from nested parts"""
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            elif part["mimeType"] == "text/html":
                return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            elif "parts" in part:
                return get_email_body(part)  # Recursive call
    elif "body" in payload and "data" in payload["body"]:
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
    return "No content available"


def get_email_details(service, message_id, attachments_dir="attachments"):
    """Get complete email details including both emails with and without attachments"""
    try:
        message = service.users().messages().get(userId="me", id=message_id).execute()
        payload = message["payload"]
        headers = payload["headers"]

        # Extract email metadata
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        sender_email = extract_email_address(sender)
        date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")

        # Get full email body
        body = get_email_body(payload)
        snippet = message.get("snippet", "")

        # Initialize email data with basic information
        email_data = {
            "id": message_id,
            "subject": subject,
            "from": sender_email,
            "date": date,
            "full_body": body.strip() if body else "No content available",
            "snippet": snippet,
            "attachments": []
        }

        # Check for and save attachments if they exist
        if "parts" in payload and any(part.get("filename") for part in payload["parts"]):
            attachment_paths = save_email_attachments(service, message_id, attachments_dir)
            email_data["attachments"] = [{"path": path} for path in attachment_paths]

        return email_data
    except Exception as e:
        print(f"Error fetching email details: {e}")
        return None


def fetch_all_emails(service, max_results=100, label_ids=["INBOX"]):
    """Fetch all emails from specified labels (default: INBOX)"""
    if not service:
        return []

    try:
        response = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            labelIds=label_ids
        ).execute()

        messages = response.get("messages", [])
        while "nextPageToken" in response and len(messages) < max_results:
            page_token = response["nextPageToken"]
            response = service.users().messages().list(
                userId="me",
                maxResults=max_results - len(messages),
                pageToken=page_token,
                labelIds=label_ids
            ).execute()
            messages.extend(response.get("messages", []))

        return [msg["id"] for msg in messages]
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []


def fetch_new_emails_since(service, last_processed_date=None, max_results=100):
    """Fetch new emails since last processed date"""
    if not service:
        return []

    try:
        query = f"after:{int(last_processed_date.timestamp())}" if last_processed_date else ""

        response = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q=query,
            labelIds=["INBOX"]
        ).execute()

        messages = response.get("messages", [])
        while "nextPageToken" in response and len(messages) < max_results:
            page_token = response["nextPageToken"]
            response = service.users().messages().list(
                userId="me",
                maxResults=max_results - len(messages),
                pageToken=page_token,
                q=query,
                labelIds=["INBOX"]
            ).execute()
            messages.extend(response.get("messages", []))

        return [msg["id"] for msg in messages]
    except Exception as e:
        print(f"Error fetching new emails: {e}")
        return []