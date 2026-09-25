import http from 'k6/http';
import { sleep, check } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 10 },   // below normal load
    { duration: '1m', target: 10 },    
    { duration: '10s', target: 140 },  // spike to 140 users
    { duration: '3m', target: 140 },   // stay at 140 for 3 minutes
    { duration: '10s', target: 10 },   // scale down. Recovery stage.
    { duration: '3m', target: 10 },    
    { duration: '10s', target: 0 },    // scale down to 0
  ],
};

export default function () {
  const res = http.get('http://test.k6.io');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
}
