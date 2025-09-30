# Test Application - Developer Onboarding

This directory contains a **complete reference implementation** showing how developers can integrate their applications with the monitoring stack (Prometheus, Grafana, Loki).

## 📁 Files Overview

| File | Purpose | Key Features |
|------|---------|--------------|
| **README.md** | Main developer guide | Quick start, metric naming convention, verification checklist |
| **app.py** | Python FastAPI reference app | 10+ metrics, JSON logging, complete implementation |
| **deployment.yaml** | Kubernetes Deployment | Annotations, health probes, resource limits |
| **service.yaml** | Kubernetes Service | HTTP + metrics ports |
| **servicemonitor.yaml** | Prometheus scraping config | **Critical**: `release: prometheus` label |
| **grafana-dashboard-configmap.yaml** | Auto-discovered dashboard | **Critical**: `grafana_dashboard: "1"` label |
| **loki-logging.md** | Loki integration guide | LogQL queries, structured logging |
| **requirements.txt** | Python dependencies | FastAPI, prometheus-client, json-logger |
| **deploy.sh** | Automated deployment | One-command deployment script |

## 🚀 Quick Start (2 Minutes)

**✨ No Docker image build required!** The test application runs using Python alpine image with code mounted from ConfigMap.

### Step 1: Deploy Everything

```bash
# Option 1: Use the automated script (recommended)
./deploy.sh

# Option 2: Manual deployment
kubectl apply -f app-configmap.yaml   # Application code
kubectl apply -f deployment.yaml       # Deployment
kubectl apply -f service.yaml          # Service
kubectl apply -f servicemonitor.yaml   # Prometheus scraping
kubectl apply -f grafana-dashboard-configmap.yaml  # Dashboard
```

**Note:** The init container will install Python dependencies on first start (takes ~1 minute).

### Step 2: Verify Integration

#### ✅ Check Metrics in Prometheus
```bash
# Port-forward to test locally
kubectl port-forward -n monitoring svc/myapp 8000:8000

# Curl the metrics endpoint
curl http://localhost:8000/metrics

# Open Prometheus UI: https://monitoring.rc.ds.wt.de
# Go to: Status → Targets → Look for "myapp"
# Should show: State = UP

# Query metrics:
myapp_http_requests_total
myapp_request_duration_seconds
myapp_active_connections
```

#### ✅ Check Dashboard in Grafana
```bash
# Open Grafana: https://monitoring.rc.ds.wt.de
# Login: admin / admin123
# Go to: Dashboards → "MyApp Metrics Dashboard"
# Should see: 8 panels with live data
```

#### ✅ Check Logs in Loki
```bash
# In Grafana: Explore → Select Loki data source
# Query: {namespace="monitoring", app="myapp"}
# Should see: JSON formatted logs with structured fields
```

## 🧹 Cleanup (After Testing)

When you're done testing the example application:

```bash
# Option 1: Use the cleanup script (recommended)
./cleanup.sh

# Option 2: Manual cleanup
kubectl delete -f grafana-dashboard-configmap.yaml
kubectl delete -f servicemonitor.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f app-configmap.yaml
```

**Important:** This only removes the test application. Your monitoring stack (Prometheus, Grafana, Loki) will continue running.

## 🎯 How It Works

### ConfigMap-Based Deployment
Instead of building a Docker image, the test app uses:

1. **ConfigMap** (`app-configmap.yaml`): Contains Python code and requirements.txt
2. **Init Container**: Installs Python dependencies from requirements.txt
3. **Main Container**: Runs the Python application with dependencies mounted

**Benefits:**
- ✅ No Docker build/push required
- ✅ Easy to modify code (just update ConfigMap)
- ✅ Faster testing and iteration
- ✅ Works with any Kubernetes cluster

**For Production:** Build a proper Docker image with dependencies baked in for better performance and security.

## 🎯 Metric Naming Convention

**IMPORTANT**: All metrics MUST follow this pattern:

```
appname_metricname
```

