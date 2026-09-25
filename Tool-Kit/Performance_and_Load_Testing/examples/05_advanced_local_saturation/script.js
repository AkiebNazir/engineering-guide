import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 150 },   // Bombard the CPU
    { duration: '30s', target: 0 },    // Ramp down
  ],
};

// Generate a somewhat large payload
const payloadBase = { data: 'x'.repeat(1000) };

export default function () {
  const url = 'http://localhost:3000/process';
  
  // Random complexity between 20 and 35 to stress the fibonacci function unpredictably
  const complexity = Math.floor(Math.random() * 16) + 20;
  
  const payload = JSON.stringify({
    complexity,
    payload: payloadBase
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post(url, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'transaction time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(0.5);
}
