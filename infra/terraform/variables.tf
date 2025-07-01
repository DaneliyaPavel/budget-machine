variable "env" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "YC region/zone"
  type        = string
  default     = "ru-central1-a"
}

variable "cidr_block" {
  description = "CIDR block for VPC network"
  type        = string
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
