FROM golang:1.21-alpine
WORKDIR /app
RUN go mod init metrics-demo && go get github.com/prometheus/client_golang/prometheus/promhttp
COPY main.go .
RUN go build -o server main.go
EXPOSE 8080
CMD ["./server"]
