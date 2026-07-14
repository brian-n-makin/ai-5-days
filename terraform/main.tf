terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.50.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# -------------------------------------------------------------
# 1. Google Artifact Registry: Store Docker Container Images
# -------------------------------------------------------------
resource "google_artifact_registry_repository" "tutor_agent_repo" {
  location      = var.region
  repository_id = "tutor-agent-repo"
  description   = "Docker repository for containerized Tutor Agent images"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }
}

# -------------------------------------------------------------
# 2. Google Secret Manager: Store GEMINI_API_KEY securely
# -------------------------------------------------------------
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  
  replication {
    automatic = true
  }
}

# -------------------------------------------------------------
# 3. Google Cloud Run Service: Host the Tutor Agent backend
# -------------------------------------------------------------
resource "google_cloud_run_v2_service" "tutor_agent_service" {
  name     = "tutor-agent-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/tutor-agent-repo/tutor-agent:latest"

      # Reference GEMINI_API_KEY securely from Secret Manager
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
    }
  }

  depends_on = [
    google_artifact_registry_repository.tutor_agent_repo,
    google_secret_manager_secret.gemini_api_key
  ]
}

# -------------------------------------------------------------
# 4. IAM Permissions: Grant Cloud Run Access to Secret Manager
# -------------------------------------------------------------
# Get the default Compute Engine service account used by Cloud Run
data "google_compute_default_service_account" "default" {}

resource "google_secret_manager_secret_iam_member" "cloud_run_secret_accessor" {
  secret_id = google_secret_manager_secret.gemini_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_compute_default_service_account.default.email}"
}
