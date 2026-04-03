from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


import uuid
import threading


from django.db import transaction

from .supabase_utils import upload_pdf_to_supabase
from .supabase_utils import SupabaseConnectionError, SupabaseUploadError
from .models import Document
from apps.skills.services.resume_skill_tool import SkillTool, normalize_skill
from apps.skills.models import Skill, UserSkill
from apps.embeddings.models import SkillEmbedding
from core.services.embedding_service import encode
from apps.roles.services.role_faiss_manager import get_role_faiss_manager


def _sync_jobs_for_roles(role_titles: list):
    """
    Background thread: fetch Adzuna jobs for the user's recommended roles.
    Runs after resume upload so the Jobs page shows relevant results.
    Calls sync_jobs once per role title using the 'what' keyword argument.
    """
    try:
        from apps.jobs.services import sync_jobs
        print(f"🔄 Background job sync started for: {role_titles}")
        total_created = 0
        for title in role_titles:
            created = sync_jobs(what=title, max_pages=2)
            total_created += created
        print(f"✅ Background job sync complete — {total_created} new jobs added")
    except Exception as e:
        print(f"❌ Background job sync failed: {e}")


class ResumeUploadView(APIView):
    """
    Upload PDF → Extract Text → Extract Skills (NLP + LLM)
                → Save Document (with recommended_roles) + UserSkills + SkillEmbeddings to DB
                → Trigger background Adzuna sync for recommended roles
                → Return skills + recommended roles to frontend
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        import fitz  # PyMuPDF
        import numpy as np
        try:
            file = request.FILES.get("file")

            if not file:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            if not (file.name or "").lower().endswith(".pdf"):
                return Response({"error": "Only PDF files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

            filename = f"{uuid.uuid4()}_{file.name}"
            pdf_bytes = file.read()

            # 1️⃣ Upload to Supabase
            file_url = upload_pdf_to_supabase(pdf_bytes, filename)

            # 2️⃣ Extract text using PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text()

            print("📄 Extracted Text Length:", len(extracted_text))

            if not extracted_text.strip():
                return Response({"error": "No text extracted from PDF"}, status=status.HTTP_400_BAD_REQUEST)

            # 3️⃣ Extract skills (spaCy rule-based + Gemini LLM)
            skills_data = SkillTool.run(extracted_text)

            # 4️⃣ Save Skill + UserSkill records, keep map for embedding step
            skill_objects = {}
            with transaction.atomic():
                for skill_name in skills_data["all_skills"]:
                    nm = normalize_skill(skill_name)
                    if not nm:
                        continue
                    skill_obj, _ = Skill.objects.get_or_create(
                        normalized_name=nm.lower(),
                        defaults={"name": nm},
                    )
                    UserSkill.objects.get_or_create(
                        user=request.user,
                        skill=skill_obj,
                        defaults={"source": "document"},
                    )
                    skill_objects[nm] = skill_obj
            print(f"✅ UserSkills saved: {len(skill_objects)} skills")

            # 5️⃣ Generate and save SkillEmbeddings
            if skill_objects:
                skill_names = list(skill_objects.keys())
                skill_vectors = encode(skill_names, normalize=True, return_numpy=False)
                with transaction.atomic():
                    for skill_name, vector in zip(skill_names, skill_vectors):
                        SkillEmbedding.objects.update_or_create(
                            skill=skill_objects[skill_name],
                            defaults={"vector": vector},
                        )
                print(f"✅ SkillEmbeddings saved: {len(skill_names)} embeddings")

            # 6️⃣ FAISS search for recommended roles
            if skills_data["all_skills"]:
                skills_vectors_np = encode(skills_data["all_skills"], normalize=True, return_numpy=True)
                query_vector = np.mean(skills_vectors_np, axis=0, keepdims=True)
                roles = get_role_faiss_manager().search(query_vector, top_k=30)
                print("✅ Roles searched successfully")
            else:
                roles = []

            # 7️⃣ Build recommended_roles — top 5 by score
            recommended_roles = [
                {
                    "role":        meta.get("role", ""),
                    "description": meta.get("description", ""),
                    "skills":      meta.get("skills", ""),
                    "score":       round(score, 4),
                }
                for score, meta in roles
            ]
            top_roles = recommended_roles[:5]

            # 8️⃣ Save Document — recommended_roles persists across logout/login
            document = Document.objects.create(
                user=request.user,
                file_url=file_url,
                parsed=True,
                extracted_text=extracted_text,
                recommended_roles=recommended_roles,
            )
            print(f"✅ Document saved: {document.id}")

            # 9️⃣ Trigger background Adzuna sync for the recommended roles
            # Runs in a daemon thread so the API response returns immediately.
            # Jobs page will show results within ~10-15 seconds after upload.
            role_titles = [r["role"] for r in top_roles if r.get("role")]
            if role_titles:
                threading.Thread(
                    target=_sync_jobs_for_roles,
                    args=(role_titles,),
                    daemon=True,
                ).start()

            # 🔟 Return response to frontend
            return Response({
                "message": "Skills extracted and saved successfully",
                "file_url": file_url,
                "rule_based_skills": skills_data["rule_based_skills"],
                "llm_skills": skills_data["llm_skills"],
                "all_skills": skills_data["all_skills"],
                "recommended_roles": recommended_roles,
            }, status=status.HTTP_200_OK)

        except SupabaseConnectionError as e:
            print("❌ Supabase connection error:", str(e))
            return Response(
                {
                    "error": "Supabase is not reachable from the backend (connection timeout).",
                    "detail": str(e),
                    "hint": "Try a different network (mobile hotspot/VPN), allow outbound 443 in firewall, or change DNS (1.1.1.1 / 8.8.8.8).",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except SupabaseUploadError as e:
            print("❌ Supabase upload error:", str(e))
            return Response(
                {"error": "Supabase upload failed.", "detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception as e:
            print("❌ Upload API Error:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def latest_resume_roles(request):
    """
    Return recommended_roles from the user's most recent uploaded document.
    Used by the Roles page to restore the 'From your resume' section after
    logout/login, without requiring a re-upload.
    """
    doc = Document.objects.filter(
        user=request.user,
        parsed=True,
    ).order_by("-uploaded_at").first()

    if not doc:
        return Response({"recommended_roles": []})

    return Response({"recommended_roles": doc.recommended_roles or []})