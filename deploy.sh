#!/bin/bash

set -e  
export ANSIBLE_HOST_KEY_CHECKING=False
export GOOGLE_APPLICATION_CREDENTIALS='/tmp/key-file.json'

echo "Starting Terraform apply..."
cd terraform
terraform init --upgrade
terraform destroy --auto-approve -lock=false
terraform apply --auto-approve -lock=false
echo "Terraform apply completed."

echo "Waiting for 60 seconds before starting Ansible playbook..."
sleep 60

echo "Starting Ansible playbook..."
ansible-playbook -i ../k8s_setup/inventory/hosts.yaml ../k8s_setup/playbook.yaml

