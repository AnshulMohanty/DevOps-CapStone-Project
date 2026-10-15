terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # The EKS module 20.x supports AWS provider 5.x only.
      version = "~> 5.95"
    }
  }

  # State stays on this machine for the short demo window (git-ignored).
  # A team would use: backend "s3" { bucket = "...", key = "foundit/terraform.tfstate", use_lockfile = true }
}
