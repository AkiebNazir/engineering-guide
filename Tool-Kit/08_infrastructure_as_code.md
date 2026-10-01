# Infrastructure as Code (IaC)

Clicking around a cloud console to create servers and databases is fine for a weekend
project. For a production system it is a liability: you cannot code-review clicks, you
cannot version-control them, and you cannot reliably recreate them in a disaster
recovery scenario. **Infrastructure as Code** (IaC) means describing infrastructure in
text files that live in Git, go through review and are applied by a tool. This chapter
explains the idea from zero, then goes deep on Terraform/OpenTofu (plan and apply, state,
modules, drift, safe changes in CI), compares the other tools you will meet (Pulumi,
CloudFormation/CDK, Crossplane) and covers Ansible for configuring machines, ending with
immutable infrastructure, which is where most teams land in 2026.

## Foundations — What does it mean to manage infrastructure as code?

### The problem

Imagine a startup's production environment built by hand over two years: a VPC, three
subnets, a load balancer, 14 security-group rules, a Postgres instance with 30 tuned
parameters, DNS records and IAM roles. Now:

- An engineer "temporarily" opened port 5432 to the internet during an incident. Nobody
  remembers.
- The company needs the same stack in a second region for a customer. Someone spends
  two weeks clicking, and gets three settings subtly wrong.
- An auditor asks "who changed the load balancer's TLS policy, and when?" There is no
  answer.

Every one of these is solved by the same move: **write the desired infrastructure down
in files, keep the files in Git, and let a tool make reality match them.** Changes then
go through pull requests (review, history, blame, revert), and a new region is the same
files with different variables.

### Declarative versus imperative

| Style | You write | The tool | Example |
|---|---|---|---|
| **Declarative** | *what* should exist ("a bucket named X with versioning on") | works out the steps: create, update in place, replace or delete | Terraform, OpenTofu, CloudFormation, Kubernetes YAML, Crossplane |
| **Imperative / procedural** | *the steps* ("install nginx, then copy the config, then restart") | runs them in order | shell scripts, Ansible playbooks (ordered tasks, though each module is desired-state) |

Declarative tools are built on **reconciliation**: compare desired state with actual
state and compute the difference. That is why running them twice is safe (the second
run finds nothing to do), a property called **idempotency**.

### Provisioning versus configuration

- **Provisioning** creates the infrastructure itself: networks, VMs, managed databases,
  buckets, DNS, IAM. Terraform/OpenTofu, Pulumi, CloudFormation.
- **Configuration management** sets up software *inside* machines: packages, files,
  users, services, kernel settings. Ansible, Chef, Puppet, Salt.

Containers shrank the second category: the configuration now lives in a Dockerfile and
the image is built once (see §8).

### An everyday example

A developer needs a new S3 bucket for invoice PDFs. Instead of opening the console they
add six lines of HCL to `storage.tf`, open a pull request, and the CI bot comments with
the plan: `+ aws_s3_bucket.invoices will be created`. A teammate reviews it, the PR is
merged and CI applies it. Three months later, `git log storage.tf` shows who added it
and why, and the same code creates the bucket in the staging account.

## 1. Terraform and OpenTofu: how plan and apply work

Terraform (HashiCorp) is the most widely used provisioning tool, and **OpenTofu** is its
open-source fork, created in 2023 after HashiCorp moved Terraform from the MPL to the
Business Source License (BSL) with version 1.6. OpenTofu is a Linux Foundation project,
drop-in compatible with Terraform ≈1.5/1.6-era configurations, and the two have
diverged a little since (OpenTofu added client-side state encryption; Terraform added
features such as ephemeral values). IBM completed its acquisition of HashiCorp in
February 2025. Everything in this section applies to both; commands are shown as
`terraform`, and `tofu` takes the same subcommands.

The configuration language is **HCL**. The main building blocks:

