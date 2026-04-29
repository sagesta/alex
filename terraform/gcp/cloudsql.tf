resource "random_password" "db" {
  length  = 24
  special = false
}

resource "google_sql_database_instance" "alex" {
  name                = "${var.app_name}-postgres"
  database_version    = "POSTGRES_15"
  region              = var.region
  deletion_protection = false

  settings {
    tier              = var.db_tier
    disk_size         = var.db_disk_size_gb
    availability_type = "ZONAL"

    ip_configuration {
      ipv4_enabled = true
      # For production, prefer private IP + VPC connector; this enables quick Cloud SQL Auth Proxy / public IP access from allowed clients.
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }

  depends_on = [google_project_service.apis]
}

resource "google_sql_database" "alex" {
  name     = "alex"
  instance = google_sql_database_instance.alex.name
}

resource "google_sql_user" "alex" {
  name     = "alexadmin"
  instance = google_sql_database_instance.alex.name
  password = random_password.db.result
}

resource "google_secret_manager_secret" "db_url" {
  secret_id = "${var.app_name}-database-url"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "db_url" {
  secret = google_secret_manager_secret.db_url.id

  secret_data = format(
    "postgresql://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.alex.name,
    random_password.db.result,
    google_sql_database.alex.name,
    google_sql_database_instance.alex.connection_name,
  )
}
