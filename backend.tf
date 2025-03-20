terraform {
    backend "gcs" {
        bucket = "chess-terraform"
        prefix = "terraform"
    }
}
