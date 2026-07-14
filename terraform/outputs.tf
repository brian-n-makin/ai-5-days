output "artifact_registry_repo_url" {
  value       = google_artifact_registry_repository.tutor_agent_repo.id
  description = "The fully qualified path to the generated Artifact Registry Docker repository."
}

output "cloud_run_service_url" {
  value       = google_cloud_run_v2_service.tutor_agent_service.uri
  description = "The public HTTPS endpoint URL of the deployed Cloud Run Tutor Agent service."
}
