# CloudScale Analytics Platform - API Documentation v2.8.4

**Last Updated:** January 15, 2025  
**Base URL:** `https://api.cloudscale-analytics.com/v2`  
**API Version:** 2.8.4  
**Authentication:** OAuth 2.0, JWT, API Key

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Data Ingestion](#data-ingestion)
4. [Query Engine](#query-engine)
5. [Machine Learning](#machine-learning)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Error Handling](#error-handling)
8. [Webhooks](#webhooks)

---

## Authentication

### OAuth 2.0 Flow

CloudScale supports the OAuth 2.0 Client Credentials flow for server-to-server authentication.

**Token Endpoint:** `POST /oauth/token`

**Request:**
```json
{
  "grant_type": "client_credentials",
  "client_id": "your_client_id_32_chars_long",
  "client_secret": "your_client_secret_64_chars",
  "scope": "data:read data:write analytics:query ml:train"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "data:read data:write analytics:query ml:train"
}
```

**Token Usage:**
Include the access token in the Authorization header:
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Key Authentication

For simpler integrations, use API keys:
```
X-API-Key: csk_live_a3f7c8e9d2b1f4a6c5e8d7b9a1f3c5e7
```

**Security Note:** API keys grant full access to your account. Rotate keys every 90 days and use separate keys for development/production.

---

## Rate Limiting

### Limits by Tier

| Tier | Requests/min | Requests/hour | Ingestion Rate | Concurrent Queries |
|------|--------------|---------------|----------------|--------------------|
| Free | 100 | 5,000 | 100 events/s | 5 |
| Tier 1 | 500 | 25,000 | 5,000 events/s | 50 |
| Tier 2 | 2,000 | 100,000 | 50,000 events/s | 200 |
| Tier 3 | 10,000 | 500,000 | 500,000 events/s | 1,000 |
| Enterprise | Custom | Custom | Unlimited | Custom |

### Rate Limit Headers

Every API response includes rate limit information:
```
X-RateLimit-Limit: 2000
X-RateLimit-Remaining: 1847
X-RateLimit-Reset: 1705334400
X-RateLimit-Window: 60
```

**HTTP 429 Response (Rate Limit Exceeded):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 42 seconds.",
    "retry_after": 42,
    "limit": 2000,
    "window": "1 minute"
  }
}
```

---

## Data Ingestion

### Batch Event Ingestion

**Endpoint:** `POST /v2/events/batch`

**Description:** Ingest multiple events in a single request. Maximum batch size: 10,000 events or 10 MB payload.

**Request:**
```json
{
  "dataset_id": "ds_8a7f3c2e1b5d4f9a",
  "events": [
    {
      "event_id": "evt_1a2b3c4d5e6f7g8h",
      "timestamp": "2025-01-15T14:32:45.123Z",
      "event_type": "user.signup",
      "user_id": "usr_9f8e7d6c5b4a3f2e",
      "properties": {
        "email": "user@example.com",
        "plan": "premium",
        "source": "organic",
        "device": "mobile",
        "country": "FR"
      },
      "metrics": {
        "signup_duration_ms": 2847,
        "form_fields_filled": 8
      }
    },
    {
      "event_id": "evt_2b3c4d5e6f7g8h9i",
      "timestamp": "2025-01-15T14:33:12.456Z",
      "event_type": "purchase.completed",
      "user_id": "usr_9f8e7d6c5b4a3f2e",
      "properties": {
        "product_id": "prod_nc_x9000",
        "product_name": "NeuroChip X9000",
        "quantity": 2,
        "currency": "EUR",
        "payment_method": "credit_card"
      },
      "metrics": {
        "amount": 8599.98,
        "discount": 429.99,
        "tax": 1719.99,
        "total": 9889.98
      }
    }
  ],
  "options": {
    "deduplicate": true,
    "validate_schema": true,
    "async_processing": false
  }
}
```

**Response (202 Accepted):**
```json
{
  "request_id": "req_7g6f5e4d3c2b1a9f",
  "status": "processing",
  "events_received": 2,
  "events_accepted": 2,
  "events_rejected": 0,
  "processing_time_ms": 47,
  "estimated_ingestion_time_ms": 150
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Schema validation failed for 1 event(s)",
    "details": [
      {
        "event_id": "evt_1a2b3c4d5e6f7g8h",
        "field": "properties.email",
        "error": "Invalid email format"
      }
    ]
  }
}
```

### Streaming Ingestion

**Endpoint:** `POST /v2/events/stream`

**Description:** Real-time event streaming using Server-Sent Events (SSE) or WebSocket.

**WebSocket Connection:**
```javascript
const ws = new WebSocket('wss://api.cloudscale-analytics.com/v2/events/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'authenticate',
    api_key: 'csk_live_a3f7c8e9d2b1f4a6c5e8d7b9a1f3c5e7'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'ack') {
    console.log('Event acknowledged:', message.event_id);
  }
};

