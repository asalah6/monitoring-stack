# Loki Configuration

This directory contains the Helm values configuration for Loki log aggregation system.

## Overview

Loki is a horizontally-scalable, highly-available log aggregation system inspired by Prometheus. It:
- Collects logs from all Kubernetes pods via Promtail
- Stores logs efficiently with 7-day retention (GDPR compliant)
- Integrates with Grafana for log visualization
- Uses labels for log indexing (similar to Prometheus)

## Architecture

This deployment uses **Single Binary Mode** which includes:
- **Loki**: Log storage and query engine
- **Promtail**: Log collector (DaemonSet on each node)

All Loki components run in a single binary for simplicity and lower resource usage.

## Installation

### Prerequisites
- Kubernetes 1.24+ cluster
- Helm 3.x installed
- kubectl configured
- `monitoring` namespace created
- Grafana already installed (optional but recommended)

### Add Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Install Loki

```bash
helm install loki grafana/loki \
  --namespace monitoring \
  --values values.yaml
```

### Verify Installation

```bash
# Check Loki pod
kubectl get pods -n monitoring | grep loki

# Check Promtail DaemonSet (should run on each node)
kubectl get ds -n monitoring | grep promtail

# Check services
kubectl get svc -n monitoring | grep loki

# Check if logs are being ingested
kubectl port-forward -n monitoring svc/loki 3100:3100
# Visit http://localhost:3100/metrics
```

## Configuration Details

### Log Retention: 7 Days

**GDPR Compliance**: Logs are automatically deleted after 7 days.

```yaml
limits_config:
  retention_period: 168h  # 7 days = 168 hours

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
```

### Storage

- **Size**: 50GB persistent volume
- **Type**: Single persistent volume for all Loki data
- **Location**: `/var/loki/`

### Resource Limits

**Loki**:
- CPU: 500m (request) - 2000m (limit)
- Memory: 1Gi (request) - 2Gi (limit)

**Promtail** (per node):
- CPU: 100m (request) - 500m (limit)
- Memory: 128Mi (request) - 256Mi (limit)

### Log Collection

Promtail runs as a DaemonSet on every node and:
- Collects logs from `/var/log/pods/`
- Adds labels: namespace, pod, container, app
- Sends logs to Loki via HTTP

## Querying Logs

### Via Grafana

1. Access Grafana at https://monitoring.rc.ds.wt.de
2. Go to "Explore" (compass icon)
3. Select "Loki" datasource
4. Use LogQL queries

### LogQL Examples

```logql
# All logs from monitoring namespace
{namespace="monitoring"}

# Logs from specific pod
{pod="prometheus-prometheus-prometheus-0"}

# Logs containing "error" (case-insensitive)
{namespace="monitoring"} |~ "(?i)error"

# Logs from app with label
{app="my-app"}

# Logs in time range with filter
{namespace="monitoring"} |= "error" | json

# Count errors per minute
rate({namespace="monitoring"} |= "error" [1m])
```

### Via Loki API

```bash
# Port forward Loki
kubectl port-forward -n monitoring svc/loki 3100:3100

# Query logs
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="monitoring"}' \
  --data-urlencode 'limit=100' | jq

# Get labels
curl -s "http://localhost:3100/loki/api/v1/labels" | jq

# Get label values
curl -s "http://localhost:3100/loki/api/v1/label/namespace/values" | jq
```

## Common Configuration Changes

### Change Retention Period

**To change to 14 days**:

Edit `values.yaml`:
```yaml
limits_config:
  retention_period: 336h  # 14 days = 336 hours
  reject_old_samples_max_age: 336h

table_manager:
  retention_period: 336h
```

Then upgrade:
```bash
helm upgrade loki grafana/loki --namespace monitoring --values values.yaml
```

### Increase Storage

Edit `values.yaml`:
```yaml
singleBinary:
  persistence:
    size: 100Gi  # Change from 50Gi
```

**Note**: May require PVC expansion or recreation.

### Change Resource Limits

Edit `values.yaml`:
```yaml
singleBinary:
  resources:
    requests:
      cpu: 1000m
      memory: 2Gi
    limits:
      cpu: 4000m
      memory: 4Gi
```

### Add Custom Scrape Config

Edit `values.yaml` to add custom Promtail scrape configs:

```yaml
promtail:
  config:
    scrapeConfigs: |
      # Your existing config...
      
      # Add custom scrape job
      - job_name: system-logs
        static_configs:
          - targets:
              - localhost
            labels:
              job: system-logs
              __path__: /var/log/syslog
```

