const express = require('express');
const app = express();

app.use(express.json());

// A CPU intensive task to simulate complex processing
function calculateFibonacci(n) {
  if (n <= 1) return n;
  return calculateFibonacci(n - 1) + calculateFibonacci(n - 2);
}

app.post('/process', (req, res) => {
  const { complexity = 10, payload } = req.body;
  
  // Simulate CPU bottleneck
  const result = calculateFibonacci(complexity);
  
  res.json({
    success: true,
    result,
    receivedPayloadSize: JSON.stringify(payload || {}).length
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
