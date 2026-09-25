# 05 Intermediate Concurrent Web Scraper

A web scraper that fetches the `<title>` from multiple URLs concurrently. It implements rate limiting using `time.Ticker` to ensure that it doesn't overwhelm target servers with too many concurrent requests.

## Usage
Run the following command to execute:
```bash
go run main.go
```
