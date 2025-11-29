"""Request monitoring and metrics collection"""

import logging
import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Prometheus metrics
REQUEST_COUNT = Counter("simpleton_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])

REQUEST_DURATION = Histogram(
    "simpleton_request_duration_seconds", "HTTP request duration in seconds", ["method", "endpoint"]
)

REQUEST_IN_PROGRESS = Gauge("simpleton_requests_in_progress", "Number of HTTP requests in progress")

ERROR_COUNT = Counter("simpleton_errors_total", "Total errors", ["endpoint", "error_type"])

CACHE_HITS = Counter("simpleton_cache_hits_total", "Total cache hits", ["cache_type"])

CACHE_MISSES = Counter("simpleton_cache_misses_total", "Total cache misses", ["cache_type"])

LLM_REQUESTS = Counter("simpleton_llm_requests_total", "Total LLM requests", ["model", "endpoint"])

LLM_TOKENS = Counter(
    "simpleton_llm_tokens_total",
    "Total LLM tokens processed",
    ["model", "token_type"],  # prompt or completion
)


class MetricsStore:
    """In-memory metrics store for analytics"""

    def __init__(self, retention_hours: int = 168):
        """
        Initialize metrics store

        Args:
            retention_hours: How long to keep metrics (default: 7 days)
        """
        self.retention_hours = retention_hours
        self.retention_delta = timedelta(hours=retention_hours)

        # Request metrics (rolling window)
        self.requests = deque(maxlen=10000)  # Last 10k requests
        self.errors = deque(maxlen=1000)  # Last 1k errors

        # Aggregated stats
        self.endpoint_stats = defaultdict(
            lambda: {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "errors": 0,
            }
        )

        # Current period counters
        self.current_minute_requests = 0
        self.current_minute_start = datetime.now()

        logger.info(f"Initialized metrics store with {retention_hours}h retention")

    def record_request(self, method: str, path: str, status_code: int, duration: float, error: str | None = None):
        """Record a request"""
        now = datetime.now()

        # Add to rolling window
        self.requests.append(
            {
                "timestamp": now,
                "method": method,
                "path": path,
                "status": status_code,
                "duration": duration,
                "error": error,
            }
        )

        # Update endpoint stats
        endpoint_key = f"{method} {path}"
        stats = self.endpoint_stats[endpoint_key]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min_time"] = min(stats["min_time"], duration)
        stats["max_time"] = max(stats["max_time"], duration)

        if status_code >= 400 or error:
            stats["errors"] += 1
            self.errors.append(
                {
                    "timestamp": now,
                    "method": method,
                    "path": path,
                    "status": status_code,
                    "error": error,
                }
            )

        # Update current minute counter
        if (now - self.current_minute_start).total_seconds() >= 60:
            self.current_minute_requests = 1
            self.current_minute_start = now
        else:
            self.current_minute_requests += 1

        # Cleanup old data
        self._cleanup_old_data()

    def _cleanup_old_data(self):
        """Remove data older than retention period"""
        cutoff = datetime.now() - self.retention_delta

        # Clean requests
        while self.requests and self.requests[0]["timestamp"] < cutoff:
            self.requests.popleft()

        # Clean errors
        while self.errors and self.errors[0]["timestamp"] < cutoff:
            self.errors.popleft()

    def get_stats(self, since_minutes: int | None = None) -> dict:
        """
        Get aggregated statistics

        Args:
            since_minutes: Only include data from last N minutes (None = all data)

        Returns:
            Statistics dictionary
        """
        if since_minutes:
            cutoff = datetime.now() - timedelta(minutes=since_minutes)
            recent_requests = [r for r in self.requests if r["timestamp"] >= cutoff]
            recent_errors = [e for e in self.errors if e["timestamp"] >= cutoff]
        else:
            recent_requests = list(self.requests)
            recent_errors = list(self.errors)

        total_requests = len(recent_requests)
        total_errors = len(recent_errors)

        # Calculate metrics
        avg_response_time = 0.0
        if recent_requests:
            avg_response_time = sum(r["duration"] for r in recent_requests) / total_requests

        error_rate = 0.0
        if total_requests > 0:
            error_rate = (total_errors / total_requests) * 100

        # Status code distribution
        status_dist = defaultdict(int)
        for req in recent_requests:
            status_class = f"{req['status'] // 100}xx"
            status_dist[status_class] += 1

        # Endpoint breakdown
        endpoint_breakdown = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats["count"] > 0:
                endpoint_breakdown[endpoint] = {
                    "requests": stats["count"],
                    "avg_time": round(stats["total_time"] / stats["count"], 3),
                    "min_time": round(stats["min_time"], 3),
                    "max_time": round(stats["max_time"], 3),
                    "errors": stats["errors"],
                    "error_rate": round((stats["errors"] / stats["count"]) * 100, 2),
                }

        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "requests_per_minute": self.current_minute_requests,
            "status_distribution": dict(status_dist),
            "endpoint_breakdown": endpoint_breakdown,
            "retention_hours": self.retention_hours,
        }

    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors"""
        errors_list = list(self.errors)[-limit:]
        return [
            {
                "timestamp": e["timestamp"].isoformat(),
                "method": e["method"],
                "path": e["path"],
                "status": e["status"],
                "error": e.get("error", "Unknown"),
            }
            for e in reversed(errors_list)  # Most recent first
        ]

    def check_alerts(self, error_threshold: float, response_time_threshold: float) -> list:
        """
        Check for alert conditions

        Args:
            error_threshold: Error rate threshold (0-1)
            response_time_threshold: Response time threshold in seconds

        Returns:
            List of active alerts
        """
        alerts = []
        stats = self.get_stats(since_minutes=5)  # Last 5 minutes

        # Check error rate
        if stats["total_requests"] > 10:  # Only alert if we have enough data
            error_rate = stats["error_rate"] / 100
            if error_rate > error_threshold:
                alerts.append(
                    {
                        "type": "high_error_rate",
                        "severity": "warning",
                        "message": f"Error rate is {stats['error_rate']:.1f}% (threshold: {error_threshold * 100:.1f}%)",
                        "value": stats["error_rate"],
                        "threshold": error_threshold * 100,
                    }
                )

        # Check response time
        if stats["avg_response_time"] > response_time_threshold:
            alerts.append(
                {
                    "type": "high_response_time",
                    "severity": "warning",
                    "message": f"Average response time is {stats['avg_response_time']:.2f}s (threshold: {response_time_threshold}s)",
                    "value": stats["avg_response_time"],
                    "threshold": response_time_threshold,
                }
            )

        return alerts


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor all requests"""

    def __init__(self, app, metrics_store: MetricsStore):
        super().__init__(app)
        self.metrics_store = metrics_store

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics"""
        # Skip metrics endpoint to avoid recursive tracking
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.time()
        error = None
        status_code = 500

        # Track in-progress requests
        REQUEST_IN_PROGRESS.inc()

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception as e:
            error = str(e)
            logger.error(f"Request error: {e}")
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Update Prometheus metrics
            REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()

            REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(duration)

            REQUEST_IN_PROGRESS.dec()

            if error or status_code >= 400:
                ERROR_COUNT.labels(
                    endpoint=request.url.path, error_type="http_error" if not error else "exception"
                ).inc()

            # Record in metrics store
            self.metrics_store.record_request(
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration=duration,
                error=error,
            )


# Global metrics store
_metrics_store: MetricsStore | None = None


def get_metrics_store(retention_hours: int = 168) -> MetricsStore:
    """Get or create metrics store instance"""
    global _metrics_store
    if _metrics_store is None:
        _metrics_store = MetricsStore(retention_hours)
    return _metrics_store


def export_prometheus_metrics() -> tuple[bytes, str]:
    """Export Prometheus metrics"""
    return generate_latest(), CONTENT_TYPE_LATEST
