import re
import time
from typing import Any

import httpx

from app.config import settings


class GenesisClientError(Exception):
    pass


class GenesisClient:
    def __init__(self, timeout_seconds: int = 45) -> None:
        self.timeout_seconds = timeout_seconds
        self._base_url = settings.genesis_base_url.rstrip("/")
        self._headers = {
            "username": settings.genesis_username,
            "password": settings.genesis_password,
        }

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self._base_url}{endpoint}",
                data=payload,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise GenesisClientError(f"Genesis request failed: {exc}") from exc

        try:
            return response.json()
        except ValueError as exc:
            raise GenesisClientError("Genesis response is not valid JSON.") from exc

    @staticmethod
    def _extract_status(body: dict[str, Any]) -> tuple[int | None, str]:
        status = body.get("Status", {})
        return status.get("Code"), str(status.get("Content", ""))

    @staticmethod
    def _extract_content(body: dict[str, Any]) -> str | None:
        object_block = body.get("Object")
        if not isinstance(object_block, dict):
            return None
        text = str(object_block.get("Content", "")).strip()
        return text or None

    @staticmethod
    def _extract_result_name(status_content: str) -> str | None:
        match = re.search(r"abgerufen werden:\s*([A-Za-z0-9_-]+)", status_content)
        if match:
            return match.group(1)
        return None

    def _fetch_async_result(self, result_name: str) -> str:
        payload: dict[str, Any] = {"name": result_name, "format": "datencsv"}

        # Background jobs can take several minutes for large tables.
        deadline = time.monotonic() + 300
        while time.monotonic() < deadline:
            body = self._post("/data/result", payload)
            status_code, status_content = self._extract_status(body)
            if status_code in {99, 104}:
                time.sleep(3)
                continue
            if isinstance(status_code, int) and status_code >= 90:
                raise GenesisClientError(
                    f"Genesis async result error {status_code} for result={result_name}: {status_content}",
                )
            content = self._extract_content(body)
            if content:
                return content
            time.sleep(3)

        raise GenesisClientError(
            f"Genesis async result timeout for result={result_name}.",
        )

    def fetch_table_csv(
        self,
        table_name: str,
        start_year: int,
        regional_variable: str | None = None,
        regional_key: str | None = None,
    ) -> str:
        if not settings.genesis_username or not settings.genesis_password:
            raise GenesisClientError(
                "Genesis credentials are missing. Please set GENESIS_USERNAME and GENESIS_PASSWORD in .env.",
            )

        payload: dict[str, Any] = {
            "name": table_name,
            "startyear": str(start_year),
            "format": "datencsv",
        }
        if regional_variable and regional_key:
            payload["regionalvariable"] = regional_variable
            payload["regionalkey"] = regional_key

        body = self._post("/data/table", payload)
        status_code, status_content = self._extract_status(body)

        # Fallback for tables too large for direct dialog response.
        if status_code == 98:
            payload_with_job = dict(payload)
            payload_with_job["job"] = "true"
            body = self._post("/data/table", payload_with_job)
            status_code, status_content = self._extract_status(body)

        if status_code == 99:
            result_name = self._extract_result_name(status_content)
            if not result_name:
                raise GenesisClientError(
                    f"Genesis async job created but no result name found for table={table_name}: {status_content}",
                )
            return self._fetch_async_result(result_name)

        if (
            isinstance(status_code, int)
            and status_code >= 90
            or isinstance(status_content, str)
            and "fehler" in status_content.lower()
        ):
            raise GenesisClientError(
                f"Genesis error {status_code} for table={table_name}, regionalvariable={regional_variable}, regionalkey={regional_key}: {status_content}",
            )

        content = self._extract_content(body)
        if not content:
            raise GenesisClientError("Genesis response does not contain table content.")
        return content

    def fetch_timeseries_csv(
        self,
        table_name: str,
        start_year: int,
    ) -> str:
        if not settings.genesis_username or not settings.genesis_password:
            raise GenesisClientError(
                "Genesis credentials are missing. Please set GENESIS_USERNAME and GENESIS_PASSWORD in .env.",
            )

        payload: dict[str, Any] = {
            "name": table_name,
            "startyear": str(start_year),
            "format": "datencsv",
        }
        body = self._post("/data/timeseries", payload)
        status_code, status_content = self._extract_status(body)

        if (
            isinstance(status_code, int)
            and status_code >= 90
            or isinstance(status_content, str)
            and "fehler" in status_content.lower()
        ):
            raise GenesisClientError(
                f"Genesis error {status_code} for timeseries={table_name}: {status_content}",
            )

        content = self._extract_content(body)
        if not content:
            raise GenesisClientError("Genesis response does not contain timeseries content.")
        return content
