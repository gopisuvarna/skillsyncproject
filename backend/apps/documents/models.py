"""Document model for user uploads."""
import uuid
from django.conf import settings
from django.db import models


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    # Store the URL of the uploaded file (supabase url)
    file_url = models.URLField(max_length=512)
    # uploaded timestamp
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Whether the document has been parsed and text extracted
    parsed = models.BooleanField(default=False)
    # The extracted text from the document (after parsing)
    extracted_text = models.TextField(blank=True)
    # Recommended roles from FAISS search at upload time — persisted so they
    # survive logout/login without needing to re-upload the resume
    recommended_roles = models.JSONField(default=list, blank=True)