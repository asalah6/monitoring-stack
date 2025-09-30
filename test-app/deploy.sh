#!/bin/bash

set -e

echo "========================================="
echo "🚀 Deploying MyApp Test Application"
echo "========================================="

# Check if namespace exists
echo ""
echo "Checking namespace..."
if ! kubectl get namespace monitoring &> /dev/null; then
    echo "Creating monitoring namespace..."
    kubectl create namespace monitoring
else
    echo "✅ Namespace 'monitoring' exists"
fi

echo ""
echo "📦 No Docker image needed - using ConfigMap with Python alpine image!"
echo ""

# Deploy ConfigMap with application code
echo "1️⃣  Deploying application code (ConfigMap)..."
kubectl apply -f app-configmap.yaml
echo "✅ ConfigMap created"

# Deploy application
echo ""
echo "2️⃣  Deploying application..."
kubectl apply -f deployment.yaml
echo "✅ Deployment created"

# Deploy service
echo ""
echo "3️⃣  Creating service..."
kubectl apply -f service.yaml
echo "✅ Service created"

# Deploy ServiceMonitor
echo ""
echo "4️⃣  Creating ServiceMonitor for Prometheus..."
kubectl apply -f servicemonitor.yaml
echo "✅ ServiceMonitor created"

# Deploy Grafana dashboard
echo ""
echo "5️⃣  Creating Grafana dashboard..."
kubectl apply -f grafana-dashboard-configmap.yaml
echo "✅ Dashboard ConfigMap created"

# Wait for deployment to be ready
echo ""
echo "⏳ Waiting for pods to be ready (this may take 1-2 minutes for init container)..."
kubectl wait --for=condition=available --timeout=180s deployment/myapp -n monitoring

# Show status
echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "📊 Status:"
kubectl get pods -n monitoring -l app=myapp
echo ""
kubectl get svc -n monitoring myapp
echo ""
kubectl get servicemonitor -n monitoring myapp-servicemonitor
echo ""
kubectl get configmap -n monitoring myapp-dashboard

echo ""
echo "========================================="
echo "🔍 Verification Steps"
echo "========================================="
echo ""
echo "1️⃣  Test metrics endpoint locally:"
echo "   kubectl port-forward -n monitoring svc/myapp 8000:8000"
echo "   curl http://localhost:8000/metrics"
echo ""
echo "2️⃣  Check Prometheus targets:"
echo "   Open: https://monitoring.rc.ds.wt.de"
echo "   Go to: Status → Targets"
echo "   Look for: myapp (should be UP)"
echo ""
echo "3️⃣  Query metrics in Prometheus:"
echo "   myapp_http_requests_total"
echo "   myapp_request_duration_seconds"
echo "   myapp_active_connections"
echo ""
echo "4️⃣  View dashboard in Grafana:"
echo "   Open: https://monitoring.rc.ds.wt.de"
echo "   Login: admin / admin123"
echo "   Go to: Dashboards → 'MyApp Metrics Dashboard'"
echo ""
echo "5️⃣  Check logs in Loki:"
echo "   In Grafana: Explore → Loki"
echo "   Query: {namespace=\"monitoring\", app=\"myapp\"}"
echo ""
echo "========================================="
echo "🧹 Cleanup (when done testing)"
echo "========================================="
echo ""
echo "To delete the test application:"
echo "   ./cleanup.sh"
echo ""
echo "Or manually:"
echo "   kubectl delete -f deployment.yaml"
echo "   kubectl delete -f service.yaml"
echo "   kubectl delete -f servicemonitor.yaml"
echo "   kubectl delete -f grafana-dashboard-configmap.yaml"
echo "   kubectl delete -f app-configmap.yaml"
echo ""
