# Service account + IAM for GitHub Actions to run Terraform against this project (demo JSON key flow).
# First apply uses your user credentials; then add the key output to GitHub secret GCP_SA_KEY.

locals {
  github_actions_sa_roles = [
    "roles/serviceusage.serviceUsageAdmin",
    "roles/artifactregistry.admin",
    "roles/cloudsql.admin",
    "roles/storage.admin",
    "roles/secretmanager.admin",
    "roles/pubsub.admin",
    "roles/run.admin", # Cloud Run deploy from GitHub Actions
  ]
}

resource "google_service_account" "github_actions" {
  count = var.create_github_actions_sa ? 1 : 0

  project      = var.project_id
  account_id   = "${var.app_name}-gha-tf"
  display_name = "GitHub Actions Terraform (${var.app_name})"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "github_actions" {
  for_each = var.create_github_actions_sa ? toset(local.github_actions_sa_roles) : toset([])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions[0].email}"
}

resource "google_service_account_key" "github_actions" {
  count = var.create_github_actions_sa && var.create_github_actions_key ? 1 : 0

  service_account_id = google_service_account.github_actions[0].name
}
