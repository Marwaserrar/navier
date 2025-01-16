output "cluster_yaml" {
  value = templatefile("hosts.yaml.tmpl", {
    instance_ips = {
      node1 = google_compute_instance.k8s_nodes[0].network_interface[0].access_config[0].nat_ip
      node2 = google_compute_instance.k8s_nodes[1].network_interface[0].access_config[0].nat_ip
      node3 = google_compute_instance.k8s_nodes[2].network_interface[0].access_config[0].nat_ip
    }
  })
}

resource "local_file" "cluster_yaml" {
  content  = templatefile("hosts.yaml.tmpl", {
    instance_ips = {
      node1 = google_compute_instance.k8s_nodes[0].network_interface[0].access_config[0].nat_ip
      node2 = google_compute_instance.k8s_nodes[1].network_interface[0].access_config[0].nat_ip
      node3 = google_compute_instance.k8s_nodes[2].network_interface[0].access_config[0].nat_ip
    }
  })
  filename = "../k8s_setup/inventory/hosts.yaml"
}
