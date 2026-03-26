"""LCSC component search and pricing service."""

from __future__ import annotations
import logging
from typing import Any, Optional

import aiohttp

from config import settings

logger = logging.getLogger(__name__)


class LCSCService:
    """Interface to the LCSC component database."""

    BASE_URL = settings.LCSC_API_URL
    SEARCH_URL = "https://wmsc.lcsc.com/ftps/wm/search/global"
    DETAIL_URL = "https://wmsc.lcsc.com/ftps/wm/product/detail"

    @classmethod
    async def search(cls, keyword: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """Search LCSC for components by keyword."""
        result: dict[str, Any] = {
            "success": False,
            "keyword": keyword,
            "results": [],
            "total": 0,
        }

        payload = {
            "keyword": keyword,
            "currentPage": page,
            "pageSize": page_size,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    cls.SEARCH_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status != 200:
                        result["error"] = f"HTTP {resp.status}"
                        return result

                    data = await resp.json()
                    if data.get("code") == 200 and data.get("result"):
                        raw = data["result"]
                        result["success"] = True
                        result["total"] = raw.get("totalCount", 0)
                        for item in raw.get("productList", []):
                            result["results"].append(cls._normalize_product(item))
        except aiohttp.ClientError as e:
            logger.warning(f"LCSC search network error: {e}")
            result["error"] = f"Network error: {str(e)}"
        except Exception as e:
            logger.warning(f"LCSC search error: {e}")
            result["error"] = str(e)

        return result

    @classmethod
    async def get_detail(cls, lcsc_code: str) -> dict[str, Any]:
        """Get detailed component information by LCSC part number (e.g., C12345)."""
        result: dict[str, Any] = {
            "success": False,
            "lcsc_code": lcsc_code,
            "detail": None,
        }

        payload = {"productCode": lcsc_code}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    cls.DETAIL_URL,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status != 200:
                        result["error"] = f"HTTP {resp.status}"
                        return result

                    data = await resp.json()
                    if data.get("code") == 200 and data.get("result"):
                        result["success"] = True
                        result["detail"] = cls._normalize_product(data["result"])
        except aiohttp.ClientError as e:
            logger.warning(f"LCSC detail network error: {e}")
            result["error"] = f"Network error: {str(e)}"
        except Exception as e:
            logger.warning(f"LCSC detail error: {e}")
            result["error"] = str(e)

        return result

    @classmethod
    async def search_by_part_number(cls, part_number: str) -> dict[str, Any]:
        """Search by manufacturer part number."""
        return await cls.search(part_number)

    # ------------------------------------------------------------------
    # 가격 티어 조회
    # ------------------------------------------------------------------

    @classmethod
    async def get_pricing(cls, lcsc_code: str) -> dict[str, Any]:
        """
        LCSC 부품의 가격 티어를 조회한다.

        Returns
        -------
        dict  { lcsc_code, currency, tiers: [{ min_qty, price_usd, price_cny }], stock, source }
        """
        detail = await cls.get_detail(lcsc_code)
        if detail.get("success") and detail.get("detail"):
            d = detail["detail"]
            return {
                "lcsc_code": lcsc_code,
                "currency": "USD/CNY",
                "tiers": d.get("price_tiers", []),
                "stock": d.get("stock", 0),
                "source": "lcsc_api",
            }

        # API 미응답 시 모의 데이터 반환
        return cls._mock_pricing(lcsc_code)

    # ------------------------------------------------------------------
    # Graceful fallback – 모의 데이터
    # ------------------------------------------------------------------

    @classmethod
    async def search_with_fallback(cls, keyword: str, category: Optional[str] = None,
                                    page: int = 1, page_size: int = 20) -> dict[str, Any]:
        """API 실패 시 모의 데이터로 fallback 하는 검색."""
        result = await cls.search(keyword, page=page, page_size=page_size)
        if result.get("success"):
            return result
        # fallback
        return cls._mock_search(keyword)

    @classmethod
    async def get_detail_with_fallback(cls, lcsc_code: str) -> dict[str, Any]:
        """API 실패 시 모의 데이터로 fallback 하는 상세 조회."""
        result = await cls.get_detail(lcsc_code)
        if result.get("success"):
            return result
        return cls._mock_detail(lcsc_code)

    # ------------------------------------------------------------------
    # 정규화 헬퍼
    # ------------------------------------------------------------------

    @classmethod
    def _normalize_product(cls, item: dict) -> dict[str, Any]:
        """Normalize LCSC product data to a common format."""
        # 가격 티어 추출
        prices = []
        for price_entry in item.get("productPriceList", []):
            prices.append({
                "quantity": price_entry.get("ladder", 0),
                "price_usd": price_entry.get("productPrice", 0),
                "price_cny": price_entry.get("discountPrice", 0),
            })

        return {
            "lcsc_code": item.get("productCode", ""),
            "part_number": item.get("productModel", ""),
            "manufacturer": item.get("brandNameEn", item.get("brandNameCn", "")),
            "description": item.get("productIntroEn", item.get("productIntroCn", "")),
            "package": item.get("encapStandard", ""),
            "category": item.get("catalogName", ""),
            "stock": item.get("stockNumber", 0),
            "price_tiers": prices,
            "min_qty": item.get("minPacketNumber", 1),
            "datasheet_url": item.get("pdfUrl", ""),
            "image_url": item.get("productImageUrl", ""),
            "product_url": f"https://www.lcsc.com/product-detail/{item.get('productCode', '')}.html",
        }

    # ------------------------------------------------------------------
    # Mock 데이터 (API 미응답 시 fallback)
    # ------------------------------------------------------------------

    @classmethod
    def _mock_search(cls, keyword: str) -> dict[str, Any]:
        """API 미응답 시 반환할 모의 검색 결과."""
        return {
            "success": True,
            "keyword": keyword,
            "results": [
                {
                    "lcsc_code": "C2040",
                    "part_number": "0603WAF1001T5E",
                    "manufacturer": "UNI-ROYAL",
                    "description": f"1kOhm +/-1% 0603 (검색어: {keyword})",
                    "package": "0603",
                    "category": "Resistors",
                    "stock": 50000,
                    "price_tiers": [{"quantity": 1, "price_usd": 0.002, "price_cny": 0.01}],
                    "min_qty": 1,
                    "datasheet_url": "",
                    "image_url": "",
                    "product_url": "https://www.lcsc.com/product-detail/C2040.html",
                },
            ],
            "total": 1,
            "source": "mock",
            "note": "LCSC API가 응답하지 않아 모의 데이터를 반환합니다.",
        }

    @classmethod
    def _mock_detail(cls, lcsc_code: str) -> dict[str, Any]:
        """API 미응답 시 반환할 모의 부품 상세."""
        return {
            "success": True,
            "lcsc_code": lcsc_code,
            "detail": {
                "lcsc_code": lcsc_code,
                "part_number": f"MOCK-{lcsc_code}",
                "manufacturer": "Unknown",
                "description": f"모의 데이터 - LCSC 코드 {lcsc_code}",
                "package": "",
                "category": "",
                "stock": 0,
                "price_tiers": [],
                "min_qty": 1,
                "datasheet_url": "",
                "image_url": "",
                "product_url": f"https://www.lcsc.com/product-detail/{lcsc_code}.html",
            },
            "source": "mock",
            "note": "LCSC API가 응답하지 않아 모의 데이터를 반환합니다.",
        }

    @classmethod
    def _mock_pricing(cls, lcsc_code: str) -> dict[str, Any]:
        """API 미응답 시 반환할 모의 가격 정보."""
        return {
            "lcsc_code": lcsc_code,
            "currency": "USD/CNY",
            "tiers": [
                {"quantity": 1, "price_usd": 0.10, "price_cny": 0.70},
                {"quantity": 10, "price_usd": 0.08, "price_cny": 0.56},
                {"quantity": 100, "price_usd": 0.05, "price_cny": 0.35},
            ],
            "stock": 0,
            "source": "mock",
            "note": "LCSC API가 응답하지 않아 모의 가격 데이터를 반환합니다.",
        }


# ---------------------------------------------------------------------------
# 모듈 수준 편의 함수
# ---------------------------------------------------------------------------

async def search_lcsc(query: str, category: Optional[str] = None) -> dict[str, Any]:
    """부품 검색 편의 함수 (fallback 포함)."""
    return await LCSCService.search_with_fallback(query, category=category)


async def get_lcsc_component(lcsc_code: str) -> dict[str, Any]:
    """부품 상세 조회 편의 함수 (fallback 포함)."""
    return await LCSCService.get_detail_with_fallback(lcsc_code)


async def get_lcsc_pricing(lcsc_code: str) -> dict[str, Any]:
    """가격 티어 조회 편의 함수."""
    return await LCSCService.get_pricing(lcsc_code)
