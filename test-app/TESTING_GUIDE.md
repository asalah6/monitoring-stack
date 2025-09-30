# Testing the Example Application

## Quick Test

This guide shows you how to quickly test the example application to see Prometheus metrics, Grafana dashboards, and Loki logs in action.

### Prerequisites
- Kubernetes cluster with monitoring stack deployed
- kubectl configured
- Monitoring namespace exists

### Step 1: Deploy the Test Application

```bash
cd test-app/
./deploy.sh
```

This will:
1. Create ConfigMap with application code
2. Deploy the application (2 replicas)
3. Create Kubernetes Service
4. Create ServiceMonitor for Prometheus
5. Create Grafana dashboard ConfigMap

**Note:** The init container installs Python dependencies on first start (~1-2 minutes).

### Step 2: Wait for Pods to be Ready

```bash
# Check pod status
kubectl get pods -n monitoring -l app=myapp

# Expected output:
# NAME                     READY   STATUS    RESTARTS   AGE
# myapp-xxxxx-yyyyy       1/1     Running   0          2m
# myapp-xxxxx-zzzzz       1/1     Running   0          2m
```

### Step 3: Test the Application

```bash
# Port-forward to access locally
kubectl port-forward -n monitoring svc/myapp 8000:8000

# In another terminal, test endpoints:
curl http://localhost:8000/
curl http://localhost:8000/api/users
curl http://localhost:8000/metrics
```

### Step 4: Verify Grafana Dashboard

1. Open Grafana: https://monitoring.rc.ds.wt.de
2. Login: `admin` / `admin123`
3. Go to **Dashboards**
4. Find **MyApp Metrics Dashboard** (auto-discovered within 1-2 minutes)
5. You should see 8 panels with live data:
   - HTTP Request Rate
   - Request Duration (p95/p99)
   - Active Connections
   - Error Rate
   - Memory Usage
   - Request Breakdown
   - Business Metrics (Orders, Payments)

### Step 5: Verify Loki Logs

1. In Grafana, go to **Explore**
2. Select **Loki** data source
3. Try these queries:
   ```logql
   {namespace="monitoring", app="myapp"}
   {namespace="monitoring", app="myapp"} |= "error"
   {namespace="monitoring", app="myapp"} | json | line_format "{{.levelname}} {{.message}}"
   ```

4. You should see JSON formatted logs with fields like:
   - `levelname`: INFO, ERROR, etc.
   - `message`: Log message
   - `method`, `path`, `status_code`: HTTP request details
   - `duration`: Request duration

### Step 6: Generate Some Traffic

Generate traffic to see metrics and logs:

```bash
# Port-forward in one terminal
kubectl port-forward -n monitoring svc/myapp 8000:8000

# In another terminal, generate requests
for i in {1..100}; do
  curl -s http://localhost:8000/ > /dev/null
  curl -s http://localhost:8000/api/users > /dev/null
  curl -s http://localhost:8000/api/orders -X POST \
    -H "Content-Type: application/json" \
    -d '{"order_id": "'$i'", "amount": 100, "product_id": "PROD-001"}' > /dev/null
  echo "Request $i sent"
  sleep 0.5
done
```

Now refresh Prometheus, Grafana, and Loki to see the increased metrics and logs!

## Cleanup (When Done)

After testing, clean up the test application:

```bash
./cleanup.sh
```

Or manually:
```bash
kubectl delete -f grafana-dashboard-configmap.yaml
kubectl delete -f servicemonitor.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
kubectl delete -f app-configmap.yaml
```

**Important:** This only removes the test application. Your monitoring stack (Prometheus, Grafana, Loki) will continue running.

## What You Learned

After completing this test, you've seen:

**Prometheus Metrics**
- How to expose metrics in Prometheus format
- How ServiceMonitor discovers your application
- How to query metrics with PromQL

**Grafana Dashboards**
- How dashboards auto-discover with the right label
- Different panel types (graph, stat, table)
- How to use variables for filtering

**Loki Logs**
- How logs are automatically collected
- Benefits of structured JSON logging
- How to query and filter logs with LogQL

**Metric Naming Convention**
- All metrics follow `appname_metricname` pattern
- Counter metrics use `_total` suffix
- Histogram metrics use `_seconds` or `_bytes` suffix
- Gauge metrics have no suffix

## Next Steps

Now that you've tested the example:

1. **Review the code**: Check `app-configmap.yaml` to see the application code
2. **Integrate your app**: Follow the patterns from the example
3. **Read guides**: Check `README.md` for detailed explanations
