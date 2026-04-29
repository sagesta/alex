# Static site hosting for Next.js `output: 'export'` (see frontend/next.config.ts).
# Public read for demo; tighten IAM for production.

resource "google_storage_bucket" "frontend" {
  count = var.create_frontend_bucket ? 1 : 0

  name                        = "${var.project_id}-${var.app_name}-site"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }

  depends_on = [google_project_service.apis]
}

resource "google_storage_bucket_iam_member" "frontend_public_read" {
  count  = var.create_frontend_bucket ? 1 : 0
  bucket = google_storage_bucket.frontend[0].name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
