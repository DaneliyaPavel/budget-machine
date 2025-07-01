terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = ">= 0.91"
    }
  }

  backend "s3" {
    endpoint = "storage.yandexcloud.net"
    bucket   = "tf-state"
    region   = var.region
    key      = "${var.env}/terraform.tfstate"
  }
}

provider "yandex" {
  zone = var.region
}

module "network" {
  source     = "./modules/network"
  env        = var.env
  region     = var.region
  cidr_block = var.cidr_block
  tags       = var.tags
}

module "k8s_dev" {
  source     = "./modules/k8s_dev"
  env        = var.env
  region     = var.region
  network_id = module.network.vpc_id
  subnet_ids = module.network.subnet_ids
  tags       = var.tags
}