| Block | Purpose |
|---|---|
| `terraform { required_providers … backend … }` | tool settings: provider versions, where state lives |
| `provider "aws" { region = … }` | a plugin that turns resources into API calls (AWS, GCP, Azure, Kubernetes, GitHub, Datadog, Cloudflare, …) |
| `resource "aws_s3_bucket" "invoices" { … }` | a thing Terraform creates and owns |
| `data "aws_vpc" "main" { … }` | read something that already exists; Terraform does not own it |
| `variable` / `locals` / `output` | inputs, computed values, and values exported to callers |
| `module "vpc" { source = … }` | call a reusable package of configuration |

A small, complete configuration:

```hcl
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { team = "billing", managed_by = "terraform" }
  }
}

variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "env" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be dev, staging or prod."
  }
}

resource "aws_s3_bucket" "invoices" {
  bucket = "acme-invoices-${var.env}"
}

resource "aws_s3_bucket_versioning" "invoices" {
  bucket = aws_s3_bucket.invoices.id   # reference = implicit dependency
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "invoices" {
  bucket                  = aws_s3_bucket.invoices.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_arn" {
  value = aws_s3_bucket.invoices.arn
}
```

### The workflow

```bash
terraform init          # download providers and modules, configure the backend
terraform fmt -check    # canonical formatting
terraform validate      # syntax and type checks, no cloud calls
terraform plan -out=tfplan -var env=prod    # compute the diff and save it
terraform apply tfplan  # apply exactly the saved plan, nothing else
```

What `plan` actually does, which is the heart of every declarative tool:

```arch
%% caption: plan compares three things: the code (desired), the state file (what Terraform created last time) and a refresh of the real cloud. apply executes the diff and writes the new state.
grid 170x110
node code "HCL code" at 1,0 icon=code sub="desired state, in Git"
node state "State file" at 0,1 icon=file sub="IDs + last known attrs"
node plan "terraform plan" at 1,1 shape=card icon=decision sub="build graph, diff"
node cloud "Cloud APIs" at 2,1 icon=cloud sub="actual state"
node diff "Saved plan" at 1,2 shape=card icon=doc sub="create / update / replace / destroy"
node apply "terraform apply" at 1,3 shape=card icon=rocket sub="walks graph in parallel"
code -> plan
state -> plan
cloud -> plan : "refresh"
plan -> diff
diff -> apply : "after review"
apply:R -> cloud:B : "API calls"
apply:L ..> state:B : "write new state"
```

1. **Build a dependency graph.** A reference such as `aws_s3_bucket.invoices.id`
   creates an edge; Terraform creates the bucket before its versioning config and runs
   independent resources in parallel (10 at a time by default, `-parallelism=N`).
   `depends_on` adds an edge Terraform cannot infer.
2. **Refresh.** Read the real attributes of every resource in state from the cloud.
3. **Diff** desired against refreshed actual and classify each resource:
   `+` create, `~` update in place, `-/+` destroy and re-create (the attribute cannot be
   changed in place, e.g. an RDS instance's identifier or a subnet's CIDR), `-` destroy.
4. **Apply** walks the graph and calls the provider for each change, then records the
   results in state.

**Read every `-/+` line in a plan.** "Forces replacement" on a database means delete and
re-create, which is data loss unless you planned for it.

## 2. State: the file that makes it all work

The **state file** maps each resource address in your code
(`aws_s3_bucket.invoices`) to the real object's ID in the cloud (`acme-invoices-prod`)
along with its last known attributes. Without it Terraform could not tell "this bucket
is the one I made" from "somebody else's bucket with a similar name", and could not
detect resources you *removed* from code (which it must destroy).

Rules that hold everywhere:

- **Never commit state to Git.** It contains every attribute of every resource,
  including generated database passwords and private keys, in plain text.
- **Use a remote backend with locking**, so two people (or two CI jobs) cannot apply
  at the same time and corrupt it.
