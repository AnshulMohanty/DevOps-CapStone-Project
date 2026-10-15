# Credentials come from the normal AWS chain (`aws configure`, AWS_PROFILE or env vars) -
# never from this repository.
provider "aws" {
  region = var.aws_region

  # Every resource gets these tags, so the whole project can be found (and its cost seen) in one filter.
  default_tags {
    tags = {
      Project     = "foundit"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
