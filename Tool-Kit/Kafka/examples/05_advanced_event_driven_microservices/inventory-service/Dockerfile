FROM golang:1.21-alpine
WORKDIR /app
RUN go mod init inv-svc && go get github.com/segmentio/kafka-go
COPY main.go .
RUN go build -o svc main.go
CMD ["./svc"]
