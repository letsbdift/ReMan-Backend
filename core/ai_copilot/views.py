"""
ReMan AI Copilot - API Views
"""

import json
import logging
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .service import AICopilotService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def copilot_chat_api(request: HttpRequest) -> JsonResponse:
    """
    POST /api/copilot/chat/
    Payload:
    {
        "prompt": "What is eka niveshana and how to get single site approval in Karnataka?",
        "history": [{"sender": "USER", "text": "..."}],
        "api_key": "AIzaSy...",  # Optional if passed via X-Gemini-API-Key header
        "project_id": "1"        # Optional project filter
    }
    """
    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            data = {}

        prompt = data.get("prompt", "").strip()
        if not prompt:
            # Fallback to form-encoded if passed
            prompt = request.POST.get("prompt", "").strip()

        if not prompt:
            return JsonResponse({
                "status": "error",
                "error_type": "empty_prompt",
                "reply": "Please provide a query or question.",
                "sources": []
            }, status=400)

        # Retrieve API key from body or header
        api_key = data.get("api_key", "").strip()
        if not api_key:
            api_key = request.headers.get("X-Gemini-API-Key", "").strip()
        if not api_key:
            api_key = request.META.get("HTTP_X_GEMINI_API_KEY", "").strip()

        history = data.get("history", [])
        project_id = data.get("project_id", request.POST.get("project_id", "All"))

        result = AICopilotService.handle_query(
            query=prompt,
            conversation_history=history,
            api_key=api_key,
            project_id=project_id
        )

        return JsonResponse(result, status=200)

    except Exception as e:
        logger.exception("Unexpected error in copilot_chat_api")
        return JsonResponse({
            "status": "error",
            "error_type": "internal_server_error",
            "reply": f"⚠️ **Backend Processing Error:** {str(e)}",
            "sources": []
        }, status=500)
