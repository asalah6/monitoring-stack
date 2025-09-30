# Test Application - Monitoring Integration Guide

This folder contains complete examples showing developers how to integrate their applications with the monitoring stack (Prometheus, Grafana, Loki).

## Contents

1. **deployment.yaml** - Example FastAPI application with metrics endpoint
2. **service.yaml** - Kubernetes Service exposing the application
3. **servicemonitor.yaml** - Prometheus ServiceMonitor for automatic metrics scraping
4. **grafana-dashboard-configmap.yaml** - Grafana dashboard as ConfigMap for auto-discovery
5. **loki-logging.yaml** - Example showing log collection with Loki

## Quick Start

**Try the example application in 2 minutes:**

```bash
cd test-app/
./deploy.sh
```

For your own application:

1. **Add metrics to your application** using Prometheus client library
2. **Deploy your application** with proper labels
3. **Create a ServiceMonitor** to enable Prometheus scraping
4. **Create a dashboard ConfigMap** for Grafana auto-discovery
5. **Enable structured logging** for better Loki integration

### Step 2: Deploy Your Application

```bash
# Deploy your application
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### Step 3: Enable Prometheus Scraping

```bash
# Create ServiceMonitor to tell Prometheus to scrape your metrics
kubectl apply -f servicemonitor.yaml
```

**Verify in Prometheus UI:**
- Go to Prometheus: http://prometheus-prometheus.monitoring.svc.cluster.local:9090
- Status → Targets → Look for your application
- Graph → Query: `myapp_http_requests_total`

### Step 4: Add Grafana Dashboard

```bash
# Deploy dashboard ConfigMap with the correct label
kubectl apply -f grafana-dashboard-configmap.yaml
```

**Grafana will automatically discover** dashboards with this label:
```yaml
labels:
  grafana_dashboard: "1"
```

Dashboard appears in Grafana under "Dashboards" within ~1 minute.

### Step 5: Enable Loki Log Collection

**Option A: Automatic (No Changes Needed)**
- Loki automatically collects all pod logs via Promtail/Grafana Agent
- View logs in Grafana → Explore → Loki datasource
- Query: `{namespace="your-namespace", app="your-app"}`

**Option B: Structured Logging (Recommended)**
- Output logs in JSON format
- See `loki-logging.yaml` for examples
- Benefits: Better filtering, label extraction, faster queries


## Metric Naming Convention

**IMPORTANT:** All metrics MUST follow this format:
```
<appname>_<metric_name>
```

### ✅ Good Examples:
- `myapp_http_requests_total`
- `myapp_database_connections_active`
- `myapp_cache_hit_rate`
- `userservice_login_attempts_total`
- `orderapi_payment_processing_duration_seconds`

### ❌ Bad Examples:
- `http_requests_total` (missing app prefix)
- `myapp.requests` (use underscore, not dot)
- `MyApp_Requests` (use lowercase)

### Metric Types:
1. **Counter** (only increases): `_total` suffix
   - Example: `myapp_requests_total`, `myapp_errors_total`
2. **Gauge** (can go up/down): no suffix
   - Example: `myapp_memory_usage_bytes`, `myapp_queue_size`
3. **Histogram** (distributions): `_seconds`, `_bytes` suffix
   - Example: `myapp_request_duration_seconds`, `myapp_response_size_bytes`
4. **Summary** (quantiles): `_seconds`, `_bytes` suffix
   - Example: `myapp_api_latency_seconds`

## Language-Specific Libraries

### Python (FastAPI/Flask)
```bash
pip install prometheus-client
```
See `deployment.yaml` for complete FastAPI example.

## Verification Checklist

After deploying your application:

- [ ] **Metrics endpoint** responds: `curl http://your-app:port/metrics`
- [ ] **ServiceMonitor** created: `kubectl get servicemonitor -n your-namespace`
- [ ] **Prometheus target** is UP: Check Prometheus UI → Status → Targets
- [ ] **Metrics visible** in Prometheus: Query `your_app_*` metrics
- [ ] **Grafana dashboard** appears: Check Grafana → Dashboards
- [ ] **Logs visible** in Loki: Grafana → Explore → Loki → `{app="your-app"}`

## Best Practices

1. **Use consistent metric prefixes** - All your app's metrics start with `appname_`
2. **Add meaningful labels** - `{method="GET", endpoint="/api/users", status="200"}`
3. **Keep cardinality low** - Don't use high-cardinality labels (user IDs, timestamps)
4. **Document your metrics** - Add HELP comments in the metrics endpoint
5. **Use structured logging** - JSON format with consistent fields
6. **Set retention policies** - Default is 7 days for Loki, configure if needed
7. **Create alerts** - Define PrometheusRule for critical metrics
8. **Test locally** - Use `docker-compose` to test metrics before K8s deployment
