# Used to generate unique filenames
import uuid

# Used for resolving DNS / IP addresses (network debugging)
import socket

# Used to extract hostname from a URL
from urllib.parse import urlparse

# Supabase Python client
from supabase import create_client

# Access Django settings (to get Supabase credentials)
from django.conf import settings

# HTTP client library (used internally by supabase)
import httpx


# ==========================================================
# SUPABASE CONFIGURATION
# ==========================================================

# Read Supabase credentials from Django settings
# strip() removes accidental spaces
SUPABASE_URL = (settings.SUPABASE_URL or "").strip()
SUPABASE_KEY = (settings.SUPABASE_KEY or "").strip()

# Create Supabase client instance
# This is used to communicate with Supabase storage
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ==========================================================
# CUSTOM EXCEPTION CLASSES
# ==========================================================

# Base error for any upload-related issue
class SupabaseUploadError(RuntimeError):
    pass


# More specific error for connection-related failures
class SupabaseConnectionError(SupabaseUploadError):
    pass


# ==========================================================
# HELPER FUNCTION: Resolve IPs of Supabase URL
# ==========================================================

def _resolved_ips_for_url(url: str) -> list[str]:
    """
    Resolves and returns all IP addresses associated with a URL.
    Useful for debugging network/DNS issues.
    """
    try:
        # Extract hostname from full URL
        host = urlparse(url).hostname
        if not host:
            return []

        # Get address info for HTTPS (port 443)
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)

        ips = []
        for info in infos:
            sockaddr = info[4]
            if sockaddr and sockaddr[0]:
                ips.append(sockaddr[0])

        # Remove duplicate IPs while preserving order
        seen = set()
        out = []
        for ip in ips:
            if ip not in seen:
                seen.add(ip)
                out.append(ip)

        return out

    except Exception:
        # If DNS resolution fails, return empty list
        return []


# ==========================================================
# MAIN FUNCTION: Upload PDF to Supabase Storage
# ==========================================================

def upload_pdf_to_supabase(file_bytes: bytes, filename: str) -> str:
    """
    Uploads a PDF file to Supabase storage bucket named 'resumes'.

    Args:
        file_bytes: Raw file content in bytes format
        filename: Original file name

    Returns:
        Public URL of uploaded file

    Raises:
        SupabaseUploadError
        SupabaseConnectionError
    """

    # Generate unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # Store inside "pdfs" folder inside bucket

















    
    path = f"pdfs/{unique_filename}"

    # Prevent uploading empty files
    if not file_bytes:
        raise SupabaseUploadError("Empty file (0 bytes); nothing to upload.")

    try:
        # Upload file to Supabase storage bucket "resumes"
        res = supabase.storage.from_("resumes").upload(
            path=path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},  # Set MIME type
        )

    # Handle timeout-related errors
    except (httpx.ConnectTimeout, httpx.ReadTimeout,
            httpx.WriteTimeout, httpx.PoolTimeout) as e:

        ips = _resolved_ips_for_url(SUPABASE_URL)
        ip_note = f" Resolved IPs: {ips}." if ips else ""

        raise SupabaseConnectionError(
            f"Supabase request timed out while uploading `{path}`.{ip_note}"
        ) from e

    # Handle network-level transport errors
    except httpx.TransportError as e:

        ips = _resolved_ips_for_url(SUPABASE_URL)
        ip_note = f" Resolved IPs: {ips}." if ips else ""

        raise SupabaseConnectionError(
            f"Supabase connection failed while uploading `{path}`.{ip_note}"
        ) from e

    # Catch any other unexpected errors
    except Exception as e:
        raise SupabaseUploadError(
            f"Supabase upload failed for `{path}`: {e}"
        ) from e


    # ======================================================
    # Handle Different Supabase Response Formats
    # ======================================================

    # supabase-py returns different response types
    # depending on version (dict or object)
    error = None

    if isinstance(res, dict):
        error = res.get("error") or res.get("message")
    else:
        error = getattr(res, "error", None) or getattr(res, "message", None)

    # If upload returned an error, raise exception
    if error:
        raise SupabaseUploadError(
            f"Supabase upload returned an error for `{path}`: {error}"
        )


    # ======================================================
    # Construct Public File URL
    # ======================================================

    base = SUPABASE_URL.rstrip("/")

    # Return publicly accessible URL
    return f"{base}/storage/v1/object/public/resumes/{path}"

