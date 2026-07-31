output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "rds_endpoint" {
  value = aws_db_instance.service_tickets.endpoint
}

output "s3_bucket_name" {
  value = aws_s3_bucket.service_ticket_data.bucket
}

output "ecr_repository_urls" {
  value = {
    for name, repository in aws_ecr_repository.service_ticket :
    name => repository.repository_url
  }
}