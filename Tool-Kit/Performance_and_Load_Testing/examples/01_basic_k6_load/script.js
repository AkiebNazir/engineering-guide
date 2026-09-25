import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const res = http.get('http://test.k6.io');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body contains text': (r) => r.body.includes('Collection of simple web-pages suitable for load testing'),
  });
  
  sleep(1);
}
