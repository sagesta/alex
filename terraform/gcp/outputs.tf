output "artifact_registry_url" {
  description = "Docker push URL prefix"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.alex.repository_id}"
}

output "gcs_vectors_bucket" {
  value = google_storage_bucket.alex_vectors.name
}

output "pubsub_analysis_topic" {
  value = google_pubsub_topic.analysis_jobs.name
}

output "cloud_sql_connection_name" {
  value = google_sql_database_instance.alex.connection_name
}

output "database_url_secret_id" {
  description = "Secret Manager secret id holding postgresql:// URI for Cloud Run / local proxy"
  value       = google_secret_manager_secret.db_url.secret_id
}

output "frontend_bucket_name" {
  description = "GCS bucket for Next static export; set GitHub Variable GCS_FRONTEND_BUCKET to this value"
  value       = var.create_frontend_bucket ? google_storage_bucket.frontend[0].name : null
}

output "frontend_public_url" {
  description = "Direct HTTPS URL to the exported site (demo)"
  value       = var.create_frontend_bucket ? "https://${google_storage_bucket.frontend[0].name}.storage.googleapis.com/index.html" : null
}

output "load_balancer_ip" {
  description = "Global LB IPv4 when create_load_balancer is true; create DNS A/AAAA for load_balancer_domain here"
  value = (
    var.create_load_balancer && var.create_frontend_bucket && var.cloud_run_api_service_name != ""
    ? google_compute_global_address.lb[0].address
    : null
  )
}

output "load_balancer_http_url" {
  description = "Open the app via the LB (not the raw bucket URL) so /api/* routes to Cloud Run. Use as site origin; set NEXT_PUBLIC_API_URL to \"\" for same-origin /api calls."
  value = (
    var.create_load_balancer && var.create_frontend_bucket && var.cloud_run_api_service_name != ""
    ? "http://${google_compute_global_address.lb[0].address}"
    : null
  )
}

output "load_balancer_https_url" {
  description = "https://<load_balancer_domain> when load_balancer_domain is set and cert is active"
  value = (
    var.create_load_balancer && var.create_frontend_bucket && var.cloud_run_api_service_name != "" && var.load_balancer_domain != ""
    ? "https://${var.load_balancer_domain}"
    : null
  )
}

output "cloud_run_researcher_service" {
  description = "Cloud Run service name used by docker-gcp workflow"
  value       = "${var.app_name}-researcher"
}

# --- GitHub Actions (demo JSON key) — see .github/workflows/terraform-gcp.yml

output "github_actions_service_account_email" {
  description = "Email of the SA used by GitHub Actions for Terraform (if create_github_actions_sa)"
  value       = var.create_github_actions_sa ? google_service_account.github_actions[0].email : null
}

output "github_actions_sa_key_base64" {
  description = <<-EOT
    Base64-encoded JSON key for the GitHub Actions SA (only if create_github_actions_key).
    Add to GitHub repository secret GCP_SA_KEY: decode with
    `terraform output -raw github_actions_sa_key_base64 | base64 -d` (Unix) or equivalent on Windows.
    Do not commit terraform.tfstate; it contains this material.
  EOT
  value = (
    var.create_github_actions_sa && var.create_github_actions_key
    ? google_service_account_key.github_actions[0].private_key
    : null
  )
  sensitive = true
}
