variable "do_token" {}
variable "do_spaces_access_id" {}
variable "do_spaces_secret_key" {}

provider "digitalocean" {
  token = "${var.do_token}"
  spaces_access_id  = "${var.do_spaces_access_id}"
  spaces_secret_key = "${var.do_spaces_secret_key}"
  version = "~> 1.9"
}

resource "digitalocean_project" "rl-arena" {
  name = "rl-arena"
  resources = ["${digitalocean_spaces_bucket.rl-arena.urn}"]
}

resource "digitalocean_spaces_bucket" "rl-arena" {
  name = "rl-arena"
  region = "fra1"
}

resource "digitalocean_project" "rl-arena" {
  image = "docker-18-04"
  name = "rl-arena"
  region = "fra1"
  size = "s-1vcpu-1gb"
  backups = true
  monitoring = true
  ssh_keys = ["d3:5f:69:0e:50:15:2e:b3:49:fd:92:d0:25:a8:c6:36"]
  user_data = <<-EOT
  #cloud-config
  runcmd:
    - git clone git@github.com:school-of-ai-angers/rl-arena.git
    - cd rl-arena; docker-compose up -d
  EOT
}

