#!/bin/bash

set -e  
export ANSIBLE_HOST_KEY_CHECKING=False
export GOOGLE_APPLICATION_CREDENTIALS='/tmp/key-file.json'

echo "Starting Terraform apply..."
cd terraform
terraform init 
terraform destroy --auto-approve
terraform apply --auto-approve

echo "Terraform apply completed."

# Add a 15-second delay
echo "Waiting for 15 seconds before starting Ansible playbook..."
sleep 15

echo "Starting Ansible playbook..."
ansible-playbook -i ../k8s_setup/inventory/hosts.yaml ../k8s_setup/playbook.yaml

