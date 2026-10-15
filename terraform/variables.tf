variable "aws_region" {
  description = "AWS region for the VPC and the EKS cluster"
  type        = string
  default     = "ap-south-1"
}

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
  default     = "foundit-eks"
}

variable "cluster_version" {
  description = "Kubernetes version of the EKS control plane (check: aws eks describe-cluster-versions)"
  type        = string
  default     = "1.34"
}

variable "environment" {
  description = "Environment tag added to every resource"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Address range of the VPC"
  type        = string
  default     = "10.30.0.0/16"
}

# No default on purpose: whoever applies this must decide who may reach the Kubernetes API.
variable "api_allowed_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint - your own IP as x.x.x.x/32"
  type        = list(string)

  validation {
    condition     = !contains(var.api_allowed_cidrs, "0.0.0.0/0")
    error_message = "Do not open the Kubernetes API to the whole internet - use your own IP (x.x.x.x/32)."
  }
}

variable "node_instance_type" {
  description = "EC2 instance type of the worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "node_count" {
  description = "Number of worker nodes (desired = min)"
  type        = number
  default     = 2

  validation {
    condition     = var.node_count >= 1 && var.node_count <= 4
    error_message = "node_count must be between 1 and 4 - this is a short-lived demo cluster."
  }
}
