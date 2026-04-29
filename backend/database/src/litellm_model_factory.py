"""
Single entry for LiteLLM model wiring: Vertex AI (GCP) when VERTEX_MODEL_ID / GEMINI_VERTEX_MODEL
is set, otherwise AWS Bedrock via BEDROCK_MODEL_ID.
"""

from __future__ import annotations

import os

from agents.extensions.models.litellm_model import LitellmModel


def create_litellm_model() -> LitellmModel:
    """
    Vertex (GCP): set VERTEX_MODEL_ID or GEMINI_VERTEX_MODEL (e.g. gemini-2.0-flash-001),
    plus GCP_PROJECT_ID (maps to VERTEXAI_PROJECT) and GCP_REGION or VERTEXAI_LOCATION.

    Bedrock (AWS): set BEDROCK_MODEL_ID and BEDROCK_REGION (default us-west-2).
    """
    vertex_model = os.getenv("VERTEX_MODEL_ID") or os.getenv("GEMINI_VERTEX_MODEL")
    if vertex_model:
        project = os.getenv("GCP_PROJECT_ID") or os.getenv("VERTEXAI_PROJECT")
        location = (
            os.getenv("VERTEXAI_LOCATION")
            or os.getenv("GCP_REGION")
            or "us-central1"
        )
        if project:
            os.environ.setdefault("VERTEXAI_PROJECT", project)
        os.environ.setdefault("VERTEXAI_LOCATION", location)
        model_ref = vertex_model.strip()
        if not model_ref.startswith("vertex_ai/"):
            model_ref = f"vertex_ai/{model_ref}"
        return LitellmModel(model=model_ref)

    model_id = os.getenv(
        "BEDROCK_MODEL_ID",
        "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    )
    bedrock_region = os.getenv("BEDROCK_REGION", "us-west-2")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    return LitellmModel(model=f"bedrock/{model_id}")
