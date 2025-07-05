provider "google" {
  project = "${var.project_id}"
  region  = "${var.project_region}"
  zone    = "${var.project_zone}"
}

terraform {
 backend "gcs" {
   bucket  = "${var.bucket_name}"
   prefix  = "/"
 }
}

resource "google_cloud_run_service" "app_service" {
  name     = "${var.cloud_run_service_name}"
  location = "${var.project_region}"
  
  template {
    spec {
      containers {
        image = "${var.location}-docker.pkg.dev/${var.project_id}/${var.repo_name}/${var.image_name}:${var.image_tag}"
      }
    }
  }
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.app_service.location
  project     = "${var.project_id}"
  service     = google_cloud_run_service.app_service.name

  policy_data = data.google_iam_policy.noauth.policy_data
}