// Send events
ws.send(JSON.stringify({
  action: 'ingest',
  event: {
    event_id: 'evt_3c4d5e6f7g8h9i0j',
    timestamp: new Date().toISOString(),
    event_type: 'pageview',
    properties: { page: '/products', referrer: 'google.com' }
  }
}));
```

**Acknowledgment Message:**
```json
{
  "type": "ack",
  "event_id": "evt_3c4d5e6f7g8h9i0j",
  "ingested_at": "2025-01-15T14:35:01.789Z",
  "latency_ms": 23
}
```

---

## Query Engine

### SQL Query API

**Endpoint:** `POST /v2/query/sql`

**Description:** Execute SQL queries on your datasets. Supports standard SQL with extensions for time-series analysis.

**Request:**
```json
{
  "query": "SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) as event_count, AVG(metrics.amount) as avg_amount FROM events WHERE event_type = 'purchase.completed' AND timestamp >= NOW() - INTERVAL '7 days' GROUP BY hour ORDER BY hour DESC LIMIT 168",
  "parameters": {},
  "options": {
    "timeout_ms": 30000,
    "max_rows": 10000,
    "format": "json"
  }
}
```

**Response:**
```json
{
  "query_id": "qry_4d5e6f7g8h9i0j1k",
  "status": "completed",
  "rows_returned": 168,
  "rows_scanned": 1247893,
  "bytes_scanned": 8947263,
  "execution_time_ms": 847,
  "cached": false,
  "columns": [
    {"name": "hour", "type": "timestamp"},
    {"name": "event_count", "type": "bigint"},
    {"name": "avg_amount", "type": "decimal"}
  ],
  "rows": [
    {
      "hour": "2025-01-15T14:00:00Z",
      "event_count": 247,
      "avg_amount": 4532.18
    },
    {
      "hour": "2025-01-15T13:00:00Z",
      "event_count": 312,
      "avg_amount": 3894.67
    }
  ]
}
```

### Aggregation API

**Endpoint:** `POST /v2/query/aggregate`

**Description:** Pre-built aggregation functions optimized for common analytics use cases.

**Request:**
```json
{
  "dataset_id": "ds_8a7f3c2e1b5d4f9a",
  "metric": "revenue",
  "aggregation": "sum",
  "filters": [
    {"field": "event_type", "operator": "eq", "value": "purchase.completed"},
    {"field": "properties.country", "operator": "in", "value": ["FR", "DE", "GB"]}
  ],
  "group_by": ["properties.country", "properties.payment_method"],
  "time_range": {
    "start": "2025-01-01T00:00:00Z",
    "end": "2025-01-15T23:59:59Z"
  },
  "time_granularity": "day"
}
```

**Response:**
```json
{
  "query_id": "qry_5e6f7g8h9i0j1k2l",
  "metric": "revenue",
  "aggregation": "sum",
  "total_value": 2847932.48,
  "groups": [
    {
      "dimensions": {
        "country": "FR",
        "payment_method": "credit_card"
      },
      "value": 1432847.92,
      "count": 3247,
      "time_series": [
        {"timestamp": "2025-01-01", "value": 94829.34},
        {"timestamp": "2025-01-02", "value": 102847.18}
      ]
    }
  ]
}
```

---

## Machine Learning

### Anomaly Detection

**Endpoint:** `POST /v2/ml/anomaly-detection`

**Description:** Detect anomalies in time-series data using Isolation Forest or LSTM Autoencoder.

**Request:**
```json
{
  "dataset_id": "ds_8a7f3c2e1b5d4f9a",
  "metric": "metrics.response_time_ms",
  "algorithm": "isolation_forest",
  "parameters": {
    "contamination": 0.05,
    "n_estimators": 100,
    "max_samples": 256
  },
  "time_range": {
    "start": "2025-01-08T00:00:00Z",
    "end": "2025-01-15T23:59:59Z"
  },
  "granularity": "5m",
  "filters": [
    {"field": "properties.endpoint", "operator": "eq", "value": "/api/checkout"}
  ]
}
```

**Response:**
```json
{
  "job_id": "ml_job_6f7g8h9i0j1k2l3m",
  "status": "completed",
  "algorithm": "isolation_forest",
  "data_points_analyzed": 2016,
  "anomalies_detected": 47,
  "anomaly_rate": 0.0233,
  "execution_time_ms": 3847,
  "results": [
    {
      "timestamp": "2025-01-12T03:15:00Z",
      "value": 8473.2,
      "anomaly_score": 0.89,
      "is_anomaly": true,
      "expected_range": [120.5, 450.3],
      "deviation_percentage": 1780.4
    },
    {
      "timestamp": "2025-01-14T19:45:00Z",
      "value": 12.8,
      "anomaly_score": 0.92,
      "is_anomaly": true,
      "expected_range": [120.5, 450.3],
      "deviation_percentage": -89.4
    }
  ],
  "statistics": {
    "mean": 247.8,
    "median": 234.5,
    "std_dev": 89.4,
    "min": 12.8,
    "max": 8473.2
  }
}
```

### Time-Series Forecasting

**Endpoint:** `POST /v2/ml/forecast`

**Description:** Predict future values using Prophet, ARIMA, or Transformer models.

**Request:**
```json
{
  "dataset_id": "ds_8a7f3c2e1b5d4f9a",
  "metric": "revenue",
  "algorithm": "prophet",
  "historical_data": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2025-01-15T23:59:59Z",
    "granularity": "day"
  },
  "forecast_horizon": {
    "periods": 30,
    "granularity": "day"
  },
  "parameters": {
    "seasonality_mode": "multiplicative",
    "yearly_seasonality": true,
    "weekly_seasonality": true,
    "changepoint_prior_scale": 0.05
  },
  "confidence_interval": 0.95
}
```

**Response:**
```json
{
  "job_id": "ml_job_7g8h9i0j1k2l3m4n",
  "status": "completed",
  "algorithm": "prophet",
  "historical_points": 380,
  "forecast_points": 30,
  "model_performance": {
    "mape": 4.73,
    "mae": 12847.32,
    "rmse": 18392.45,
    "r_squared": 0.94
  },
  "forecast": [
    {
      "timestamp": "2025-01-16",
      "predicted_value": 94832.47,
      "lower_bound": 82743.21,
      "upper_bound": 106921.73,
      "confidence": 0.95
    },
    {
      "timestamp": "2025-01-17",
      "predicted_value": 103482.18,
      "lower_bound": 91237.84,
      "upper_bound": 115726.52,
      "confidence": 0.95
    }
  ],
  "seasonality_components": {
    "yearly": "strong_positive",
    "weekly": "moderate_positive",
    "daily": "weak"
  },
  "execution_time_ms": 12384
}
```

---

## Monitoring & Alerts

### Create Alert Rule

**Endpoint:** `POST /v2/alerts/rules`

**Request:**
```json
{
  "name": "High Error Rate Alert",
  "description": "Trigger when error rate exceeds 5% for 5 consecutive minutes",
  "dataset_id": "ds_8a7f3c2e1b5d4f9a",
  "condition": {
    "metric": "error_rate",
    "aggregation": "avg",
    "operator": "gt",
    "threshold": 0.05,
    "window": "5m",
    "consecutive_periods": 5
  },
  "filters": [
    {"field": "properties.environment", "operator": "eq", "value": "production"}
  ],
  "channels": [
    {
      "type": "email",
      "recipients": ["oncall@example.com", "devops@example.com"],
      "priority": "high"
    },
    {
      "type": "webhook",
      "url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    },
    {
      "type": "pagerduty",
      "service_key": "your_pagerduty_service_key",
      "severity": "critical"
    }
  ],
  "enabled": true,
  "throttle_minutes": 30
}
```

**Response:**
```json
{
  "alert_id": "alert_8h9i0j1k2l3m4n5o",
  "name": "High Error Rate Alert",
  "status": "active",
  "created_at": "2025-01-15T14:45:32Z",
  "next_evaluation": "2025-01-15T14:50:00Z"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request payload is malformed",
    "details": [
      {
        "field": "events[0].timestamp",
        "error": "Invalid ISO 8601 timestamp format"
      }
    ],
    "request_id": "req_9i0j1k2l3m4n5o6p",
    "timestamp": "2025-01-15T14:50:12Z",
    "documentation_url": "https://docs.cloudscale-analytics.com/errors/INVALID_REQUEST"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description | Retry? |
|------|-------------|-------------|--------|
| AUTHENTICATION_FAILED | 401 | Invalid or expired credentials | No |
| INSUFFICIENT_PERMISSIONS | 403 | API key lacks required scope | No |
| RESOURCE_NOT_FOUND | 404 | Dataset or query not found | No |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Yes (after delay) |
| VALIDATION_ERROR | 400 | Request validation failed | No |
| QUERY_TIMEOUT | 504 | Query exceeded timeout | Yes |
| INTERNAL_SERVER_ERROR | 500 | Unexpected server error | Yes (with backoff) |
| SERVICE_UNAVAILABLE | 503 | Maintenance or overload | Yes (with backoff) |

### Retry Strategy Recommendation

```python
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Exponential backoff with jitter
retry_strategy = Retry(
    total=5,
    backoff_factor=2,  # 2s, 4s, 8s, 16s, 32s
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
    raise_on_status=False
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)

response = session.post(
    "https://api.cloudscale-analytics.com/v2/events/batch",
    headers={"X-API-Key": "your_api_key"},
    json=payload,
    timeout=30
)
```

---

## Webhooks

### Configure Webhook

**Endpoint:** `POST /v2/webhooks`

**Request:**
```json
{
  "url": "https://your-domain.com/webhooks/cloudscale",
  "events": [
    "data.ingestion.completed",
    "query.completed",
    "alert.triggered",
    "ml.job.completed"
  ],
  "secret": "whsec_8h9i0j1k2l3m4n5o6p7q8r9s0t",
  "enabled": true
}
```

**Webhook Payload Example (alert.triggered):**
```json
{
  "event_id": "evt_webhook_9j0k1l2m3n4o5p6q",
  "event_type": "alert.triggered",
  "timestamp": "2025-01-15T15:03:47Z",
  "data": {
    "alert_id": "alert_8h9i0j1k2l3m4n5o",
    "alert_name": "High Error Rate Alert",
    "triggered_at": "2025-01-15T15:03:47Z",
    "condition_met": {
      "metric": "error_rate",
      "current_value": 0.0847,
      "threshold": 0.05,
      "consecutive_periods": 5
    },
    "dataset_id": "ds_8a7f3c2e1b5d4f9a"
  },
  "signature": "sha256=a8f7c9e2d1b4f6a8c5e7d9b1a3f5c7e9..."
}
```

**Signature Verification (Python):**
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    computed_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(
        f"sha256={computed_signature}",
        signature
    )
```

---

## SDK Examples

### Python SDK

```python
from cloudscale import CloudScaleClient

client = CloudScaleClient(
    api_key="csk_live_a3f7c8e9d2b1f4a6c5e8d7b9a1f3c5e7",
    timeout=30
)

# Ingest events
events = [
    {
        "event_type": "pageview",
        "timestamp": "2025-01-15T15:10:00Z",
        "properties": {"page": "/products"}
    }
]

response = client.events.ingest_batch(
    dataset_id="ds_8a7f3c2e1b5d4f9a",
    events=events
)

print(f"Ingested {response.events_accepted} events")

# Run SQL query
result = client.query.sql(
    "SELECT COUNT(*) FROM events WHERE event_type = 'pageview'"
)

print(f"Total pageviews: {result.rows[0][0]}")
```

### JavaScript SDK

```javascript
const CloudScale = require('@cloudscale/analytics');

const client = new CloudScale({
  apiKey: 'csk_live_a3f7c8e9d2b1f4a6c5e8d7b9a1f3c5e7',
  timeout: 30000
});

// Ingest events
await client.events.ingestBatch({
  datasetId: 'ds_8a7f3c2e1b5d4f9a',
  events: [
    {
      eventType: 'pageview',
      timestamp: new Date().toISOString(),
      properties: { page: '/products' }
    }
  ]
});

// Run aggregation query
const result = await client.query.aggregate({
  datasetId: 'ds_8a7f3c2e1b5d4f9a',
  metric: 'revenue',
  aggregation: 'sum',
  timeRange: {
    start: '2025-01-01',
    end: '2025-01-15'
  }
});

console.log(`Total revenue: €${result.total_value}`);
```

---

## Support & Resources

- **Documentation:** https://docs.cloudscale-analytics.com
- **API Status:** https://status.cloudscale-analytics.com
- **Support Email:** support@cloudscale-analytics.com
- **Developer Community:** https://community.cloudscale-analytics.com
- **GitHub:** https://github.com/cloudscale-analytics
- **Changelog:** https://docs.cloudscale-analytics.com/changelog