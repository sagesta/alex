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

variable "create_load_balancer" {
  type        = bool
  description = "Create a global HTTP(S) load balancer: GCS → default, /api/* → Cloud Run portfolio API (see cloud_run_api_service_name)"
  default     = false

  validation {
    condition = (
      !var.create_load_balancer ||
      (var.create_frontend_bucket && var.cloud_run_api_service_name != "")
    )
    error_message = "When create_load_balancer is true, create_frontend_bucket must be true and cloud_run_api_service_name must be set (deploy backend/api to Cloud Run in var.region first)."
  }
}

variable "cloud_run_api_service_name" {
  type        = string
  description = "Existing Cloud Run service name for backend/api in var.region (e.g. alex-api). Required when create_load_balancer is true."
  default     = ""
}

variable "load_balancer_domain" {
  type        = string
  description = "Optional FQDN for managed SSL (e.g. app.example.com). Leave empty for HTTP-only on the LB IP. Point DNS A/AAAA at load_balancer_ip before enabling HTTPS."
  default     = ""
}
