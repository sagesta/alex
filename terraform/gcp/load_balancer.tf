# Global external HTTP load balancer:
# - Default → GCS frontend bucket (Next static export)
# - /api and /api/* → Cloud Run portfolio API (serverless NEG)
#
# Prerequisite: Cloud Run service `var.cloud_run_api_service_name` must exist in `var.region`
# (deploy backend/api image first). Same host fixes relative /api/* when users open the site via the LB URL.

locals {
  lb_enabled = (
    var.create_load_balancer &&
    var.create_frontend_bucket &&
    var.cloud_run_api_service_name != ""
  )
  lb_https_enabled = local.lb_enabled && var.load_balancer_domain != ""
}

resource "google_compute_global_address" "lb" {
  count   = local.lb_enabled ? 1 : 0
  name    = "${var.app_name}-lb-ip"
  project = var.project_id
}

resource "google_compute_region_network_endpoint_group" "api_neg" {
  count = local.lb_enabled ? 1 : 0

  name                  = "${var.app_name}-api-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id

  cloud_run {
    service = var.cloud_run_api_service_name
  }
}

resource "google_compute_backend_service" "api" {
  count = local.lb_enabled ? 1 : 0

  name                  = "${var.app_name}-api-backend"
  project               = var.project_id
  protocol              = "HTTP"
  load_balancing_scheme = "EXTERNAL"
  timeout_sec           = 30

  backend {
    group = google_compute_region_network_endpoint_group.api_neg[0].id
  }
}

resource "google_compute_backend_bucket" "lb_static" {
  count = local.lb_enabled ? 1 : 0

  name        = "${var.app_name}-frontend-lb-bucket"
  bucket_name = google_storage_bucket.frontend[0].name
  enable_cdn  = true

  cdn_policy {
    cache_mode                   = "CACHE_ALL_STATIC"
    default_ttl                  = 3600
    max_ttl                      = 86400
    client_ttl                   = 3600
    negative_caching  = true
    serve_while_stale = 86400
  }
}

resource "google_compute_url_map" "lb" {
  count = local.lb_enabled ? 1 : 0

  name            = "${var.app_name}-lb-url-map"
  project         = var.project_id
  default_service = google_compute_backend_bucket.lb_static[0].id

  host_rule {
    hosts        = ["*"]
    path_matcher = "paths"
  }

  path_matcher {
    name            = "paths"
    default_service = google_compute_backend_bucket.lb_static[0].id

    path_rule {
      paths   = ["/api", "/api/*"]
      service = google_compute_backend_service.api[0].id
    }
  }
}

resource "google_compute_target_http_proxy" "http" {
  count = local.lb_enabled ? 1 : 0

  name    = "${var.app_name}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.lb[0].id
}

resource "google_compute_global_forwarding_rule" "http" {
  count = local.lb_enabled ? 1 : 0

  name                  = "${var.app_name}-http-forwarding-rule"
  project               = var.project_id
  target                = google_compute_target_http_proxy.http[0].id
  port_range            = "80"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.lb[0].self_link
  ip_protocol           = "TCP"
}

# Optional HTTPS (set load_balancer_domain). Create an A/AAAA record for the domain → load_balancer_ip first;
# managed certs may stay PROVISIONING until DNS propagates.

resource "google_compute_managed_ssl_certificate" "lb" {
  count = local.lb_https_enabled ? 1 : 0

  name = "${var.app_name}-lb-cert"
  managed {
    domains = [var.load_balancer_domain]
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "google_compute_target_https_proxy" "https" {
  count = local.lb_https_enabled ? 1 : 0

  name             = "${var.app_name}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.lb[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.lb[0].id]
}

resource "google_compute_global_forwarding_rule" "https" {
  count = local.lb_https_enabled ? 1 : 0

  name                  = "${var.app_name}-https-forwarding-rule"
  project               = var.project_id
  target                = google_compute_target_https_proxy.https[0].id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL"
  ip_address            = google_compute_global_address.lb[0].self_link
  ip_protocol           = "TCP"
}
