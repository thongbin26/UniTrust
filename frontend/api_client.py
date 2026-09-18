import os
import httpx
from typing import Dict, Any, List

class APIClient:
    def __init__(self):
        # We can read from environment or default to local FastAPI
        self.base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
        self.std_timeout = float(os.getenv("API_STD_TIMEOUT", "10.0"))
        # Local LLMs can be slow (e.g. Qwen3 4B takes 100s+)
        self.llm_timeout = float(os.getenv("API_LLM_TIMEOUT", "120.0"))

    def _get(self, path: str, timeout: float = None) -> Dict[str, Any]:
        try:
            resp = httpx.get(f"{self.base_url}{path}", timeout=timeout or self.std_timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"API Request failed: {e}")

    def _post(self, path: str, json: Dict[str, Any], timeout: float = None) -> Dict[str, Any]:
        try:
            resp = httpx.post(f"{self.base_url}{path}", json=json, timeout=timeout or self.std_timeout)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            raise RuntimeError(f"API Request failed: {e}")

    def verify_claim(self, text: str, use_llm: bool = False, top_k: int = 5) -> Dict[str, Any]:
        timeout = self.llm_timeout if use_llm else self.std_timeout
        payload = {
            "text": text,
            "use_llm": use_llm,
            "top_k": top_k
        }
        return self._post("/verify", json=payload, timeout=timeout)

    def list_notices(self) -> List[Dict[str, Any]]:
        return self._get("/evidence/notices")

    def get_notice(self, notice_id: int) -> Dict[str, Any]:
        return self._get(f"/evidence/notices/{notice_id}")

    def get_notice_versions(self, notice_id: int) -> List[Dict[str, Any]]:
        return self._get(f"/evidence/notices/{notice_id}/versions")

    def get_notice_changes(self, notice_id: int) -> Dict[str, Any]:
        return self._get(f"/evidence/notices/{notice_id}/changes")

    def get_for_you(self, faculty: str = None, major: str = None, cohort: str = None, program: str = None) -> Dict[str, Any]:
        payload = {
            "faculty": faculty,
            "major": major,
            "cohort": cohort,
            "program": program
        }
        return self._post("/for-you", json=payload)

    def for_you(self, profile: dict) -> Dict[str, Any]:
        """Canonical method used by For You page."""
        return self._post("/for-you", json=profile)

api_client = APIClient()
