# Basic resource to test the state
resource "aws_sns_topic" "alerts" {
  name = "production-alerts"
}
