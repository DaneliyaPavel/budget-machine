variable "yc_token" {
  description = "Yandex Cloud OAuth token"
  type        = string
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud folder ID"
  type        = string
}

variable "yc_zone" {
  description = "Zone where resources will be created"
  type        = string
  default     = "ru-central1-a"
}

variable "yc_network_id" {
  description = "ID of the network used for the cluster"
  type        = string
}
