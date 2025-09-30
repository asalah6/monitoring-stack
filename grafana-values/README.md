# Grafana Configuration

This directory contains the Helm values configuration for Grafana.

## Overview

Grafana is an open-source analytics and monitoring platform that integrates with Prometheus and Loki to provide:
- Beautiful dashboards for metrics visualization
- Log exploration and analysis
- Alerting capabilities
- Multi-datasource support

## Installation

### Prerequisites
- Kubernetes 1.24+ cluster
- Helm 3.x installed
- kubectl configured
- `monitoring` namespace created
- Prometheus already installed

### Add Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Install Grafana

```bash
helm install grafana grafana/grafana \
  --namespace monitoring \
  --values values.yaml
```

### Verify Installation

```bash
# Check pod status
kubectl get pods -n monitoring | grep grafana

# Check service
kubectl get svc -n monitoring | grep grafana

# Get admin password (if using auto-generated)
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo
```

## Accessing Grafana

### Method 1: Port Forward (Testing)

```bash
kubectl port-forward -n monitoring svc/grafana 3000:80
```

Then access at: http://localhost:3000

Login:
- Username: `admin`
- Password: `admin123` (as configured in values.yaml)


## Configuration Details

### Default Credentials

**⚠️ SECURITY WARNING**: Change these in production!

- Username: `admin`
- Password: `admin123`

To change the password:

1. Edit `values.yaml`:
```yaml
adminPassword: "your-secure-password"
```

2. Upgrade Grafana:
```bash
helm upgrade grafana grafana/grafana \
  --namespace monitoring \
  --values values.yaml
```

### Pre-configured Datasources

The configuration includes two datasources:

1. **Prometheus**: Main metrics source
   - URL: `http://prometheus-prometheus.monitoring.svc.cluster.local:9090`
   - Set as default datasource

2. **Loki**: Logs source
   - URL: `http://loki.monitoring.svc.cluster.local:3100`

### Pre-installed Dashboards

The following dashboards are automatically imported:

**Default Folder**:
- Prometheus Stats (ID: 2)
- Node Exporter Full (ID: 1860)

**Kubernetes Folder**:
- Kubernetes Cluster Monitoring (ID: 7249)
- Kubernetes Pod Monitoring (ID: 6417)
- Kubernetes Deployment Monitoring (ID: 9679)

### Installed Plugins

- `grafana-piechart-panel`: Pie chart visualizations
- `grafana-clock-panel`: Clock widget

## Common Configuration Changes

### Change Admin Password

Edit `values.yaml`:
```yaml
adminPassword: "new-secure-password"
```

Then upgrade:
```bash
helm upgrade grafana grafana/grafana --namespace monitoring --values values.yaml
```

### Add More Dashboards

Edit `values.yaml` to add dashboard by ID from [Grafana Dashboard Repository](https://grafana.com/grafana/dashboards/):

```yaml
dashboards:
  default:
    my-custom-dashboard:
      gnetId: 12345  # Dashboard ID from grafana.com
      revision: 1
      datasource: Prometheus
```

### Add Custom Datasource

Edit `values.yaml`:
```yaml
datasources:
  datasources.yaml:
    apiVersion: 1
    datasources:
    - name: MyDatabase
      type: postgres
      url: postgres-service:5432
      database: mydb
      user: grafana
      secureJsonData:
        password: "mypassword"
```

### Enable SMTP for Alerting

Edit `values.yaml`:
```yaml
smtp:
  enabled: true
  host: smtp.gmail.com:587
  user: your-email@gmail.com
  password: your-app-password
  from_address: grafana@yourcompany.com
  from_name: Grafana Alerts

grafana.ini:
  smtp:
    enabled: true
    host: smtp.gmail.com:587
    user: your-email@gmail.com
    password: your-app-password
    from_address: grafana@yourcompany.com
```

### Increase Storage

Edit `values.yaml`:
```yaml
persistence:
  size: 20Gi  # Change from 10Gi
```

### Change Resource Limits

Edit `values.yaml`:
```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
```

## Creating Custom Dashboards

### Via UI

1. Access Grafana at https://monitoring.rc.ds.wt.de
2. Click the "+" icon → "Dashboard"
3. Add panels, queries, and visualizations
4. Save dashboard

### Via ConfigMap (Persistent)

1. Create dashboard JSON file (export from Grafana UI)

2. Create ConfigMap:
```bash
kubectl create configmap my-dashboard \
  --from-file=my-dashboard.json \
  --namespace monitoring
```

3. Mount in Grafana pod by editing values.yaml:
```yaml
extraConfigmapMounts:
  - name: my-dashboard
    mountPath: /var/lib/grafana/dashboards/custom
    configMap: my-dashboard
    readOnly: true
```

## Monitoring with Grafana

### View Prometheus Metrics

1. Login to Grafana
2. Go to "Explore" (compass icon)
3. Select "Prometheus" datasource
4. Enter PromQL query, e.g.:
   - `rate(http_requests_total[5m])`
   - `container_memory_usage_bytes`
   - `node_cpu_seconds_total`

### View Loki Logs

1. Go to "Explore"
2. Select "Loki" datasource
3. Use LogQL query, e.g.:
   - `{namespace="monitoring"}`
   - `{app="my-app"} |= "error"`
   - `{pod=~"prometheus.*"}`

### Create Alerts

1. Go to Alerting → Alert rules
2. Click "Create alert rule"
3. Define query and conditions
4. Set notification channels
5. Save alert


## Troubleshooting

### Cannot Access Grafana

1. Check pod status:
```bash
kubectl get pods -n monitoring | grep grafana
kubectl describe pod <grafana-pod> -n monitoring
```

2. Check logs:
```bash
kubectl logs -n monitoring <grafana-pod>
```

3. Check service:
```bash
kubectl get svc -n monitoring grafana
```

### Datasource Not Working

1. Verify datasource URL is correct
2. Check if Prometheus/Loki is running:
```bash
kubectl get pods -n monitoring
```

3. Test connectivity from Grafana pod:
```bash
kubectl exec -it <grafana-pod> -n monitoring -- curl http://prometheus-prometheus.monitoring.svc.cluster.local:9090/-/healthy
```

### Dashboard Not Loading

1. Check Grafana logs for errors
2. Verify dashboard JSON is valid
3. Check if datasource exists and is accessible

### Persistent Storage Issues

```bash
# Check PVC
kubectl get pvc -n monitoring

# Describe PVC for events
kubectl describe pvc <grafana-pvc> -n monitoring
```

## Updating Configuration

```bash
# Edit values.yaml, then upgrade
helm upgrade grafana grafana/grafana \
  --namespace monitoring \
  --values values.yaml
```

## Uninstalling

```bash
# Uninstall Grafana
helm uninstall grafana -n monitoring

# Delete PVC (if you want to remove data)
kubectl delete pvc grafana -n monitoring
```