- **Encrypt it at rest and restrict who can read it.** Read access to state is often
  read access to production secrets. (OpenTofu can also encrypt state client-side.)
- **Split state by blast radius.** One giant state for everything makes every plan slow
  and every mistake global. Typical split: per environment × per layer (network,
  data, compute, DNS).

An S3 backend in 2026:

```hcl
terraform {
  backend "s3" {
    bucket       = "acme-tfstate-prod"
    key          = "billing/storage/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true   # S3-native locking (Terraform 1.10+); replaces the DynamoDB lock table
  }
}
```

The owner's original advice, "S3 with DynamoDB locking", was the standard for years.
Terraform 1.10 added S3-native locking through conditional writes (`use_lockfile`), and
the DynamoDB option (`dynamodb_table`) is deprecated as of 1.11; existing setups can run
both during a migration. Other common backends: GCS and Azure Blob (both lock natively),
**HCP Terraform** (the SaaS formerly called Terraform Cloud, which also runs plans
remotely), Spacelift, env0, Scalr.

### Changing state without changing infrastructure

| Need | Tool |
|---|---|
| Adopt a resource that was created by hand | `import` block (Terraform 1.5+): `import { to = aws_s3_bucket.logs  id = "acme-logs" }`, then `terraform plan -generate-config-out=gen.tf` |
| Rename or move a resource in code without destroying it | `moved { from = aws_s3_bucket.b  to = module.storage.aws_s3_bucket.b }` |
| Stop managing a resource but keep it | `removed { from = aws_s3_bucket.old  lifecycle { destroy = false } }` (1.7+), or `terraform state rm` |
| Inspect | `terraform state list`, `terraform state show ADDR` |
| Recover | backends keep versions; enable S3 versioning on the state bucket |

`moved`/`import`/`removed` blocks are preferred over the old `terraform state mv` and
`terraform import` commands because they are code: reviewed in a PR and applied by the
same pipeline.

## 3. Modules, environments and repetition

A **module** is a directory of `.tf` files with inputs (`variable`) and outputs
(`output`). Every configuration is a module (the root module); you call others:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"   # public registry module
  version = "~> 6.0"                           # always pin

  name            = "billing-${var.env}"
  cidr            = "10.20.0.0/16"
  azs             = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  private_subnets = ["10.20.1.0/24", "10.20.2.0/24", "10.20.3.0/24"]
  public_subnets  = ["10.20.101.0/24", "10.20.102.0/24", "10.20.103.0/24"]
}

module "queues" {
  source   = "./modules/sqs-with-dlq"         # local module
  for_each = toset(["orders", "emails", "refunds"])
  name     = "${each.key}-${var.env}"
}
```

`for_each` over a map or set gives each instance a stable key (`module.queues["emails"]`).
`count` gives an index (`[0]`, `[1]`, …), so removing the first element shifts every
later index and Terraform wants to destroy and re-create them. Prefer `for_each` for
anything that is not truly interchangeable.

### How to lay out environments

| Approach | How | Good | Watch out |
|---|---|---|---|
| **Directory per environment** | `envs/dev`, `envs/prod`, each a root module calling shared modules, each with its own backend key | explicit, separate state and credentials per env, easy to review | some duplication of wiring |
| **Workspaces** (`terraform workspace`) | one config, multiple named states | little duplication | same code and backend for all envs, easy to apply to the wrong one; best for short-lived copies |
| **Terragrunt** | thin wrapper that generates backends and inputs per env | DRY at large scale | another tool to learn |
| **Stacks** (HCP Terraform) / Spacelift stacks | platform-managed orchestration across many states | dependencies between states | vendor coupling |

Most teams start with directory-per-environment plus versioned shared modules; it keeps
prod credentials and state physically separate from dev.

## 4. Drift, lifecycle rules and dangerous changes

**Drift** is when the real infrastructure no longer matches the code, usually because
someone changed it in the console. `terraform plan` shows drift as a diff (and
`terraform plan -refresh-only` shows *only* drift). `apply` then puts managed attributes
back to what the code says, which is what you want for a hand-opened security group and
exactly what you do *not* want for a setting that an autoscaler legitimately changes.
Terraform only sees attributes it manages: a rule someone added *as a new resource* by
hand is invisible until you import it. Run a scheduled `plan` in CI (nightly) and alert
when it is non-empty.

`lifecycle` meta-arguments control risky behaviour:

```hcl
resource "aws_db_instance" "main" {
  identifier          = "billing-${var.env}"
  engine              = "postgres"
  engine_version      = "17"
  instance_class      = "db.r7g.large"
  allocated_storage   = 200
  username            = "app"
  manage_master_user_password = true   # RDS keeps the password in Secrets Manager, not in state
  deletion_protection = true
  skip_final_snapshot = false
  final_snapshot_identifier = "billing-${var.env}-final"

  lifecycle {
    prevent_destroy = true               # plan fails if anything would destroy this
    ignore_changes  = [engine_version]   # minor upgrades are applied by AWS automatically
  }
}

