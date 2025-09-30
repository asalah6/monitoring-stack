# Grafana VirtualService Configuration

This directory contains the Istio VirtualService configuration to expose Grafana at https://monitoring.rc.ds.wt.de

## Overview

The VirtualService routes external HTTPS traffic through the Istio ingress gateway to the Grafana service running in the `monitoring` namespace.

## Architecture

```
Internet (HTTPS)
    ↓
https://monitoring.rc.ds.wt.de
    ↓
Istio Ingress Gateway (knative-serving/knative-ingress-gateway)
    ↓
VirtualService (monitoring/grafana-monitoring)
    ↓
Grafana Service (grafana.monitoring.svc.cluster.local:80)
    ↓
Grafana Pod (port 3000)
```

## Deployment

### Apply the VirtualService

```bash
kubectl apply -f grafana-virtualservice.yaml
```

### Verify the VirtualService

```bash
# Check if VirtualService is created
kubectl get virtualservice -n monitoring

# Describe the VirtualService
kubectl describe virtualservice grafana-monitoring -n monitoring

# Check ingress gateway
kubectl get svc -n istio-system istio-ingressgateway
```

## Access Grafana

Once deployed, Grafana will be accessible at:

**URL**: https://monitoring.rc.ds.wt.de

**Credentials**:
- Username: `admin`
- Password: `admin123` (change this in production!)

## DNS Configuration

Ensure that the DNS record for `monitoring.rc.ds.wt.de` points to the Istio ingress gateway's external IP or the cluster load balancer.

To find the ingress gateway address:

```bash
kubectl get svc -n istio-system istio-ingressgateway
```

## SSL/TLS Certificate

The Istio ingress gateway should be configured with the wildcard SSL certificate for `*.rc.ds.wt.de` to handle HTTPS termination.

Check the gateway configuration:

```bash
kubectl get gateway -n knative-serving knative-ingress-gateway -o yaml
```

## Troubleshooting

### VirtualService not working

1. **Check VirtualService status**:
   ```bash
   kubectl get virtualservice -n monitoring grafana-monitoring -o yaml
   ```

2. **Check Grafana service**:
   ```bash
   kubectl get svc -n monitoring grafana
   ```

3. **Check Grafana pod**:
   ```bash
   kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana
   kubectl logs -n monitoring -l app.kubernetes.io/name=grafana
   ```

4. **Test internal connectivity**:
   ```bash
   # Port-forward to test Grafana directly
   kubectl port-forward -n monitoring svc/grafana 3000:80
   # Then access http://localhost:3000
   ```

5. **Check Istio configuration**:
   ```bash
   # Verify the gateway exists
   kubectl get gateway -n knative-serving
   
   # Check for Istio configuration errors
   istioctl analyze -n monitoring
   ```

### 404 or 503 Errors

- **404**: VirtualService routing might be incorrect
- **503**: Backend service (Grafana) might be down or not ready

Check the Grafana service endpoints:
```bash
kubectl get endpoints -n monitoring grafana
```

### SSL/TLS Issues

If you get certificate errors:

1. Verify the gateway has the correct TLS configuration
2. Check that the wildcard certificate includes `*.rc.ds.wt.de`
3. Ensure the certificate is not expired

## Testing

### Test from within the cluster

```bash
# Create a test pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- sh

# Inside the pod, test the service
curl -v http://grafana.monitoring.svc.cluster.local
```

### Test from outside the cluster

```bash
# Test the external URL
curl -v https://monitoring.rc.ds.wt.de

# Check DNS resolution
nslookup monitoring.rc.ds.wt.de
```

## Configuration Details

**Gateway**: `knative-serving/knative-ingress-gateway`
- This is the shared Istio ingress gateway used by other services in the cluster
- Handles HTTPS termination with the wildcard certificate

**Host**: `monitoring.rc.ds.wt.de`
- External DNS name for accessing Grafana
- Must resolve to the ingress gateway IP

**Destination**: `grafana.monitoring.svc.cluster.local:80`
- Internal Kubernetes service for Grafana
- Service listens on port 80, forwards to pod port 3000

## Security Considerations

1. **Change default password**: The default admin password `admin123` should be changed immediately in production
2. **Enable RBAC**: Configure Grafana authentication and authorization
3. **Network policies**: Consider implementing network policies to restrict access to Grafana
4. **Rate limiting**: Add rate limiting to prevent abuse

## Related Resources

- Prometheus: http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090
- Alertmanager: http://prometheus-alertmanager.monitoring.svc.cluster.local:9093
- Loki: http://loki-gateway.monitoring.svc.cluster.local

## Updating the Configuration

To modify the VirtualService:

1. Edit the `grafana-virtualservice.yaml` file
2. Apply the changes:
   ```bash
   kubectl apply -f grafana-virtualservice.yaml
   ```
3. Verify the changes:
   ```bash
   kubectl get virtualservice grafana-monitoring -n monitoring -o yaml
   ```

Changes to the VirtualService take effect immediately without restarting Grafana.
