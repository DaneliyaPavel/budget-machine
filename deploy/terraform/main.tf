terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.91"
    }
  }
  required_version = ">= 1.6"
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

resource "yandex_kubernetes_cluster" "k8s" {
  name      = "budget-machine"
  network_id = var.yc_network_id

  master {
    version   = "1.27"
    public_ip = true
  }
}

resource "yandex_kubernetes_node_group" "default" {
  cluster_id = yandex_kubernetes_cluster.k8s.id
  version    = "1.27"
  name       = "default"

  scale_policy {
    fixed_scale {
      size = 2
    }
  }

  instance_template {
    platform_id = "standard-v3"
    resources {
      cores  = 2
      memory = 4
    }
    boot_disk {
      type = "network-hdd"
      size = 64
    }
  }
}