resource "aws_launch_template" "web" {
  name_prefix   = "web-"
  image_id      = var.ami_id
  instance_type = "t4g.medium"
  lifecycle {
    create_before_destroy = true         # new one first, then delete the old one
  }
}
```

Failure modes that show up in production:

| What happens | Why | Prevention |
|---|---|---|
| A plan replaces the database | an immutable attribute changed, or a resource was renamed without `moved` | read `-/+` lines; `prevent_destroy`; `deletion_protection`; `moved` blocks |
| Two applies at once corrupt state | no locking, or someone ran `-lock=false` | backend locking; apply only from CI |
| Apply half-fails | an API error midway; Terraform has no transactions | state records what succeeded; fix and re-apply; keep states small |
| A secret appears in a PR comment or log | plan output prints attribute values | `sensitive = true` on variables/outputs, ephemeral resources/values (Terraform 1.10+), keep secrets out of state where possible |
| Provider upgrade changes behaviour | unpinned `version` | pin with `~>`, commit `.terraform.lock.hcl`, upgrade deliberately |
| Plan passes, apply fails on quota or naming conflict | plan does not call every create API | stage in a non-prod account first |

## 5. IaC in a pipeline

Running `terraform apply` from a laptop means laptop credentials with production write
access and no record of what was reviewed. The standard setup:

```arch
%% caption: Plans run on every pull request; only the reviewed, merged change is applied, by CI, with short-lived cloud credentials.
grid 170x110
node dev "Engineer" at 0,0 icon=developer sub="edits .tf, opens PR"
node pr "Pull request" at 1,0 icon=git sub="fmt, validate, lint"
node plan "CI: plan" at 2,0 icon=workflow sub="posts plan to PR"
node pol "Policy checks" at 2,1 icon=shield sub="OPA / Checkov / cost"
node rev "Review + merge" at 1,1 icon=check sub="humans read the plan"
node apply "CI: apply" at 1,2 icon=rocket sub="protected env, approval"
node oidc "Cloud IAM" at 0,2 icon=identity sub="OIDC, short-lived role"
node st "State backend" at 2,2 icon=storage sub="locked during apply"
dev -> pr -> plan
plan -> pol
pol -> rev
rev -> apply
oidc -> apply : "token"
apply -> st
```

A GitHub Actions job that plans with keyless cloud credentials:

```yaml
name: terraform
on:
  pull_request:
    paths: ["infra/**"]
permissions:
  id-token: write      # allow the job to request an OIDC token
  contents: read
  pull-requests: write
jobs:
  plan:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra/envs/prod
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/tf-plan-readonly
          aws-region: eu-west-1
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init -input=false
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - run: terraform plan -input=false -out=tfplan
      - run: terraform show -no-color tfplan > plan.txt
