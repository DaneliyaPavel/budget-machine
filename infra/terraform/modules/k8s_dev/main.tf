variable "env" {
  type = string
}

variable "region" {
  type = string
}

variable "network_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "tags" {
  type = map(string)
  default = {}
}

resource "yandex_kubernetes_cluster" "this" {
  name       = "${var.env}-k8s"
  network_id = var.network_id

  master {
    version   = "1.27"
    public_ip = true
  }

  labels = var.tags
}

resource "yandex_kubernetes_node_group" "default" {
  cluster_id = yandex_kubernetes_cluster.this.id
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

  labels = var.tags
}

output "cluster_id" {
  value = yandex_kubernetes_cluster.this.id
}
