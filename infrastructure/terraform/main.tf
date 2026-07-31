provider "aws" {
  region = "us-east-1"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "ticket_classification_vpc"
  cidr = "10.0.0.0/16"

  azs              = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnets   = ["10.0.102.0/24", "10.0.103.0/24", "10.0.104.0/24"]
  private_subnets  = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  database_subnets = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

  enable_nat_gateway           = true
  single_nat_gateway           = true
  map_public_ip_on_launch      = true
  create_database_subnet_group = false
  enable_dns_support           = true
  enable_dns_hostnames         = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "service_ticket_data" {
  bucket = "service-ticket-data-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

resource "aws_s3_bucket_versioning" "service_ticket_data" {
  bucket = aws_s3_bucket.service_ticket_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "service_ticket_data" {
  bucket = aws_s3_bucket.service_ticket_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

locals {
  ecr_repositories = toset([
    "api",
    "frontend",
    "train",
    "insert",
    "retrain"
  ])
}

resource "aws_ecr_repository" "service_ticket" {
  for_each = local.ecr_repositories

  name                 = "service-ticket-${each.key}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "service_ticket" {
  for_each = aws_ecr_repository.service_ticket

  repository = each.value.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"

        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }

        action = {
          type = "expire"
        }
      }
    ]
  })
}
resource "aws_db_subnet_group" "service_ticket" {
  name       = "service-ticket-db-subnet"
  subnet_ids = module.vpc.database_subnets

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

resource "aws_security_group" "rds" {
  name        = "service-ticket-rds"
  description = "PostgreSQL access from EKS"
  vpc_id      = module.vpc.vpc_id
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_vpc" {
  security_group_id = aws_security_group.rds.id

  cidr_ipv4   = module.vpc.vpc_cidr_block
  from_port   = 5432
  to_port     = 5432
  ip_protocol = "tcp"
}

resource "aws_db_instance" "service_tickets" {
  identifier = "service-tickets"

  engine         = "postgres"
  engine_version = "16"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "service_tickets"
  username = "technician"
  password = var.db_password

  db_subnet_group_name = aws_db_subnet_group.service_ticket.name

  vpc_security_group_ids = [
    aws_security_group.rds.id
  ]

  publicly_accessible = false

  backup_retention_period = 1

  skip_final_snapshot = true
  deletion_protection = false

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = "service-ticket-cluster"
  kubernetes_version = "1.35"

  endpoint_private_access = true
  endpoint_public_access  = true

  endpoint_public_access_cidrs = [
    "${var.admin_public_ip}/32",
    "${var.runner_public_ip}/32"
  ]

  enable_cluster_creator_admin_permissions = true

  compute_config = {
    enabled    = true
    node_pools = ["general-purpose"]
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

    access_entries = {
      github_runner = {
        principal_arn = "arn:aws:iam::835577334660:role/secure_ci_ec2_role"

        policy_associations = {
          cluster_admin = {
            policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

            access_scope = {
              type = "cluster"
            }
          }
        }
      }
    }

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

resource "aws_iam_role" "api_pod_role" {
  name = "api-pod-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEksPodIdentity"
        Effect = "Allow"
        Principal = {
          Service = "pods.eks.amazonaws.com"
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

resource "aws_iam_policy" "api_s3_policy" {
  name        = "service-ticket-api-s3-policy"
  description = "Allows the api pod to download the ml model"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "ReadProductionModel"
        Effect = "Allow"

        Action = [
          "s3:GetObject"
        ]

        Resource = "${aws_s3_bucket.service_ticket_data.arn}/models/production/ticket-classifier.joblib"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_s3_policy_attachment" {
  role       = aws_iam_role.api_pod_role.name
  policy_arn = aws_iam_policy.api_s3_policy.arn
}

resource "aws_eks_pod_identity_association" "api" {
  cluster_name = module.eks.cluster_name

  namespace       = "service-ticket"
  service_account = "service-ticket-api"

  role_arn = aws_iam_role.api_pod_role.arn
}

resource "aws_iam_role" "jobs_pod_role" {
  name = "jobs-pod-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowEksPodIdentity"
        Effect = "Allow"
        Principal = {
          Service = "pods.eks.amazonaws.com"
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })

  tags = {
    Project     = "ticket_classification_system"
    Environment = "dev"
    Owner       = "Mantavya"
  }
}

resource "aws_iam_policy" "jobs_s3_policy" {
  name        = "service-ticket-jobs-s3-policy"
  description = "Allows job pods to read, write and put objects in the s3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadWriteObjects"
        Effect = "Allow"

        Action = [
          "s3:GetObject",
          "s3:PutObject",
        ]

        Resource = "${aws_s3_bucket.service_ticket_data.arn}/*"
      },
      {
        Sid    = "ListBucket"
        Effect = "Allow"

        Action = [
          "s3:ListBucket"
        ]

        Resource = aws_s3_bucket.service_ticket_data.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "jobs_s3_policy_attachment" {
  role       = aws_iam_role.jobs_pod_role.name
  policy_arn = aws_iam_policy.jobs_s3_policy.arn
}

resource "aws_eks_pod_identity_association" "jobs" {
  cluster_name = module.eks.cluster_name

  namespace       = "service-ticket"
  service_account = "service-ticket-job"

  role_arn = aws_iam_role.jobs_pod_role.arn
}