# Deployment Guide

This document describes how to provision infrastructure and deploy the application using Terraform, Helm and Argo CD.

## Infrastructure with Terraform

The `deploy/terraform` directory contains an example configuration for Yandex Cloud. It provisions a managed Kubernetes cluster and a node group.

```bash
cd deploy/terraform
terraform init
terraform apply
```

Set the variables `yc_token`, `yc_cloud_id`, `yc_folder_id`, `yc_network_id` and optionally `yc_zone` to match your account.

## Application deployment with Helm

A Helm chart lives in `deploy/helm`. After obtaining kubeconfig for the cluster, install the chart:

```bash
helm install budget-machine ./deploy/helm \
  --set env.DATABASE_URL=postgresql://user:pass@db:5432/budget \
  --set env.SECRET_KEY=change_me
```

It will create a Deployment, Service and a Rollout resource for canary releases.

## Argo CD

The directory `deploy/argocd` provides manifests for Argo CD.

- `applicationset.yaml` creates preview environments for pull requests using `ApplicationSet`.
- `rollout-example.yaml` demonstrates how to sync the chart with automated canary rollouts.

Apply them to a running Argo CD instance:

```bash
kubectl apply -f deploy/argocd/
```

After that new pull requests will trigger temporary environments and production updates will use Argo Rollouts for gradual rollout.
