#!/bin/bash
set -e

echo "Downloading and installing istioctl..."
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

echo "Installing Istio onto the cluster using the demo profile..."
istioctl install --set profile=demo -y

echo "Labeling the default namespace for automatic sidecar injection..."
kubectl label namespace default istio-injection=enabled --overwrite

echo "Istio installation and namespace labeling complete."
