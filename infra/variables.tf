variable "project_id" {
  type        = string
  description = "Project ID"
  default     = ""
}

variable "repo_name" {
  type        = string
  description = "Artifact Registry repo name"
  default     = ""
}

variable "location" {
  type        = string
  description = "Artifact Registry repo location"
  default     = ""
}

variable "image_name" {
  type        = string
  description = "Docker Image name"
  default     = ""
}

variable "image_tag" {
  type = string
  default = "latest"
}

variable "cloud_run_service_name" {
  type        = string
  description = "Cloud Run service name"
  default     = ""
}

variable "bucket_name" {
  type        = string
  description = "GCS bucket name for Terraform state"
  default     = ""
  
}

variable "project_name" {
  type        = string
  description = "Project name"
  default     = ""
}

variable "project_region" {
  type        = string
  description = "Project location"
  default     = "us-central1"
  
}

variable "project_zone" {
  type        = string
  description = "Project zone"
  default     = "us-central1-a"
  
}