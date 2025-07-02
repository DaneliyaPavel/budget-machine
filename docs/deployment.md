# Руководство по развертыванию

Этот документ описывает, как создавать инфраструктуру и развёртывать приложение с помощью Terraform, Helm и Argo CD.

## Инфраструктура с Terraform

Каталог `infra/terraform` содержит пример конфигурации для Yandex Cloud. Он создаёт управляемый кластер Kubernetes и группу узлов.

```bash
cd infra/terraform
terraform init
terraform apply
```

Укажите значения переменных `yc_token`, `yc_cloud_id`, `yc_folder_id`, `yc_network_id` и при необходимости `yc_zone` в соответствии со своей учётной записью.

Для проверки конфигураций Terraform можно запускать `tfsec` или `terrascan`.

## Развёртывание приложения с Helm

В каталоге `infra/helm` находится Helm-чарт. Получив kubeconfig для кластера, установите чарт:

```bash
helm install budget-machine ./infra/helm \
  --set env.DATABASE_URL=postgresql://user:pass@db:5432/budget \
  --set env.SECRET_KEY=change_me
```

Чарт создаст Deployment, Service и ресурс Rollout для канареечных релизов.

## Argo CD

Каталог `infra/argocd` содержит манифесты для Argo CD.

- `applicationset.yaml` создаёт предварительные окружения для pull request'ов с помощью `ApplicationSet`.
- `rollout-example.yaml` демонстрирует синхронизацию чарта с автоматизированными канареечными rollout'ами.

Примените их к запущенному экземпляру Argo CD:

```bash
kubectl apply -f infra/argocd/
```

После этого новые pull request'ы будут запускать временные окружения, а обновления в продакшене будут использовать Argo Rollouts для плавного развёртывания.
