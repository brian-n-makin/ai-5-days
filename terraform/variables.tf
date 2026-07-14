variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID to provision resources in."
}

variable "region" {
  type        = string
  description = "The Google Cloud region to deploy the resources."
  default     = "us-central1"
}
