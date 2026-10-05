terraform {
  required_version = ">= 1.6.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = { source = "hashicorp/random", version = "~> 3.7" }
    local  = { source = "hashicorp/local", version = "~> 2.5" }
  }

  # Start with Terraform's default local backend. Remote state is a later lesson.
}