### ✅ Good Examples
- `myapp_http_requests_total` (Counter with _total suffix)
- `myapp_request_duration_seconds` (Histogram with _seconds suffix)
- `myapp_active_connections` (Gauge, no suffix)
- `myapp_orders_processed_total` (Business metric)

### ❌ Bad Examples
- `http_requests_total` (missing app name)
- `myapp:requests` (using colon instead of underscore)
- `myapp.requests` (using dot instead of underscore)
- `MyApp_Requests` (uppercase letters)

**Why underscore?** Prometheus doesn't support colons in metric names (`:` is reserved for aggregation operations like `sum by`). Always use underscore `_`.

## 📊 Critical Labels for Auto-Discovery

### ServiceMonitor (Prometheus Scraping)
```yaml
metadata:
  labels:
    release: prometheus  # ← REQUIRED for Prometheus Operator to discover
```

### Dashboard ConfigMap (Grafana)
```yaml
metadata:
  labels:
    grafana_dashboard: "1"  # ← REQUIRED for Grafana to auto-load
```

## 🔍 What's Next?

1. **Start with README.md** - Comprehensive developer guide
2. **Review app.py** - Complete working example with 10+ metrics
3. **Check MULTI_LANGUAGE_EXAMPLES.md** - Examples for your language
4. **Read loki-logging.md** - Learn structured logging for Loki

## 🛠️ Multi-Language Support

The example is provided in Python (FastAPI), but `MULTI_LANGUAGE_EXAMPLES.md` includes complete implementations for:

- Python (FastAPI & Flask)
- Go (gorilla/mux)
- Node.js (Express)
- Java (Spring Boot with Micrometer)
- .NET Core (prometheus-net)
- Ruby (Sinatra)
- Rust (Actix)

All examples follow the **same metric naming convention** and patterns.

## 🐛 Troubleshooting

### Metrics Not Appearing in Prometheus?
```bash
# 1. Check if ServiceMonitor was created
kubectl get servicemonitor -n monitoring myapp-servicemonitor

# 2. Verify the critical label exists
kubectl get servicemonitor -n monitoring myapp-servicemonitor -o yaml | grep "release: prometheus"

# 3. Check Prometheus targets
# Open Prometheus UI → Status → Targets → Search for "myapp"
```

### Dashboard Not Appearing in Grafana?
```bash
# 1. Check if ConfigMap was created
kubectl get configmap -n monitoring myapp-dashboard -o yaml

# 2. Verify the critical label exists
kubectl get configmap -n monitoring myapp-dashboard -o yaml | grep "grafana_dashboard"

# 3. Wait 1-2 minutes for Grafana to scan and load the dashboard

# 4. Check Grafana logs
kubectl logs -n monitoring deployment/grafana | grep dashboard
```

### Logs Not Appearing in Loki?
```bash
# 1. Check if pods are running
kubectl get pods -n monitoring -l app=myapp

# 2. Check pod logs are being generated
kubectl logs -n monitoring <pod-name>

# 3. Verify Promtail is running
kubectl get pods -n monitoring | grep promtail

# 4. Check Loki query in Grafana Explore
{namespace="monitoring", app="myapp"}
```

## 📚 Additional Resources

- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **Loki**: https://grafana.com/docs/loki/
- **ServiceMonitor CRD**: https://prometheus-operator.dev/docs/operator/api/#servicemonitor
- **PromQL**: https://prometheus.io/docs/prometheus/latest/querying/basics/

## 🔒 Security Notes

⚠️ **For Production Deployments:**

1. Change Grafana default password (`admin/admin123`)
2. Use specific Docker image versions (not `:latest`)
3. Update `python:3.11-slim` base image (has 2 known vulnerabilities)
4. Add authentication to ServiceMonitor (example in servicemonitor.yaml)
5. Enable TLS for metrics endpoints in production
6. Review and adjust resource limits based on actual usage

---

**Need Help?** Check the comprehensive guides in this directory or contact the monitoring team.
