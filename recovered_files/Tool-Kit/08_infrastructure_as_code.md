# Infrastructure as Code (IaC)

Clicking around a cloud console to create servers and databases is fine for a weekend project. For a production system, it is a disaster. You cannot code-review clicks, you cannot version-control them, and you cannot reliably recreate them in a disaster recovery scenario.

Infrastructure as Code (IaC) allows you to define your infrastructure in text files.

## 1. Terraform (Declarative Provisioning)

Terraform is the industry standard for provisioning cloud resources (AWS, GCP, Azure). It is **declarative**: you write what you want to exist, and Terraform figures out the API calls to make it happen.

```arch
%% caption: Terraform calculates the difference between the Desired State (code) and the Actual State (cloud), storing the mapping in the State File.
route straight
node code "HCL Code\\n(Desired State)" at 0,0 icon=code color=blue
node tf "Terraform Engine" at 2,0 icon=package color=amber
node state "State File\\n(Current State)" at 2,1 icon=file color=slate
node cloud "AWS / GCP\\n(Actual Cloud)" at 4,0 icon=cloud color=green

code -> tf : "terraform apply"
state -> tf : "reads"
tf -> cloud : "makes API calls"
cloud -> state : "updates"
```

### Core Concepts

- **Providers**: Plugins that teach Terraform how to talk to a specific API (e.g., the AWS provider, the GitHub provider).
- **Resources**: The actual things you are creating.
  ```hcl
  resource "aws_s3_bucket" "my_bucket" {
    bucket = "my-company-data-123"
  }
  ```
- **State File (`terraform.tfstate`)**: A JSON file where Terraform remembers the mapping between the resources in your code and the actual IDs in the cloud. **Never store this in Git.** It contains secrets (like DB passwords) and causes race conditions if two developers run `apply` at the same time. Store it in an S3 bucket with DynamoDB locking (or use Terraform Cloud).
- **Modules**: Reusable packages of Terraform code. Instead of copying 50 lines to create a secure VPC every time, you call a module.
- **Drift**: When someone manually changes a resource in the AWS Console, the actual state has "drifted" from the code. Running `terraform plan` detects this drift, and `terraform apply` will forcefully revert the manual change to match the code.

## 2. Ansible (Imperative Configuration)

If Terraform is for *provisioning* the hardware (creating the EC2 instance), Ansible is for *configuring* the software on it (installing Nginx, tweaking Linux kernel parameters).

Ansible is agentless; it just needs SSH access and Python installed on the target machines.

### Core Concepts

- **Inventory**: A list of IP addresses or hostnames to target.
  ```ini
  [webservers]
  10.0.1.5
  10.0.1.6
  ```
- **Playbooks**: YAML files that describe the steps to execute. They run top-to-bottom (imperative).
  ```yaml
  - name: Configure Webservers
    hosts: webservers
    become: yes # Run as sudo
    tasks:
      - name: Install Nginx
        apt:
          name: nginx
          state: present
      - name: Start Nginx
        service:
          name: nginx
          state: started
  ```
- **Roles**: A way to structure complex playbooks into reusable folders (tasks, handlers, templates, variables).
- **Idempotency**: Good Ansible modules are idempotent. If you run the playbook above 10 times, it only installs Nginx the first time. The next 9 times, it sees Nginx is already `present` and does nothing.

## 3. The Modern Synthesis

With the rise of containers, Ansible's role has shrunk. Instead of booting an empty VM and using Ansible to carefully install dependencies and configure the app, we build a Docker image containing everything, push it to a registry, and use Terraform to deploy the container to Kubernetes or AWS ECS. 

**Immutable Infrastructure**: Never SSH into a server to patch a library. Build a new Docker image, provision a new server, and kill the old one.
