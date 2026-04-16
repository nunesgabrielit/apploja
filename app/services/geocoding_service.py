from __future__ import annotations

from decimal import Decimal
from logging import getLogger
from typing import Any

import httpx

logger = getLogger(__name__)


class GeocodingService:
    base_url = "https://nominatim.openstreetmap.org/search"

    async def geocode_address(
        self,
        *,
        street: str,
        number: str,
        district: str,
        city: str,
        state: str,
        zip_code: str,
    ) -> tuple[Decimal, Decimal] | None:
        query = ", ".join(
            part
            for part in [
                f"{street}, {number}",
                district,
                city,
                state,
                zip_code,
                "Brasil",
            ]
            if part
        )

        params = {
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "br",
            "addressdetails": 0,
        }
        headers = {"User-Agent": "WMDistribuidora/1.0 (admin@wmdistribuidora.local)"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(self.base_url, params=params, headers=headers)
                response.raise_for_status()
        except httpx.HTTPError:
            logger.warning("Geocoding request failed for query %s", query, exc_info=True)
            return None

        data = response.json()
        if not isinstance(data, list) or not data:
            return None

        first_result = data[0]
        latitude = first_result.get("lat")
        longitude = first_result.get("lon")
        if latitude is None or longitude is None:
            return None

        try:
            return Decimal(str(latitude)), Decimal(str(longitude))
        except Exception:
            logger.warning("Invalid geocoding payload for query %s: %s", query, first_result)
            return None
