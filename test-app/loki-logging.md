# Loki Log Collection Guide

This document explains how Loki automatically collects logs from your applications and how to use structured logging for better log analysis.

## How Loki Works

Loki automatically collects logs from ALL pods in the Kubernetes cluster through:
1. **Promtail** (if installed) - DaemonSet that tails pod logs
2. **Grafana Agent** (alternative) - Unified agent for metrics and logs
3. **Log labels** - Kubernetes labels are automatically added (namespace, pod, container, etc.)

**No configuration needed in your application!** Loki reads logs directly from stdout/stderr.

## Basic Log Queries

### View All Logs from Your Application
```logql
{namespace="monitoring", app="myapp"}
```

### Filter by Log Level
```logql
{namespace="monitoring", app="myapp"} |= "error"
{namespace="monitoring", app="myapp"} |= "ERROR"
```

### Filter by Time Range
Use Grafana's time picker, or:
```logql
{namespace="monitoring", app="myapp"} | __timestamp__ > ago(1h)
```

### Count Errors
```logql
sum(count_over_time({namespace="monitoring", app="myapp"} |= "error" [5m]))
```

## 🎯 Structured Logging (Recommended)

### Why Structured Logging?

**Plain text logs:**
```
2024-01-15 10:30:45 ERROR Failed to process order 12345
```

**Structured JSON logs:**
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "error",
  "message": "Failed to process order",
  "order_id": "12345",
  "user_id": "user-789",
  "error_type": "PaymentTimeout"
}
```

Benefits:
- Better filtering and searching
- Automatic label extraction
- Faster queries
- Better correlation with metrics

## 📝 Example: Structured Logging in Python

See `app.py` for a complete example using `python-json-logger`.

Key points:
```python
from pythonjsonlogger import jsonlogger

# Configure JSON formatter
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s',
    rename_fields={'asctime': 'timestamp', 'levelname': 'level'}
)

# Log with extra fields
logger.info(
    "User logged in",
    extra={
        'user_id': '12345',
        'ip_address': '192.168.1.1',
        'session_id': 'abc-123'
    }
)
```

Output:
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "info",
  "message": "User logged in",
  "user_id": "12345",
  "ip_address": "192.168.1.1",
  "session_id": "abc-123"
}
```

## 🔎 Advanced LogQL Queries

### Parse JSON Logs
```logql
{namespace="monitoring", app="myapp"} 
  | json
  | level="error"
```

### Extract and Filter by Fields
```logql
{namespace="monitoring", app="myapp"} 
  | json
  | user_id="12345"
  | line_format "{{.timestamp}} {{.message}}"
```

### Aggregate Logs
```logql
# Count logs by level
sum by (level) (count_over_time({namespace="monitoring", app="myapp"} | json [5m]))

# Count errors by error_type
sum by (error_type) (count_over_time({namespace="monitoring", app="myapp"} | json | level="error" [5m]))
```

### Calculate Rates
```logql
# Error rate per second
rate({namespace="monitoring", app="myapp"} |= "error" [5m])

# Request rate per endpoint
sum by (endpoint) (rate({namespace="monitoring", app="myapp"} | json | __line__ =~ "HTTP request completed" [5m]))
```

### Pattern Matching
```logql
# Match regex pattern
{namespace="monitoring", app="myapp"} |~ "order.*failed"

# Match multiple patterns
{namespace="monitoring", app="myapp"} |~ "error|exception|failed"
```

## Language-Specific Libraries

### Python
```bash
pip install python-json-logger
```

```python
from pythonjsonlogger import jsonlogger
import logging

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)

logger.info("Message", extra={'key': 'value'})
```

## Viewing Logs in Grafana

### Method 1: Explore View
1. Open Grafana: https://monitoring.rc.ds.wt.de
2. Click "Explore" (compass icon)
3. Select "Loki" datasource
4. Enter LogQL query: `{namespace="monitoring", app="myapp"}`
5. Click "Run query"

### Method 2: Dashboard Panel
Add a logs panel to your dashboard:
```json
{
  "type": "logs",
  "title": "Application Logs",
  "targets": [
    {
      "expr": "{namespace=\"monitoring\", app=\"myapp\"} | json"
    }
  ]
}
```

### Method 3: Link from Metrics Dashboard
Create a data link in your Grafana dashboard to jump from metrics to logs:
```json
{
  "title": "View Logs",
  "url": "/explore?left={\"queries\":[{\"expr\":\"{namespace=\\\"monitoring\\\",app=\\\"myapp\\\"}\"}]}"
}
```

## ⏱Log Retention

Current retention: **7 days** (168 hours)

This is configured in `/loki-values/values-simple.yaml`:
```yaml
limits_config:
  retention_period: 168h  # 7 days

compactor:
  retention_enabled: true
```

To change retention:
1. Edit `loki-values/values-simple.yaml`
2. Update `retention_period` value
3. Run: `helm upgrade loki grafana/loki -n monitoring --values ./loki-values/values-simple.yaml`
