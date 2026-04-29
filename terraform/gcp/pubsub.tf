resource "google_pubsub_topic" "analysis_jobs" {
  name = "${var.app_name}-analysis-jobs"

  depends_on = [google_project_service.apis]
}

resource "google_pubsub_topic" "analysis_jobs_dlq" {
  name = "${var.app_name}-analysis-jobs-dlq"

  depends_on = [google_project_service.apis]
}
