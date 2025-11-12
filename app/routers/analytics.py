"""Analytics and monitoring endpoints"""

from fastapi import APIRouter, HTTPException, status, Response
from typing import Optional

from app.auth import RequireAPIKey
from app.config import settings
from app.utils.monitoring import get_metrics_store, export_prometheus_metrics
from app.utils.cache import get_cache_client

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/stats")
async def get_stats(
    since_minutes: Optional[int] = None,
    api_key: RequireAPIKey = None,
):
    """
    Get service statistics and metrics.

    Returns request counts, error rates, response times, and endpoint breakdowns.
    Optionally filter to last N minutes.
    """
    try:
        metrics_store = get_metrics_store(settings.metrics_retention_hours)
        stats = metrics_store.get_stats(since_minutes=since_minutes)

        return {
            "status": "success",
            "metrics": stats,
            "period": f"last {since_minutes} minutes" if since_minutes else "all time"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stats: {str(e)}"
        )


@router.get("/errors")
async def get_recent_errors(
    limit: int = 10,
    api_key: RequireAPIKey = None,
):
    """
    Get recent errors.

    Returns the most recent errors with timestamps, endpoints, and error messages.
    """
    try:
        metrics_store = get_metrics_store(settings.metrics_retention_hours)
        errors = metrics_store.get_recent_errors(limit=limit)

        return {
            "status": "success",
            "errors": errors,
            "count": len(errors)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve errors: {str(e)}"
        )


@router.get("/alerts")
async def check_alerts(
    api_key: RequireAPIKey = None,
):
    """
    Check for active alerts.

    Monitors error rates and response times against configured thresholds.
    Returns any active alerts that require attention.
    """
    try:
        metrics_store = get_metrics_store(settings.metrics_retention_hours)
        alerts = metrics_store.check_alerts(
            error_threshold=settings.alert_error_rate_threshold,
            response_time_threshold=settings.alert_response_time_threshold
        )

        return {
            "status": "success" if not alerts else "warning",
            "alerts": alerts,
            "alert_count": len(alerts),
            "thresholds": {
                "error_rate": settings.alert_error_rate_threshold,
                "response_time": settings.alert_response_time_threshold
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check alerts: {str(e)}"
        )


@router.get("/cache")
async def get_cache_stats(
    api_key: RequireAPIKey = None,
):
    """
    Get cache statistics.

    Returns cache hit/miss rates, memory usage, and other cache metrics.
    """
    try:
        cache_client = get_cache_client(settings.redis_url, settings.cache_enabled)
        stats = cache_client.get_stats()

        return {
            "status": "success",
            "cache": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cache stats: {str(e)}"
        )


@router.delete("/cache")
async def clear_cache(
    prefix: Optional[str] = None,
    api_key: RequireAPIKey = None,
):
    """
    Clear cache entries.

    If prefix is provided, only clears entries with that prefix.
    Otherwise, clears all cache entries.

    **WARNING**: This will clear cached responses and may temporarily increase load.
    """
    try:
        cache_client = get_cache_client(settings.redis_url, settings.cache_enabled)

        if prefix:
            deleted = cache_client.clear_prefix(prefix)
            return {
                "status": "success",
                "message": f"Cleared cache entries with prefix: {prefix}",
                "deleted": deleted
            }
        else:
            success = cache_client.clear_all()
            return {
                "status": "success" if success else "error",
                "message": "Cleared all cache entries" if success else "Failed to clear cache"
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/health")
async def analytics_health():
    """
    Check analytics system health.

    Verifies that monitoring and caching systems are operational.
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }

    # Check monitoring
    try:
        metrics_store = get_metrics_store(settings.metrics_retention_hours)
        stats = metrics_store.get_stats(since_minutes=1)
        health_status["components"]["monitoring"] = {
            "status": "healthy" if settings.monitoring_enabled else "disabled",
            "recent_requests": stats["total_requests"]
        }
    except Exception as e:
        health_status["components"]["monitoring"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check cache
    try:
        cache_client = get_cache_client(settings.redis_url, settings.cache_enabled)
        cache_stats = cache_client.get_stats()
        health_status["components"]["cache"] = {
            "status": cache_stats.get("status", "unknown"),
            "enabled": cache_stats.get("enabled", False)
        }
    except Exception as e:
        health_status["components"]["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    return health_status