```

The plan role is read-only; a separate apply job on `main`, gated by a protected
environment, assumes a write role. No long-lived access keys exist anywhere (see
[Secret Management](11_secret_management.md) on OIDC federation). Tools such as **Atlantis** (plan/apply
driven by PR comments), HCP Terraform, Spacelift and env0 package this workflow.

**Policy as code** checks plans before a human sees them: OPA/Conftest or Sentinel for
custom rules ("no public buckets", "all RDS encrypted", "only approved instance types"),
Checkov or Trivy's misconfiguration scanner (which absorbed tfsec) for common
misconfigurations, and Infracost to post the monthly cost delta on the PR.

## 6. The tool landscape

| Tool | Model | Language | State | When it fits |
|---|---|---|---|---|
| **Terraform** | declarative, plan/apply | HCL | state file you manage (or HCP Terraform) | the default for multi-cloud and SaaS providers; huge provider ecosystem |
| **OpenTofu** | same as Terraform | HCL | same, optional client-side encryption | same, with an open-source (MPL) license under the Linux Foundation |
| **Pulumi** | declarative engine driven by a real program | TypeScript, Python, Go, C#, Java, YAML | Pulumi Cloud or self-managed backend | teams that want loops, types, tests and abstractions in a general-purpose language |
| **AWS CloudFormation** | declarative, AWS-managed | YAML/JSON | managed by AWS (stacks), automatic rollback | AWS-only shops that want no state to manage |
| **AWS CDK** | code that synthesizes CloudFormation | TypeScript, Python, Java, Go, C# | CloudFormation stacks | AWS-only, developer-heavy teams |
| **Azure Bicep** / **Google Infrastructure Manager** | cloud-native declarative | Bicep / Terraform under the hood | managed | single-cloud shops |
| **Crossplane** | Kubernetes controllers continuously reconcile cloud resources | Kubernetes YAML (CRDs, compositions) | the Kubernetes API (etcd) | platform teams offering self-service infra through Kubernetes; drift is corrected continuously, not at the next apply |
| **Ansible** | ordered tasks, desired-state modules | YAML | none (checks the machine each run) | configuring machines, one-off orchestration |

The deepest difference is **when reconciliation happens**. Terraform/Pulumi/CloudFormation
reconcile when someone runs apply. Crossplane (and Kubernetes itself, and GitOps tools
such as Argo CD; see [GitOps and Argo CD](../CICD/04_gitops_and_argocd.md)) reconcile continuously in a
control loop, so drift is reverted within minutes whether or not anyone runs anything.

## 7. Ansible: configuring machines

If Terraform creates the EC2 instance, **Ansible** configures what runs on it: packages,
config files, users, services, kernel parameters. It is **agentless**: the control node
connects over SSH (WinRM for Windows) and runs small Python modules on the target, so
targets need SSH and Python, nothing else installed.

### Core concepts

- **Inventory**: hosts and groups, static or generated dynamically from a cloud API
  (the `amazon.aws.aws_ec2` inventory plugin builds groups from tags).

  ```ini
  [webservers]
  10.0.1.5
  10.0.1.6

  [webservers:vars]
  ansible_user=ubuntu
  ```

- **Playbook**: an ordered list of plays; each play maps hosts to tasks. Tasks run
  top-to-bottom (procedural order), but each **module** is desired-state: `state:
  present` means "make sure it is installed", not "install it".
- **Handlers**: tasks that run once at the end, only if notified by a task that
  *changed* something. The classic use: restart nginx only when its config changed.
- **Roles**: a standard folder layout (`tasks/`, `handlers/`, `templates/`,
  `defaults/`, `files/`) for reuse; **collections** package roles and modules for
  distribution (Ansible Galaxy).
- **Ansible Vault**: encrypts variable files that hold secrets.

```yaml
- name: Configure webservers
  hosts: webservers
  become: true                     # sudo
  vars:
    worker_connections: 4096
  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: true
        cache_valid_time: 3600

    - name: Deploy nginx config
      ansible.builtin.template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        owner: root
        mode: "0644"
        validate: nginx -t -c %s   # refuse to install a broken config
      notify: Reload nginx

    - name: Ensure nginx is running and enabled
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Reload nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded
```

```bash
ansible-playbook -i inventory.ini site.yml --check --diff   # dry run, show file diffs
ansible-playbook -i inventory.ini site.yml --limit 10.0.1.5 # one host first
ansible webservers -i inventory.ini -m ansible.builtin.ping # ad-hoc command
```

**Idempotency**: run that playbook ten times and the first run installs and configures;
the next nine report `ok` with zero `changed`. The `ansible.builtin.shell` and
`command` modules break this, because Ansible cannot know whether a command already
took effect; guard them with `creates:`/`removes:` or `changed_when:`, or find a real
module. `ansible-lint` flags these. Rolling changes across a fleet use `serial: 2` (two
hosts at a time) and `max_fail_percentage` so a bad change stops before it reaches
every server.

## 8. Immutable infrastructure: where most teams end up

With containers, Ansible's role has shrunk. Instead of booting a generic VM and
configuring it in place (mutable: every server slowly becomes a unique snowflake), teams
**bake** everything into an artifact and replace servers rather than patch them:

- **Containers**: the Dockerfile is the configuration; the image is built once in CI,
  scanned, pushed to a registry and deployed unchanged to every environment
  ([Docker and Containerization](01_docker_and_containers.md), [Kubernetes and Orchestration](02_kubernetes_and_helm.md)).
- **Golden VM images**: Packer (often running Ansible as the provisioner, so Ansible is
  still used, just at build time) builds an AMI; Terraform rolls an autoscaling group
  onto it.

```arch
%% caption: Immutable infrastructure: configuration happens once at build time; deploys swap whole servers or pods, and rollback is redeploying the previous artifact.
grid 160x110
node src "Git" at 0,0 icon=git sub="app + Dockerfile + .tf"
node build "CI build" at 1,0 icon=workflow sub="docker build / packer"
node reg "Registry" at 2,0 icon=package sub="image v42, immutable"
node tf "Terraform / GitOps" at 1,1 icon=code sub="points env at v42"
group run "Running fleet" color=green icon=server
node old "v41 instances" at 0,2 in run icon=server sub="drained, then deleted"
node new "v42 instances" at 2,2 in run icon=server sub="created fresh"
src -> build -> reg
reg -> tf
tf -> new : "create"
tf ..> old : "destroy"
```

**Never SSH into a server to patch a library.** Change the source, build a new
artifact, roll it out, delete the old instances. Rollback becomes "deploy v41 again",
and every server of a version is identical because none was ever changed after boot.
Terraform still owns the long-lived foundation (accounts, networks, databases, IAM,
DNS, clusters); the application layer on top is usually deployed by a CD system or
GitOps controller ([Continuous Deployment (CD) and Delivery](../CICD/02_cd_and_delivery.md)).

## Common interview questions

**What is Terraform state and why does it matter?**
A mapping from resource addresses in code to real cloud IDs plus last-known attributes.
Terraform needs it to know what it owns, to detect removed resources and to compute
diffs quickly. It holds secrets, so it lives in an encrypted, access-controlled remote
backend with locking, never in Git.

**What happens during `terraform plan`?**
Build a dependency graph from references, refresh real attributes from the provider,
diff against the configuration and output create / update / replace / destroy actions.
Save it with `-out` and apply exactly that file.

**How do you handle drift?**
Detect it with a scheduled `plan -refresh-only`, find out why (console change, another
tool, an autoscaler), then either codify the change or let apply revert it. Use
`ignore_changes` for attributes legitimately managed elsewhere. Prevent it with
read-only console access in production.

**Someone renamed a resource and the plan wants to destroy the production database.
What do you do?**
Stop. Add a `moved` block from the old address to the new one (or `terraform state mv`),
re-plan and confirm it shows no destroy. Add `prevent_destroy` and the provider's
deletion protection so it cannot happen silently again.

**`count` versus `for_each`?**
`count` addresses instances by index, so removing one shifts the others and causes
churn. `for_each` addresses by a stable key and is the safer default.

**Terraform versus Ansible?**
Terraform provisions infrastructure declaratively and tracks state; Ansible configures
software on existing machines through ordered, mostly idempotent tasks, with no state
file. They combine: Terraform creates the VMs, Ansible (or a baked image) configures
them.

**Terraform versus OpenTofu versus Pulumi versus CloudFormation?**
Same declarative core. Terraform (BSL) and OpenTofu (MPL fork) share HCL and providers;
Pulumi uses general-purpose languages; CloudFormation is AWS-managed with no state file
to operate and automatic rollback, but AWS only. Choose on ecosystem, team skills,
licensing and multi-cloud needs.

**How do you give CI permission to apply without storing cloud keys?**
OIDC federation: the CI job receives a signed identity token, the cloud trusts the CI
provider as an identity provider, and the job assumes a narrowly scoped role for
minutes. Separate read-only plan and write apply roles, with apply gated to `main`.

**What makes infrastructure immutable, and why prefer it?**
Servers are never modified after creation; changes ship as new images and old
instances are replaced. It removes configuration drift, makes rollback trivial and makes
every instance of a version identical.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Why clicking in a console does not scale; declarative vs imperative; can read a simple `resource` block and a plan output. |
| Junior (L3) | Software Engineer I | L3 | Run init/plan/apply in a team workflow, add resources and variables, read `+`/`~`/`-/+` in a plan, never commit state or secrets, write a basic Ansible task. |
| Mid (L4) | Software Engineer II | L4 | Write and version modules, use `for_each`, remote state with locking, `moved`/`import` blocks, lifecycle rules, drift detection, and a PR-based plan/apply pipeline with OIDC. |
| Senior (L5) | Senior Software Engineer | L5 | Design state layout by blast radius, environment structure, safe migrations of stateful resources, policy as code, secrets kept out of state, and recovery from a half-failed apply or corrupted state. |
| Staff+ (L6+) | Staff / Principal Engineer | L6+ | Choose the organization's IaC platform (Terraform vs OpenTofu vs Pulumi vs Crossplane) on licensing, ecosystem and operating model; define golden paths, module registries, guardrails and the boundary between IaC, GitOps and self-service. |

## Interview checklist

- [ ] I can explain declarative vs imperative, and provisioning vs configuration management.
- [ ] I can describe what `plan` does: graph, refresh, diff, and what `-/+` means.
- [ ] I can explain what is in state, why it is sensitive, and how locking works (S3 `use_lockfile`, GCS, HCP Terraform).
- [ ] I can use `moved`, `import` and `removed` blocks and explain why they beat CLI state surgery.
- [ ] I can explain `count` vs `for_each` churn.
- [ ] I can protect stateful resources with `prevent_destroy`, deletion protection and `create_before_destroy`.
- [ ] I can sketch a PR plan / merge apply pipeline with OIDC credentials and policy checks.
- [ ] I can compare Terraform, OpenTofu, Pulumi, CloudFormation/CDK and Crossplane.
- [ ] I can write an idempotent Ansible playbook with handlers, and explain why `shell` tasks break idempotency.
- [ ] I can explain immutable infrastructure and golden images.

Related: [Platform and Infrastructure](../SystemDesign/building_blocks/16_platform_and_infra.md) (IaC, GitOps and
progressive delivery at the architecture level), [Continuous Deployment (CD) and Delivery](../CICD/02_cd_and_delivery.md) and
[GitOps and Argo CD](../CICD/04_gitops_and_argocd.md) (continuous reconciliation), [Secret Management](11_secret_management.md)
(keeping secrets out of code and state), [Kubernetes and Orchestration](02_kubernetes_and_helm.md).
