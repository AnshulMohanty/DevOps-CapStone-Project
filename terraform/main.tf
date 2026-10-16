data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# ---------------------------------------------------------------- network
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.8.1"

  name = "${var.cluster_name}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  # 2 AZs x (public + private). Nodes live in the private subnets; load balancers in the public ones.
  private_subnets = [cidrsubnet(var.vpc_cidr, 8, 1), cidrsubnet(var.vpc_cidr, 8, 2)]
  public_subnets  = [cidrsubnet(var.vpc_cidr, 8, 101), cidrsubnet(var.vpc_cidr, 8, 102)]

  # Private nodes reach the internet (image pulls from GHCR) through ONE NAT gateway.
  # One per AZ would survive an AZ outage but doubles the most expensive part of this VPC.
  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  # Tags Kubernetes uses to pick subnets for internet-facing / internal load balancers.
  public_subnet_tags  = { "kubernetes.io/role/elb" = 1 }
  private_subnet_tags = { "kubernetes.io/role/internal-elb" = 1 }
}

# ---------------------------------------------------------------- cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "20.37.1"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # The API endpoint is public so kubectl works from my laptop - but only from the CIDRs in
  # api_allowed_cidrs (set to my own IP in terraform.tfvars). The nodes stay private.
  cluster_endpoint_public_access           = true
  cluster_endpoint_public_access_cidrs     = var.api_allowed_cidrs
  enable_cluster_creator_admin_permissions = true

  cluster_addons = {
    coredns    = { most_recent = true }
    kube-proxy = { most_recent = true }
    vpc-cni    = { most_recent = true, before_compute = true }
    # Without the EBS CSI driver a PersistentVolumeClaim (the Postgres volume) stays Pending.
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
      # EKS >= 1.30 ships no default StorageClass; let the addon create a gp3 one and mark it default.
      configuration_values = jsonencode({ defaultStorageClass = { enabled = true } })
    }
    # Feeds CPU numbers to the HorizontalPodAutoscaler.
    metrics-server = { most_recent = true }
  }

  eks_managed_node_groups = {
    main = {
      instance_types = [var.node_instance_type]
      capacity_type  = "ON_DEMAND"
      min_size       = var.node_count
      desired_size   = var.node_count
      max_size       = var.node_count + 1
      disk_size      = 20
    }
  }
}

# IAM role for the EBS CSI driver's service account (IRSA): only that one pod may create/attach volumes,
# instead of giving the permission to every node.
module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "5.55.0"

  role_name             = "${var.cluster_name}-ebs-csi"
  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }
}
