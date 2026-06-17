import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 1,
  iterations: __ENV.ITERATIONS ? parseInt(__ENV.ITERATIONS) : 3,
  thresholds: {
    'http_req_failed': ['rate<0.1'],
  },
};

const BASE = __ENV.LOOMA_URL || 'http://127.0.0.1:8010';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || 'token-b658c985';
const URL = `${BASE}/v1/ask`;

export default function () {
  const unique = Math.random().toString(36).slice(2, 9);
  const payload = JSON.stringify({
    query: `微基准测试 - 禁用缓存 ${unique}`,
    execution_hint: 'auto',
    context_scope: 'public',
  });
  const params = {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${AUTH_TOKEN}`,
    },
    timeout: '90s',
  };
  const res = http.post(URL, payload, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body contains answer': (r) => r.body && r.body.indexOf('answer') !== -1,
  });
  sleep(0.5);
}
