# Promtail Configuration

Promtail is a log collection agent that ships logs to Loki. It runs as a DaemonSet on every node in the cluster to scrape container logs.

## Overview

- **Version**: Compatible with Loki 3.5.5 (chart: loki-6.41.1)
- **Deployment**: DaemonSet (runs on all 7 nodes)
- **Function**: Scrapes container logs and sends to Loki
- **Target**: http://loki-gateway.monitoring.svc.cluster.local

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Node 1     │  │   Node 2     │  │   Node 7     │     │
│  │              │  │              │  │              │     │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │
│  │ │ Promtail │ │  │ │ Promtail │ │  │ │ Promtail │ │     │
│  │ │ DaemonSet│ │  │ │ DaemonSet│ │  │ │ DaemonSet│ │     │
│  │ └────┬─────┘ │  │ └────┬─────┘ │  │ └────┬─────┘ │     │
│  │      │       │  │      │       │  │      │       │     │
│  │   Reads      │  │   Reads      │  │   Reads      │     │
│  │      ↓       │  │      ↓       │  │      ↓       │     │
│  │ /var/log/pods│  │ /var/log/pods│  │ /var/log/pods│     │
│  └──────┼───────┘  └──────┼───────┘  └──────┼───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           ↓                                │
│                   ┌──────────────┐                         │
│                   │     Loki     │                         │
│                   │   Gateway    │                         │
│                   │   Port 3100  │                         │
│                   └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## What Promtail Does

1. **Discovers Logs**: Automatically finds all pod logs via Kubernetes API
2. **Parses Logs**: Extracts metadata (namespace, pod, container, etc.)
3. **Labels Logs**: Adds labels for easy querying in Grafana
4. **Ships Logs**: Sends logs to Loki gateway
5. **Tracks Position**: Remembers where it left off to avoid duplicates

## Labels Added to Logs

Promtail automatically adds these labels to every log line:

- `namespace` - Kubernetes namespace
- `pod` - Pod name
- `container` - Container name within the pod
- `node` - Node where the pod is running
- `app` - Application label (if exists)
- `job` - Job name (app label or pod name)

## Installation

### 1. Add Grafana Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 2. Install Promtail

```bash
helm install promtail grafana/promtail \
  --namespace monitoring \
  --values ./promtail-values/values.yaml
```

### 3. Verify Installation

```bash
# Check DaemonSet
kubectl get daemonset -n monitoring promtail

# Check pods (should be 7 pods - one per node)
kubectl get pods -n monitoring -l app.kubernetes.io/name=promtail

# Check logs
kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=20
```

Expected output:
```
NAME       DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
promtail   7         7         7       7            7           <none>          1m
```

### 4. Verify Log Collection

