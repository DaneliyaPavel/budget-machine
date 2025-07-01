variable "env" {
  type = string
}

variable "region" {
  type = string
}

variable "cidr_block" {
  type = string
}

variable "tags" {
  type = map(string)
  default = {}
}

resource "yandex_vpc_network" "this" {
  name   = "${var.env}-vpc"
  labels = var.tags
}

resource "yandex_vpc_subnet" "this" {
  name           = "${var.env}-subnet"
  zone           = var.region
  network_id     = yandex_vpc_network.this.id
  v4_cidr_blocks = [var.cidr_block]
  labels         = var.tags
}

output "vpc_id" {
  value = yandex_vpc_network.this.id
}

output "subnet_ids" {
  value = [yandex_vpc_subnet.this.id]
}
