#!/bin/bash

set -e

echo "========================================="
echo "🧹 Cleaning up MyApp Test Application"
echo "========================================="

echo ""
echo "Deleting resources from monitoring namespace..."

# Delete in reverse order
echo ""
echo "1️⃣  Deleting Grafana dashboard..."
kubectl delete -f grafana-dashboard-configmap.yaml 2>/dev/null || echo "⚠️  Dashboard ConfigMap not found"

echo ""
echo "2️⃣  Deleting ServiceMonitor..."
kubectl delete -f servicemonitor.yaml 2>/dev/null || echo "⚠️  ServiceMonitor not found"

echo ""
echo "3️⃣  Deleting Service..."
kubectl delete -f service.yaml 2>/dev/null || echo "⚠️  Service not found"

echo ""
echo "4️⃣  Deleting Deployment..."
kubectl delete -f deployment.yaml 2>/dev/null || echo "⚠️  Deployment not found"

echo ""
echo "5️⃣  Deleting ConfigMap..."
kubectl delete -f app-configmap.yaml 2>/dev/null || echo "⚠️  ConfigMap not found"

# Wait for pods to terminate
echo ""
echo "⏳ Waiting for pods to terminate..."
kubectl wait --for=delete pod -l app=myapp -n monitoring --timeout=60s 2>/dev/null || true

echo ""
echo "========================================="
echo "✅ Cleanup Complete!"
echo "========================================="
echo ""
echo "Verification:"
kubectl get all -n monitoring -l app=myapp 2>/dev/null || echo "No resources found (as expected)"

echo ""
echo "The test application has been removed."
echo "Your monitoring stack (Prometheus, Grafana, Loki) is still running."
echo ""
