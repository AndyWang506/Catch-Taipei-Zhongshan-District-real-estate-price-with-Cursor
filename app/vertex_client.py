"""
Lightweight Vertex AI prediction client.
Uses either a deployed Endpoint (PREDICT) or direct Model.predict.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from google.cloud import aiplatform


def vertex_predict(
    instances: List[Dict[str, Any]],
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run a prediction using Vertex AI.
    Requires environment variables:
      - GOOGLE_CLOUD_PROJECT
      - VERTEX_LOCATION (e.g., us-central1)
      - and one of:
          * VERTEX_ENDPOINT_ID (Endpoint.predict)
          * VERTEX_MODEL_NAME (projects/.../models/...)
    """

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("VERTEX_LOCATION", "us-central1")
    endpoint_id = os.getenv("VERTEX_ENDPOINT_ID")
    model_name = os.getenv("VERTEX_MODEL_NAME")

    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is not set.")

    aiplatform.init(project=project, location=location)

    if endpoint_id:
        endpoint = aiplatform.Endpoint(endpoint_id=endpoint_id)
        prediction = endpoint.predict(instances=instances, parameters=parameters or {})
        return {
            "predictions": prediction.predictions,
            "deployed_model_id": prediction.deployed_model_id,
        }

    if model_name:
        model = aiplatform.Model(model_name=model_name)
        prediction = model.predict(instances=instances, parameters=parameters or {})
        return {"predictions": prediction.predictions}

    raise RuntimeError("Set VERTEX_ENDPOINT_ID or VERTEX_MODEL_NAME to use Vertex AI.")


