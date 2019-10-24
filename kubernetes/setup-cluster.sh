#!/bin/sh
gcloud container clusters create bernd-zeebe-benchmark \
  --region europe-west1-b \
  --num-nodes=1 \
  --enable-autoscaling --max-nodes=32 --min-nodes=1 \
  --machine-type=n1-standard-8 \
  --maintenance-window=1:00

kubectl apply -f k8s-tiller-rbac-config.yaml
kubectl apply -f k8s-zeebe-benchmark-role-binding.yaml

helm init --service-account tiller --wait
until helm install --name metrics stable/prometheus-operator -f helm-values-prometheus-chart.yaml | grep -m 1 "The Prometheus Operator has been installed"
do
	printf .
	sleep 1
done

kubectl apply -f k8s-grafana.yaml
kubectl apply -f k8s-ssd-storageclass.yaml
kubectl apply -f k8s-service-monitor.yaml