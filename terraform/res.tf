terraform {
   backend "gcs" {
    bucket = "bucket-marwa"
  }
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"  
         }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0" 
    }
  }
}


provider "google" {
  credentials = file("/tmp/key-file.json")
  project     = "silver-course-448318-r7"
  region      = "europe-west4"
}


resource "google_compute_network" "k8s_network" {
  name                    = "k8s-network"
  auto_create_subnetworks = false
}


resource "google_compute_subnetwork" "k8s_subnet" {
  name          = "k8s-subnet"
  ip_cidr_range = "10.0.0.0/16" 
  region        = "europe-west4"
  network       = google_compute_network.k8s_network.id
}


resource "google_compute_firewall" "k8s_firewall" {
  name    = "k8s-firewall"
  network = google_compute_network.k8s_network.name


  allow {
    protocol = "tcp"
    ports    = ["22", "6443", "2379-2380", "10250", "10251", "10252", "30000-32767", "80", "443","179","4789"]
              
  }

  allow {
    protocol = "icmp"
  }
  
  allow {
    protocol = "ipip"
  }


  source_ranges = ["0.0.0.0/0"]
}


resource "google_compute_instance" "k8s_nodes" {
  count        = 3
  name         = "k8s-node-${count.index + 1}"
  machine_type = "e2-standard-2"
  zone         = "europe-west4-b"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
      size  = 20 
      type  = "pd-ssd"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.k8s_subnet.name
    access_config {}
  }

  metadata = {
    ssh-keys = "asmae:${file("/tmp/.ssh/gcp_key.pub")}"
  }

  service_account {
  email  = "marwa-364@silver-course-448318-r7.iam.gserviceaccount.com"
  scopes = ["cloud-platform"] 
}

}


output "addresses" {
  value = [for instance in google_compute_instance.k8s_nodes : instance.network_interface[0].access_config[0].nat_ip]
}