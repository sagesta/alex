resource "google_artifact_registry_repository" "alex" {
  location      = var.region
  repository_id = "${var.app_name}-images"
  format        = "DOCKER"
  description   = "Alex container images (Cloud Run)"

  depends_on = [google_project_service.apis]
}
