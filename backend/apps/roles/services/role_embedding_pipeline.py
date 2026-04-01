"""
Offline pipeline to build FAISS index for IT roles from CSV.
Uses backend/apps/documents/data/IT_Job_Roles_Skills.csv and core embedding service.
convert IT job roles into embeddings and store them in a FAISS vector database for semantic search.
"""
#Improves type hinting performance and forward references.
from __future__ import annotations

#Used to record logs for debugging and monitoring.
import logging
#Used to handle file paths in a platform-independent way.
from pathlib import Path
#Used for type hinting of lists and dictionaries.
from typing import List, Dict

#Used for data manipulation and analysis, especially for handling CSV files.
import pandas as pd
#Used to access Django settings, such as file paths and embedding dimensions.
from django.conf import settings

#Used to generate vector embeddings from text using the core embedding service.
from core.services.embedding_service import encode
#Used to manage the FAISS index for role embeddings, including creation and search functionality.
from .role_faiss_manager import RoleFAISSManager

#Set up logging for this module.
logger = logging.getLogger(__name__)

# CSV lives in documents app data (single source of truth)
DOCUMENTS_DATA_CSV = Path(settings.BASE_DIR) / "apps" / "documents" / "data" / "IT_Job_Roles_Skills.csv"

#Custom exception for errors in the role embedding pipeline, such as missing dataset or invalid format.
class RolePipelineException(Exception):
    """Pipeline / dataset error."""
    pass


#Main class for the role embedding pipeline, responsible for loading the dataset, generating embeddings, and building the FAISS index.
class RoleEmbeddingPipeline:
    """Build FAISS index for IT roles from CSV (Job Title, Job Description, Skills)."""

    #Initialize the pipeline by setting the dataset path and checking if it exists. Raises an exception if the dataset is not found.
    def __init__(self) -> None:
        self.dataset_path = DOCUMENTS_DATA_CSV
        if not self.dataset_path.exists():
            raise RolePipelineException(
                f"Dataset not found: {self.dataset_path} (expected backend/apps/documents/data/IT_Job_Roles_Skills.csv)"
            )

    #Run the pipeline: load the dataset, generate embeddings, and build the FAISS index. Logs progress and raises exceptions for any issues encountered.
    def run(self) -> None:
        logger.info("Loading roles dataset...")
        df = pd.read_csv(self.dataset_path, encoding="latin1")
        required_cols = {"Job Title", "Job Description", "Skills"}
        #Check if the required columns are present in the dataset. If not, raise an exception. Also drop any rows with missing values in these columns.
        if not required_cols.issubset(df.columns):
            raise RolePipelineException(f"Dataset must contain columns: {required_cols}")
        df = df.dropna(subset=list(required_cols))
        logger.info("Loaded %s roles.", len(df))

        #Calls helper function to combine role information into text.
        texts = self._build_role_text(df)
        #Creates metadata dictionary.
        metadata = self._build_metadata(df)

        logger.info("Generating embeddings (batch, normalized)...")
        #Generate vector embeddings for the combined role texts using the core embedding service. 
        #The embeddings are normalized and returned as a NumPy array.
        vectors = encode(texts, normalize=True, return_numpy=True)

        logger.info("Building FAISS index...")
        manager = RoleFAISSManager()
        manager.create_index(vectors, metadata)
        logger.info("FAISS build complete.")

    '''Job Title: Data Scientist.
        Job Description: Build predictive ML models.
        Required Skills: Python, Machine Learning, Pandas.'''
    def _build_role_text(self, df: pd.DataFrame) -> List[str]:
        texts = []
        for _, row in df.iterrows():
            title = str(row["Job Title"]).strip()
            desc = str(row["Job Description"]).strip()
            skills = str(row["Skills"]).strip()
            combined = (
                f"Job Title: {title}. "
                f"Job Description: {desc}. "
                f"Required Skills: {skills}."
            )
            texts.append(combined)
        return texts

    def _build_metadata(self, df: pd.DataFrame) -> List[Dict]:
        metadata = []
        #Checks if dataset has certifications column.
        has_certs = "Certifications" in df.columns
        for _, row in df.iterrows():
            meta = {
                "role": row["Job Title"],
                "skills": row["Skills"],
                "description": row["Job Description"],
            }
            #Checks if certification exists. If so, adds it to metadata; otherwise, sets it to an empty string.
            if has_certs and pd.notna(row.get("Certifications")):
                meta["certifications"] = str(row["Certifications"]).strip()
            else:
                meta["certifications"] = ""
            metadata.append(meta)
        return metadata
