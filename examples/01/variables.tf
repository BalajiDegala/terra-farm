variable "project_name" {
  description = "Project label used in resource names; uppercase and underscores are normalized."
  type        = string
  default     = "terraform-lab"
  nullable    = false

  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9_-]{2,23}$", var.project_name))
    error_message = "Use 3-24 letters, digits, underscores, or hyphens, starting with a letter."
  }
}

variable "environment" {
  description = "Naming and tagging label within Floci; even prod remains a local lab."
  type        = string
  default     = "dev"
  nullable    = false

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "Environment must be dev, test, or prod. All environments run locally."
  }
}

variable "aws_region" {
  description = "Region namespace used by the local emulator. Use the same region in AWS CLI commands."
  type        = string
  default     = "us-east-1"
  nullable    = false

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z]+)+-[0-9]+$", var.aws_region))
    error_message = "Use an AWS region name such as us-east-1."
  }
}

variable "floci_endpoint" {
  description = "Local Floci HTTP endpoint; restricted to the loopback listener in compose.yaml."
  type        = string
  default     = "http://localhost:4566"
  nullable    = false

  validation {
    condition = contains([
      "http://localhost:4566",
      "http://127.0.0.1:4566",
    ], var.floci_endpoint)
    error_message = "Use http://localhost:4566 or http://127.0.0.1:4566. Remote endpoints are not permitted in this lab."
  }
}

variable "common_tags" {
  description = "Additional tags. Project, Environment, and ManagedBy are set by the lab and take precedence."
  type        = map(string)
  default     = {}
  nullable    = false
}
