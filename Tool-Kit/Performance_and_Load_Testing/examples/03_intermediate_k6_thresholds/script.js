import http from 'k6/http';
import { sleep, check } from 'k6';
import { Rate } from 'k6/metrics';

export const errorRate = new Rate('errors');

export const options = {
  vus: 20,
  duration: '1m',
  thresholds: {
    // p95 latency should be less than 200ms
    http_req_duration: ['p(95)<200'],
    // error rate should be less than 1%
    errors: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://test.k6.io/contacts.php');
  
  const success = check(res, {
    'status is 200': (r) => r.status === 200,
  });
  
  errorRate.add(!success);
  
  sleep(1);
}
