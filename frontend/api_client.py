import os
import httpx
from typing import Dict, Any, List


class URLVerificationRequestError(RuntimeError):
    """Safe URL-fetch failure returned by the API."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class APIClient:
    def __init__(self):
        # We can read from environment or default to local FastAPI
        self.base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
        self.std_timeout = float(os.getenv("API_STD_TIMEOUT", "10.0"))
        # Local LLMs can be slow (e.g. Qwen3 4B takes 100s+)
        self.llm_timeout = float(os.getenv("API_LLM_TIMEOUT", "120.0"))
        # Local CPU OCR plus verification needs more time than ordinary API calls.
        self.image_timeout = float(os.getenv("API_IMAGE_TIMEOUT", "120.0"))
        self.url_timeout = float(os.getenv("API_URL_TIMEOUT", "30.0"))

    def _get(self, path: str, timeout: float = None) -> Dict[str, Any] | List[Dict[str, Any]]:
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

    def _post_multipart(self, path: str, files: dict, data: dict, timeout: float = None) -> Dict[str, Any]:
        try:
            resp = httpx.post(
                f"{self.base_url}{path}",
                files=files,
                data=data,
                timeout=timeout or self.std_timeout,
            )
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

    def verify_image(
        self,
        image_bytes: bytes,
        filename: str,
        content_type: str | None,
        use_llm: bool = False,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        timeout = max(self.image_timeout, self.llm_timeout) if use_llm else self.image_timeout
        return self._post_multipart(
            "/verify/image",
            files={"image": (filename, image_bytes, content_type or "application/octet-stream")},
            data={"top_k": str(top_k), "use_llm": str(use_llm).lower()},
            timeout=timeout,
        )

    def verify_url(self, url: str, top_k: int = 5, use_llm: bool = False) -> Dict[str, Any]:
        timeout = max(self.url_timeout, self.llm_timeout) if use_llm else self.url_timeout
        try:
            response = httpx.post(
                f"{self.base_url}/verify/url",
                json={"url": url, "top_k": top_k, "use_llm": use_llm},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            try:
                detail = exc.response.json().get("detail", {})
                if isinstance(detail, dict) and isinstance(detail.get("code"), str):
                    raise URLVerificationRequestError(detail["code"]) from exc
            except (TypeError, ValueError):
                pass
            raise URLVerificationRequestError("FETCH_FAILED") from exc
        except httpx.HTTPError as exc:
            raise URLVerificationRequestError("FETCH_FAILED") from exc

    def list_notices(self) -> List[Dict[str, Any]]:
        return self._get("/evidence/notices")

    def get_search_index(self) -> List[Dict[str, Any]]:
        return self._get("/evidence/search-index")

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
