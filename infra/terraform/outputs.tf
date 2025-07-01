output "vpc_id" {
  value = module.network.vpc_id
}

output "subnet_ids" {
  value = module.network.subnet_ids
}

output "cluster_id" {
  value = module.k8s_dev.cluster_id
}
