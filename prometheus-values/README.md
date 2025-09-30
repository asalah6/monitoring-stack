# Prometheus Configuration

This directory contains the Helm values configuration for Prometheus monitoring stack using `kube-prometheus-stack`.

## Overview

The `kube-prometheus-stack` includes:
- **Prometheus Operator**: Manages Prometheus instances
- **Prometheus**: Time-series database for metrics
- **Alertmanager**: Handles alerts
- **Node Exporter**: Collects node-level metrics
- **Kube State Metrics**: Collects Kubernetes object metrics
- **ServiceMonitor CRDs**: Automatically discover services to scrape

## Installation

### Prerequisites
- Kubernetes 1.24+ cluster
- Helm 3.x installed
- kubectl configured to access your cluster
- `monitoring` namespace created

### Add Helm Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

### Install Prometheus Stack

```bash
# Install using version compatible with K8s 1.24
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --version 45.31.1 \
  --values values.yaml
```

### Verify Installation

```bash
# Check all pods are running
kubectl get pods -n monitoring

# Check services
kubectl get svc -n monitoring

# Check ServiceMonitor CRDs
kubectl get servicemonitors -n monitoring
```

## Configuration Details

### Key Settings

- **Retention**: 15 days of metrics data
- **Storage**: 50GB persistent volume for Prometheus
- **Scrape Interval**: 30 seconds
- **Service Monitor**: Automatically discovers services with proper labels

### Service Monitor Labels

For Prometheus to scrape your application, create a ServiceMonitor with these labels:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: my-namespace
  labels:
    app: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Resource Limits

**Prometheus**:
- CPU: 500m (request) - 2000m (limit)
- Memory: 2Gi (request) - 4Gi (limit)

**Alertmanager**:
- CPU: 100m (request) - 500m (limit)
- Memory: 256Mi (request) - 512Mi (limit)

## Updating Configuration

### Method 1: Helm Upgrade

```bash
# Edit values.yaml, then upgrade
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --version 45.31.1 \
  --values values.yaml
```

### Method 2: Direct kubectl Edit

```bash
# Edit Prometheus instance directly
kubectl edit prometheus -n monitoring prometheus-kube-prometheus-prometheus
```

## Common Configuration Changes

### Change Retention Period

Edit `values.yaml`:
```yaml
prometheus:
  prometheusSpec:
    retention: 30d  # Change from 15d to 30d
```

Then upgrade:
```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --version 45.31.1 \
  --values values.yaml
```

### Change Scrape Interval

Edit `values.yaml`:
```yaml
prometheus:
  prometheusSpec:
    scrapeInterval: 15s  # Change from 30s to 15s
```

### Add Additional Scrape Configs

Edit `values.yaml`:
```yaml
prometheus:
  prometheusSpec:
    additionalScrapeConfigs:
    - job_name: 'my-custom-job'
      static_configs:
      - targets: ['my-service:9090']
```

### Increase Storage

Edit `values.yaml`:
```yaml
prometheus:
  prometheusSpec:
    storageSpec:
      volumeClaimTemplate:
        spec:
          resources:
            requests:
              storage: 100Gi  # Change from 50Gi
```

**Note**: Increasing storage requires deleting and recreating the PVC, or using volume expansion if your storage class supports it.

## Accessing Prometheus UI

### Port Forward (for testing)

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Then access at: http://localhost:9090

### Via Istio VirtualService

See `/virtualservice/README.md` for production access configuration.

## Monitoring Your Applications

### Step 1: Expose Metrics Endpoint

Your application must expose metrics at `/metrics` endpoint in Prometheus format.

Example using Python FastAPI:
```python
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Response

app = FastAPI()
request_count = Counter('http_requests_total', 'Total HTTP requests')

@app.get("/metrics")
async def metrics():
    request_count.inc()
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### Step 2: Create Service with metrics port

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  ports:
  - name: metrics  # Important: name must be 'metrics' or match ServiceMonitor
    port: 8000
    targetPort: 8000
  selector:
    app: my-app
```

### Step 3: Create ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: my-namespace
  labels:
    app: my-app
spec:
  selector:
    matchLabels:
      app: my-app
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Step 4: Verify Scraping

```bash
# Check if ServiceMonitor is created
kubectl get servicemonitor -n my-namespace

# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit http://localhost:9090/targets
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n monitoring

# Check logs
kubectl logs <pod-name> -n monitoring
```

### ServiceMonitor Not Working

1. Check if ServiceMonitor exists:
```bash
kubectl get servicemonitor -n <namespace>
```

2. Check Prometheus logs:
```bash
kubectl logs -n monitoring prometheus-prometheus-kube-prometheus-prometheus-0
```

3. Verify service labels match ServiceMonitor selector:
```bash
kubectl get svc <service-name> -n <namespace> --show-labels
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n monitoring

# Check storage class
kubectl get storageclass
```

## Uninstalling

```bash
# Uninstall Helm release
helm uninstall prometheus -n monitoring

# Delete CRDs (if needed)
kubectl delete crd alertmanagerconfigs.monitoring.coreos.com
kubectl delete crd alertmanagers.monitoring.coreos.com
kubectl delete crd podmonitors.monitoring.coreos.com
kubectl delete crd probes.monitoring.coreos.com
kubectl delete crd prometheuses.monitoring.coreos.com
kubectl delete crd prometheusrules.monitoring.coreos.com
kubectl delete crd servicemonitors.monitoring.coreos.com
kubectl delete crd thanosrulers.monitoring.coreos.com
```