### Filter Specific Logs

To exclude certain logs from collection, add pipeline stages:

```yaml
promtail:
  config:
    scrapeConfigs: |
      - job_name: kubernetes-pods
        pipeline_stages:
          - cri: {}
          # Drop logs matching pattern
          - drop:
              expression: ".*healthcheck.*"
          # Drop specific namespace
          - match:
              selector: '{namespace="kube-system"}'
              action: drop
```

## Monitoring Loki

### ServiceMonitor

Loki exposes Prometheus metrics at `/metrics`. A ServiceMonitor is automatically created:

```yaml
serviceMonitor:
  enabled: true
  namespace: monitoring
  labels:
    release: prometheus
```

### Key Metrics to Monitor

- `loki_ingester_received_chunks`: Chunks received
- `loki_distributor_bytes_received_total`: Bytes ingested
- `loki_request_duration_seconds`: Query latency
- `loki_panic_total`: Panics (should be 0)

View in Prometheus:
```promql
rate(loki_distributor_bytes_received_total[5m])
```

## Verifying Log Collection

### Check if Logs Are Being Collected

```bash
# Check Promtail logs
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=50

# Check Loki logs
kubectl logs -n monitoring -l app.kubernetes.io/name=loki --tail=50

# Query via API
kubectl port-forward -n monitoring svc/loki 3100:3100
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="monitoring"}' \
  --data-urlencode 'limit=10' | jq
```

### Test Log Ingestion

Create a test pod that generates logs:

```bash
kubectl run test-logs --image=busybox --namespace=default -- sh -c 'while true; do echo "Test log message at $(date)"; sleep 5; done'

# Wait a minute, then query in Grafana:
{pod="test-logs"}

# Delete test pod
kubectl delete pod test-logs --namespace=default
```

## Troubleshooting

### Loki Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n monitoring -l app.kubernetes.io/name=loki

# Check logs
kubectl logs -n monitoring -l app.kubernetes.io/name=loki

# Common issues:
# - PVC not binding (check storage class)
# - Resource limits too low
# - Config syntax error
```

### Promtail Not Collecting Logs

```bash
# Check Promtail DaemonSet
kubectl get ds -n monitoring promtail

# Check Promtail logs
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=100

# Check if Promtail can reach Loki
kubectl exec -n monitoring -l app.kubernetes.io/name=promtail -- wget -O- http://loki:3100/ready

# Common issues:
# - Promtail can't access /var/log/pods (check volumes)
# - Network policy blocking Promtail -> Loki
# - Loki not ready
```

### No Logs in Grafana

1. Check Loki datasource in Grafana:
   - Settings → Data Sources → Loki
   - Click "Test" button
   - Should show "Data source connected and labels found"

2. Verify logs exist:
```bash
kubectl port-forward -n monitoring svc/loki 3100:3100
curl -s "http://localhost:3100/loki/api/v1/labels" | jq
```

3. Try simple query in Grafana Explore:
```logql
{namespace="monitoring"}
```

### High Memory Usage

If Loki uses too much memory:

1. Reduce retention period
2. Increase `split_queries_by_interval`
3. Add more resources
4. Consider splitting to microservices mode

### Storage Full

```bash
# Check PVC usage
kubectl exec -n monitoring -l app.kubernetes.io/name=loki -- df -h /var/loki

# Check compactor is running
kubectl logs -n monitoring -l app.kubernetes.io/name=loki | grep compactor

# Manually trigger compaction
kubectl exec -n monitoring -l app.kubernetes.io/name=loki -- wget -O- http://localhost:3100/compactor/ring
```

## GDPR Compliance

This configuration is designed for GDPR compliance:

1. **7-Day Retention**: Logs older than 7 days are automatically deleted
2. **Compactor**: Runs every 10 minutes to enforce retention
3. **Delete Delay**: 2-hour delay before actual deletion (allows recovery)

### Verifying Retention

```bash
# Check oldest logs
kubectl port-forward -n monitoring svc/loki 3100:3100

# Query old logs (should return nothing after 7 days)
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={namespace="monitoring"}' \
  --data-urlencode 'start=8d' \
  --data-urlencode 'end=7d' | jq
```

## Upgrading

```bash
# Pull latest chart
helm repo update

# Upgrade Loki
helm upgrade loki grafana/loki \
  --namespace monitoring \
  --values values.yaml
```

## Uninstalling

```bash
# Uninstall Loki
helm uninstall loki -n monitoring

# Delete PVC (if you want to remove all logs)
kubectl delete pvc storage-loki-0 -n monitoring
```