Access Grafana (https://monitoring.rc.ds.wt.de):

1. Go to **Explore**
2. Select **Loki** datasource
3. Run this query:
   ```logql
   {namespace="monitoring"}
   ```

You should see logs from all monitoring namespace pods.

## Configuration Details

### Loki Endpoint

Promtail sends logs to:
```
http://loki-gateway.monitoring.svc.cluster.local/loki/api/v1/push
```

If you changed the Loki service name during installation, update this in `values.yaml`:
```yaml
config:
  clients:
    - url: http://YOUR-LOKI-SERVICE.monitoring.svc.cluster.local/loki/api/v1/push
```

### Log Sources

Promtail reads logs from:
- `/var/log/pods/*` - All pod logs
- `/var/lib/docker/containers/*` - Docker container logs
- `/var/log/*.log` - System component logs

### Resource Limits

Default resources per Promtail pod:
- CPU Request: 100m
- CPU Limit: 200m
- Memory Request: 128Mi
- Memory Limit: 256Mi

Adjust if needed in `values.yaml`.

### Security

Promtail runs as:
- **Privileged**: Yes (needs access to host filesystem)
- **User**: root (UID 0)
- **Tolerations**: Runs on all nodes including control plane

## Querying Logs in Grafana

### Basic Queries

**All logs from a namespace**:
```logql
{namespace="monitoring"}
```

**Logs from specific pod**:
```logql
{namespace="monitoring", pod="loki-0"}
```

**Logs from specific app**:
```logql
{app="grafana"}
```

**Logs from specific container**:
```logql
{namespace="monitoring", container="prometheus"}
```

### Advanced Queries

**Filter by log content**:
```logql
{namespace="monitoring"} |= "error"
```

**Exclude specific content**:
```logql
{namespace="monitoring"} != "debug"
```

**Regex pattern matching**:
```logql
{namespace="monitoring"} |~ "error|failed|exception"
```

**Parse JSON logs**:
```logql
{namespace="monitoring"} | json | level="error"
```

**Count errors per minute**:
```logql
sum(count_over_time({namespace="monitoring"} |= "error" [1m]))
```

## Troubleshooting

### Promtail Pods Not Starting

Check DaemonSet status:
```bash
kubectl describe daemonset -n monitoring promtail
```

Check pod events:
```bash
kubectl get events -n monitoring --field-selector involvedObject.name=promtail-xxxxx
```

### No Logs Appearing in Loki

1. **Check Promtail is sending logs**:
   ```bash
   kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=50
   ```
   
   Look for lines like:
   ```
   level=info msg="Successfully sent batch"
   ```

2. **Test connectivity to Loki**:
   ```bash
   kubectl exec -n monitoring -l app.kubernetes.io/name=promtail -- \
     wget -qO- http://loki-gateway.monitoring.svc.cluster.local/ready
   ```
   
   Should return: `ready`

3. **Check Loki is receiving logs**:
   ```bash
   kubectl logs -n monitoring loki-0 -c loki --tail=50 | grep "POST /loki/api/v1/push"
   ```

### Promtail Using Too Much Memory

Reduce resource limits or decrease the number of scrape targets by excluding certain namespaces:

```yaml
config:
  scrape_configs:
    - job_name: kubernetes-pods
      kubernetes_sd_configs:
        - role: pod
          namespaces:
            names:
              - monitoring
              - default
              - your-app-namespace
```

### Logs Missing from Specific Pods

1. Check if Promtail can access the pod logs:
   ```bash
   kubectl exec -n monitoring promtail-xxxxx -- ls -la /var/log/pods/
   ```

2. Check Promtail targets:
   ```bash
   kubectl port-forward -n monitoring promtail-xxxxx 3101:3101
   curl http://localhost:3101/targets
   ```

## Maintenance

### Updating Promtail

```bash
# Update Helm repository
helm repo update

# Check available versions
helm search repo grafana/promtail --versions | head -10

# Upgrade
helm upgrade promtail grafana/promtail \
  --namespace monitoring \
  --values ./promtail-values/values.yaml
```

### Restarting Promtail

```bash
# Restart all Promtail pods
kubectl rollout restart daemonset/promtail -n monitoring

# Check status
kubectl rollout status daemonset/promtail -n monitoring
```

### Checking Promtail Metrics

Promtail exposes metrics on port 3101:
```bash
kubectl port-forward -n monitoring promtail-xxxxx 3101:3101
curl http://localhost:3101/metrics
```

Key metrics:
- `promtail_sent_entries_total` - Total log entries sent
- `promtail_dropped_entries_total` - Dropped entries (should be 0)
- `promtail_read_lines_total` - Lines read from logs

## Integration with Prometheus

Promtail includes a ServiceMonitor for automatic discovery by Prometheus:

```yaml
serviceMonitor:
  enabled: true
  labels:
    release: prometheus  # Match your Prometheus release name
```

Check in Prometheus:
1. Port-forward to Prometheus: `kubectl port-forward -n monitoring prometheus-prometheus-prometheus-0 9090:9090`
2. Visit http://localhost:9090/targets
3. Look for `promtail` targets

---

**Last Updated**: September 30, 2025  
**Promtail Chart**: Compatible with loki-6.41.1  
**Cluster**: ranch1-cl4 (Kubernetes v1.24.13)
