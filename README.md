# Kubernetes Monitoring Stack

Complete monitoring infrastructure for Kubernetes cluster with Prometheus, Grafana, and Loki.

## Overview

This repository contains Infrastructure-as-Code (IaC) for deploying a production-ready monitoring stack on Kubernetes with:

- **Prometheus** - Metrics collection and alerting
- **Grafana** - Visualization and dashboards  
- **Loki** - Log aggregation and querying
- **Promtail** - Log collection agent (DaemonSet)
- **GDPR Compliance** - 7-day log retention
- **Istio Integration** - External access via VirtualService

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Access (HTTPS)                       │
│              https://monitoring.rc.ds.wt.de                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│           Istio Ingress Gateway (knative-serving)                │
│                    SSL/TLS Termination                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Monitoring Namespace                            │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │   Grafana    │◄───┤  Prometheus  │    │     Loki     │     │
│  │  (Dashboard) │    │   (Metrics)  │    │    (Logs)    │     │
│  │              │◄───┤              │    │      ▲       │     │
│  │  Port: 3000  │    │  Port: 9090  │    │      │       │     │
│  └──────────────┘    └──────┬───────┘    └──────┼───────┘     │
│                              │                    │              │
└──────────────────────────────┼────────────────────┼──────────────┘
                               │                    │
                               ▼                    │ Push logs
              ┌────────────────────────────────────┼────────┐
              │         Kubernetes Cluster         │        │
              │  • 7 Nodes (3 control plane, 4 workers)    │
              │  • Kubernetes v1.24.13                     │
              │  • ServiceMonitors for auto-discovery      │
              │                                            │
              │  ┌─────────────────────────────────┐      │
              │  │  Promtail DaemonSet (7 pods)    │──────┘
              │  │  Reads: /var/log/pods/*         │
              │  └─────────────────────────────────┘
              └────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Kubernetes cluster v1.24+ (tested on v1.24.13)
- Helm v3.18+ installed
- kubectl configured with cluster access
- Istio with ingress gateway
- Default storage class for PVC provisioning

### Installation

1. **Clone the repository**
   ```bash
   git clone https://gitlab.se.wt.de/data-science/mlops/monitoring.git
   cd monitoring
   ```

2. **Create monitoring namespace**
   ```bash
   kubectl create namespace monitoring
   ```

3. **Add Helm repositories**
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   ```

4. **Install Prometheus**
   ```bash
   helm install prometheus prometheus-community/kube-prometheus-stack \
     --namespace monitoring \
     --version 45.31.1 \
     --values ./prometheus-values/values.yaml
   ```

5. **Install Grafana**
   ```bash
   helm install grafana grafana/grafana \
     --namespace monitoring \
     --values ./grafana-values/values.yaml
   ```

6. **Install Loki**
   ```bash
   helm install loki grafana/loki \
     --namespace monitoring \
     --values ./loki-values/values.yaml
   ```

7. **Install Promtail** (Log collection agent)
   ```bash
   helm install promtail grafana/promtail \
     --namespace monitoring \
     --values ./promtail-values/values.yaml
   ```

8. **Configure External Access**
   ```bash
   kubectl apply -f ./virtualservice/grafana-virtualservice.yaml
   ```

9. **Access Grafana**
   
   URL: **https://monitoring.rc.ds.wt.de**
   
   Credentials:
   - Username: `admin`
   - Password: `admin123` (To be changed!)

10. **Verify Log Collection**
    
    Access Grafana → Explore → Select Loki datasource → Run:
    ```logql
    {namespace="monitoring"}
    ```

## Repository Structure

```
monitoring/
├── README.md                          # This file
├── prometheus-values/                 # Prometheus configuration
│   ├── values.yaml                    # Prometheus configuration values
│   └── README.md                      # Prometheus documentation
├── grafana-values/                    # Grafana configuration
│   ├── values.yaml                    # Grafana configuration values
│   └── README.md                      # Grafana documentation
├── loki-values/                       # Loki configuration
│   ├── values.yaml                    # Loki configuration values
│   └── README.md                      # Loki documentation
├── promtail-values/                   # Promtail configuration
│   ├── values.yaml                    # Promtail configuration values
│   └── README.md                      # Promtail documentation
├── virtualservice/                    # Istio routing
│   ├── grafana-virtualservice.yaml   # VirtualService definition
│   └── README.md                      # Routing documentation
└── test-app/                          # Example application for developers
    ├── 00-GETTING-STARTED.md         # Quick start guide
    ├── README.md                      # Comprehensive developer guide
    ├── TESTING_GUIDE.md              # How to test the example
    ├── MULTI_LANGUAGE_EXAMPLES.md    # 8 language implementations
    ├── loki-logging.md               # Loki integration guide
    ├── app-configmap.yaml            # Application code as ConfigMap
    ├── deployment.yaml               # Kubernetes Deployment
    ├── service.yaml                  # Kubernetes Service
    ├── servicemonitor.yaml           # Prometheus scraping config
    ├── grafana-dashboard-configmap.yaml  # Auto-discovered dashboard
    ├── deploy.sh                     # Deploy test app (no Docker build!)
    └── cleanup.sh                    # Remove test app when done
```

## Cluster Information

**Kubernetes Version**: v1.24.13  
**Container Runtime**: Docker 20.10.21  
**Nodes**: 7 (3 control plane + 4 workers)  
**Rancher**: Active (cattle-system namespace)  
**Istio**: Active with ingress gateway

**Control Plane Nodes**:
- ranch1-cl4-m01 (172.17.98.221)
- ranch1-cl4-m02 (172.17.98.222)  
- ranch1-cl4-m03 (172.17.98.223)

**Worker Nodes**:
- ranch1-cl4-w01 (172.17.98.224)
- ranch1-cl4-w02 (172.17.98.225)
- ranch1-cl4-w04 (picasso)
- ranch1-cl4-w05 (vangogh)

## Installed Components

### Prometheus Stack (v45.31.1)

- **Prometheus Operator** - Manages Prometheus instances
- **Prometheus Server** - Metrics collection (15-day retention, 50GB storage)
- **Alertmanager** - Alert handling and routing
- **Node Exporter** - Host metrics (DaemonSet on all nodes)
- **Kube State Metrics** - Kubernetes object metrics

**Internal Access**: http://prometheus-prometheus.monitoring.svc.cluster.local:9090

**Pods Running**:
```
prometheus-prometheus-prometheus-0       # Main Prometheus server
alertmanager-prometheus-alertmanager-0   # Alertmanager
prometheus-operator-*                     # Operator
prometheus-kube-state-metrics-*          # K8s metrics
prometheus-prometheus-node-exporter-*    # Node exporters (DaemonSet)
```

### Grafana (Latest)

- **Pre-configured dashboards**: Node Exporter, Kubernetes Cluster
- **Datasources**: Prometheus and Loki (pre-configured)
- **Persistence**: 10GB PVC for dashboards and settings
- **External access**: https://monitoring.rc.ds.wt.de

**Internal Access**: http://grafana.monitoring.svc.cluster.local

**Pods Running**:
```
grafana-*   # Grafana server
```

### Loki (v3.5.5)

- **Deployment mode**: SingleBinary (simplified for smaller clusters)
- **Retention**: 7 days (GDPR compliant)
- **Log collection**: Via Promtail DaemonSet
- **Storage**: 50GB filesystem storage
- **Compactor**: Enabled for retention enforcement

**Internal Access**: http://loki-gateway.monitoring.svc.cluster.local

**Pods Running**:
```
loki-0                   # Loki SingleBinary
loki-gateway-*           # NGINX gateway for Loki
loki-chunks-cache-0      # Chunk cache
loki-results-cache-0     # Results cache
loki-canary-*            # Health check canaries (DaemonSet)
```

### Promtail (Log Agent)

- **Deployment mode**: DaemonSet (runs on all 7 nodes)
- **Function**: Scrapes container logs and ships to Loki
- **Log sources**: `/var/log/pods/`, `/var/lib/docker/containers/`
- **Labels**: Automatically adds namespace, pod, container, node labels
- **Resource usage**: 100m CPU / 128Mi RAM per pod

**Pods Running**:
```
promtail-*              # Promtail DaemonSet (7 pods total)
```

## GDPR Compliance

### Log Retention Policy

- **Duration**: 7 days (168 hours)
- **Enforcement**: Automated via Loki compactor
- **Deletion**: Logs older than 7 days are automatically deleted
- **Compaction**: Runs every 10 minutes
- **Configuration**: See `loki-values/README.md` for details

### Verification

Check retention configuration:
```bash
kubectl logs -n monitoring loki-0 -c loki | grep retention
```

### Data Privacy

- Logs are stored within the cluster (no external transmission)
- Retention is enforced at the storage level
- No personal data should be logged without proper justification
- Compactor automatically purges old data

## Verification

### Check All Pods

```bash
kubectl get pods -n monitoring
```

Expected output: All pods should be in `Running` state.

### Test Grafana Access

**Internal (port-forward)**:
```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
# Access http://localhost:3000
```

**External (via Istio)**:
```bash
curl -I https://monitoring.rc.ds.wt.de
```

### Test Prometheus

```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Access http://localhost:9090
# Check Status → Targets
```

### Test Loki

```bash
kubectl port-forward -n monitoring svc/loki-gateway 3100:80
curl http://localhost:3100/ready
```

### Verify ServiceMonitor Discovery

Access Grafana → Explore → Select Prometheus → Run query:
```promql
up{job="prometheus-kube-state-metrics"}
```

### Verify Promtail is Running

```bash
kubectl get daemonset -n monitoring promtail
kubectl get pods -n monitoring -l app.kubernetes.io/name=promtail
```

Expected: 7 pods running (one per node)

### Verify Log Collection

Access Grafana → Explore → Select Loki → Run query:
```logql
{namespace="monitoring"}
```

You should see logs from all monitoring pods with labels like `namespace`, `pod`, `container`, `node`.

## Monitoring Capabilities

### What's Being Monitored

- **Cluster metrics**: CPU, memory, disk, network
- **Node health**: All 7 nodes via Node Exporter
- **Kubernetes objects**: Pods, deployments, services, etc.
- **Control plane**: API server, scheduler, controller manager
- **Container logs**: All pods (auto-discovered)
- **Prometheus self-monitoring**: Prometheus, Alertmanager
- **Grafana metrics**: Available via Prometheus

### Adding New Monitoring Targets

To monitor your application with Prometheus:

1. **Try the example first**:
   ```bash
   cd test-app/
   ./deploy.sh
   ```
   This deploys a complete working example with metrics, dashboard, and logs.

2. **For your application**, expose `/metrics` endpoint in Prometheus format
3. **Create a ServiceMonitor** (see `test-app/servicemonitor.yaml` for examples)
4. **Create a Grafana dashboard** as ConfigMap (see `test-app/grafana-dashboard-configmap.yaml`)
5. **Enable structured logging** for Loki (see `test-app/loki-logging.md`)

**Comprehensive Developer Guide**: See `test-app/` directory for:
- Complete working example (Python FastAPI)
- Metric naming conventions
- ServiceMonitor configuration
- Grafana dashboard auto-discovery
- Loki log collection

To monitor your application with Prometheus:

1. Expose `/metrics` endpoint in your application (Prometheus format)
2. Create a ServiceMonitor:
   ```yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: my-app
     namespace: my-namespace
     labels:
       release: prometheus  # Important for discovery!
   spec:
     selector:
       matchLabels:
         app: my-app
     endpoints:
       - port: metrics
         interval: 30s
   ```

See `prometheus-values/README.md` for complete examples.

## Configuration

### Changing Default Passwords

**Grafana**:
```bash
# Edit the values file
vi grafana-values/values-simple.yaml
# Change: adminPassword: admin123

# Upgrade Helm release
helm upgrade grafana grafana/grafana \
  --namespace monitoring \
  --values ./grafana-values/values-simple.yaml
```

### Adjusting Retention Periods

**Prometheus** (edit `prometheus-values/values.yaml`):
```yaml
prometheus:
  prometheusSpec:
    retention: 15d  # Change this value
    retentionSize: 50GB
```

**Loki** (edit `loki-values/values-simple.yaml`):
```yaml
limits_config:
  retention_period: 168h  # 7 days (GDPR requirement - don't change without approval)
```

### Resource Limits

Default resource allocations:

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| Prometheus | 500m | 2000m | 2Gi | 4Gi |
| Grafana | 250m | 1000m | 512Mi | 1Gi |
| Loki | 500m | 2000m | 1Gi | 2Gi |
| Promtail (per pod) | 100m | 200m | 128Mi | 256Mi |

Adjust in the respective `values.yaml` files.

## Troubleshooting

### Prometheus Not Scraping Targets

1. Check ServiceMonitor labels:
   ```bash
   kubectl get servicemonitor -n <namespace> <name> -o yaml
   ```
   
2. Verify the `release: prometheus` label exists

3. Check Prometheus configuration:
   ```bash
   kubectl port-forward -n monitoring prometheus-prometheus-prometheus-0 9090:9090
   # Visit http://localhost:9090/config
   ```

4. Check Prometheus logs:
   ```bash
   kubectl logs -n monitoring prometheus-prometheus-prometheus-0 -c prometheus
   ```

### Grafana Can't Connect to Datasources

1. Test connectivity from Grafana pod:
   ```bash
   kubectl exec -n monitoring deploy/grafana -- \
     curl -v http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up
   ```

2. Check datasource configuration in Grafana UI:
   - Configuration → Data Sources
   - Click "Test" button

### Loki Not Receiving Logs

1. Check if Promtail is running:
   ```bash
   kubectl get daemonset -n monitoring promtail
   kubectl get pods -n monitoring -l app.kubernetes.io/name=promtail
   kubectl logs -n monitoring -l app.kubernetes.io/name=promtail --tail=50
   ```
   
   Look for: `level=info msg="Successfully sent batch"`

2. Check if Loki is running:
   ```bash
   kubectl get pods -n monitoring | grep loki
   kubectl logs -n monitoring loki-0 -c loki --tail=50
   ```

3. Test connectivity from Promtail to Loki:
   ```bash
   kubectl exec -n monitoring -l app.kubernetes.io/name=promtail -- \
     wget -qO- http://loki-gateway.monitoring.svc.cluster.local/ready
   ```

4. Test log ingestion:
   ```bash
   kubectl port-forward -n monitoring svc/loki-gateway 3100:80
   
   curl -H "Content-Type: application/json" -XPOST \
     "http://localhost:3100/loki/api/v1/push" \
     --data-raw '{"streams": [{"stream": {"job": "test"}, "values": [["'"$(date +%s)"'000000000", "test log"]]}]}'
   ```

5. Query logs:
   ```bash
   curl "http://localhost:3100/loki/api/v1/query_range" --data-urlencode 'query={job="test"}'
   ```


## Detailed Documentation

Each component has comprehensive documentation in its respective folder:

- **[Prometheus Documentation](prometheus-values/README.md)** - Configuration, ServiceMonitors, troubleshooting, query examples
- **[Grafana Documentation](grafana-values/README.md)** - Dashboards, datasources, security, UI testing
- **[Loki Documentation](loki-values/README.md)** - Log queries (LogQL), retention, GDPR compliance
- **[Promtail Documentation](promtail-values/README.md)** - Log collection, DaemonSet configuration, troubleshooting
- **[VirtualService Documentation](virtualservice/README.md)** - External access, SSL/TLS, Istio routing
- **[Test Application](test-app/README.md)** - Example app with metrics endpoint

---

**Repository**: https://gitlab.se.wt.de/data-science/mlops/monitoring  
**Last Updated**: September 30, 2025  
**Cluster**: ranch1-cl4 (Kubernetes v1.24.13)  
**Maintainer**: Data Science MLOps Team
