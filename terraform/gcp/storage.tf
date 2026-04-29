resource "google_storage_bucket" "alex_vectors" {
  name                        = "${var.project_id}-${var.app_name}-vectors"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  depends_on = [google_project_service.apis]
}
