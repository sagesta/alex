variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "Default region (e.g. us-central1)"
  default     = "us-central1"
}

variable "app_name" {
  type        = string
  description = "Prefix for resource names"
  default     = "alex"
}

variable "db_tier" {
  type        = string
  description = "Cloud SQL machine tier (cost vs capacity)"
  default     = "db-f1-micro"
}

variable "db_disk_size_gb" {
  type        = number
  description = "Allocated disk for Cloud SQL (GB)"
  default     = 10
}

variable "create_github_actions_sa" {
  type        = bool
  description = "Create a user-managed SA + IAM for GitHub Actions Terraform (demo)"
  default     = true
}

variable "create_github_actions_key" {
  type        = bool
  description = "Create a JSON key for the GitHub Actions SA (sensitive; stored in Terraform state)"
  default     = true
}

variable "create_frontend_bucket" {
  type        = bool
  description = "Create a public GCS bucket for static Next export (demo)"
  default     = true
}
