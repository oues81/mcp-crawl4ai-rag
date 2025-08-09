# Runtime guard to force Crawl4AI to respect BrowserConfig.browser_type for Firefox
# and fail fast if Chromium is launched instead (persistent via repo code).
from __future__ import annotations
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from crawl4ai import browser_manager as _bm  # type: ignore
except Exception as e:  # pragma: no cover
    logger.warning("crawl4ai not available at import: %s", e)
    _bm = None

if _bm is not None and hasattr(_bm, "BrowserManager"):
    from playwright.async_api import async_playwright

    _Orig_get_browser_args = getattr(_bm.BrowserManager, "_get_browser_args", None)
    _Orig_start = getattr(_bm.BrowserManager, "start", None)

    async def _guarded_get_browser_args(self):  # type: ignore
        # Force internal browser_type to match config.browser_type (no fallback)
        if getattr(self, "browser_config", None) is not None:
            req_type = getattr(self.browser_config, "browser_type", None)
            if req_type:
                self.browser_type = req_type
        # Delegate if available
        if callable(_Orig_get_browser_args):
            return await _Orig_get_browser_args(self)  # type: ignore
        return []

    async def _guarded_start(self):  # type: ignore
        cfg = getattr(self, "browser_config", None)
        # If firefox requested and not managed/CDP, force native firefox launch here
        if cfg and getattr(cfg, "browser_type", "chromium") == "firefox" and not getattr(cfg, "use_managed_browser", False) and not getattr(cfg, "cdp_url", None):
            # Start Playwright if needed
            if getattr(self, "playwright", None) is None:
                self.playwright = await async_playwright().start()
            # Minimal args honoring headless and extra_args when possible
            launch_kwargs = {
                "headless": bool(getattr(cfg, "headless", True)),
            }
            extra_args = getattr(cfg, "extra_args", None)
            if extra_args:
                launch_kwargs["args"] = list(extra_args)

            # Launch native firefox
            self.browser = await self.playwright.firefox.launch(**launch_kwargs)
            self.managed_browser = None
            # Prepare a default context to mirror Crawl4AI expectations
            self.default_context = await self.browser.new_context()
            return self

        # Else: enforce CDP only for chromium
        if cfg and getattr(cfg, "cdp_url", None) and getattr(cfg, "browser_type", "chromium") != "chromium":
            raise RuntimeError("cdp_url provided for non-chromium browser. This would force Chromium.")

        # Fallback to original start
        if callable(_Orig_start):
            return await _Orig_start(self)  # type: ignore
        raise RuntimeError("Crawl4AI BrowserManager.start not available to patch")

    # Apply patches
    if callable(_Orig_get_browser_args):
        _bm.BrowserManager._get_browser_args = _guarded_get_browser_args  # type: ignore
        logger.info("Applied Crawl4AI BrowserManager _get_browser_args guard for firefox")
    if callable(_Orig_start):
        _bm.BrowserManager.start = _guarded_start  # type: ignore
        logger.info("Applied Crawl4AI BrowserManager start() override for firefox path")
