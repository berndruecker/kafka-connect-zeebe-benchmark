# Overview

## Configure gcloud and kubernetes

https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl

```
gcloud auth login
gcloud config set project camunda-consulting-de
```

## Create and init new cluster

```
./setup-cluster.sh
```

This does

* Setup the cluster
* Setup Tiller Service Account
* Init helm
* Install Prometheus Operator
* Setup Grafana
* Setup SSD Storage class


## Install Kafka (via Helm)

See https://github.com/confluentinc/cp-helm-charts/tree/master/charts/cp-kafka

Adjust `kafka-connect-values.yaml` if you want to change certain configurations (e.g. number of broker nodes, replication factor, ...).

Note that this configures kafka-connect to use the image `berndruecker/kafka-connect-zeebe`, which includes all libraries for kafka-connect-zeebe

```
git clone https://github.com/confluentinc/cp-helm-charts.git
helm install -f helm-values-kafka-connect.yaml --name kafka cp-helm-charts
```

## Install Zeebe (via Helm)

Adjust the parameters in `helm-values-zeebe.yaml` and then

```
helm repo add zeebe https://helm.zeebe.io
helm repo update
helm install -f helm-values-zeebe.yaml --name zeebe zeebe/zeebe-cluster
```

And if you want to have Operate as well

```
helm install --name zeebe-operate zeebe/zeebe-operate --set global.zeebe=zeebe
```

## Forward ports


```
kubectl port-forward svc/zeebe-zeebe-cluster 26500:26500 & kubectl port-forward svc/kafka-cp-kafka-connect 8083:8083 & kubectl port-forward svc/kafka-cp-kafka 9092:9092 & kubectl port-forward svc/kafka-cp-control-center 9021:9021 & kubectl port-forward svc/zeebe-operate 8080:8080
```

## Run benchmark

see [Readme on root level](../)