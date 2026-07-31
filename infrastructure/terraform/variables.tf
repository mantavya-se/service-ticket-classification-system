variable "db_password" {
  description = "Password for the db"
  type        = string
  sensitive = true
}

variable "admin_public_ip" {
  description = "IP address of the admin"
}

variable "runner_public_ip" {
  description = "IP address of the workflow runner"
}