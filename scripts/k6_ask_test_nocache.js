import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 2,
  duration: __ENV.DURATION || '90s',
  thresholds: {
    // 每次请求唯一query，完全nocache
    'http_req_duration': ['p(95)<45000'],
    'http_req_failed': ['rate<0.05'],
  },
};

const BASE = __ENV.LOOMA_URL || 'http://127.0.0.1:5200';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const URL = `${BASE}/v1/ask`;

const headers = {
  'Content-Type': 'application/json',
};
if (AUTH_TOKEN) {
  headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
}
const params = {
  headers: headers,
  timeout: '90s',  // 允许单请求最多 90s
};

export default function () {
  // 每次请求使用唯一的query避免缓存
  const uniqueQuery = `内测压力测试 question ${__VU} ${__ITER} ${Date.now()}`;
  const payload = JSON.stringify({
    query: uniqueQuery,
    execution_hint: 'auto',
    context_scope: 'public',
  });
  
  const res = http.post(URL, payload, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body contains answer': (r) => r.body && r.body.indexOf('answer') !== -1,
  });
  sleep(1);
}

export function setup() {
  console.log(`[setup] No-cache test with unique queries each iteration`);
  return {};
}