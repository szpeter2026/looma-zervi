import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: __ENV.VUS ? parseInt(__ENV.VUS) : 2,
  duration: __ENV.DURATION || '90s',
  thresholds: {
    // 首请求后命中缓存，后续 < 50ms；首次 ~35s
    'http_req_duration': ['p(95)<45000'],
    'http_req_failed': ['rate<0.05'],
  },
};

const BASE = __ENV.LOOMA_URL || 'http://127.0.0.1:5200';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';
const URL = `${BASE}/v1/ask`;
const payload = JSON.stringify({
  query: '底座优先架构是什么？',
  execution_hint: 'auto',
  context_scope: 'public',
});
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
  const res = http.post(URL, payload, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body contains answer': (r) => r.body && r.body.indexOf('answer') !== -1,
  });
  sleep(1);
}

// 可选的预热阶段：先发一个请求填满缓存
export function setup() {
  console.log(`[setup] 预热请求: ${URL}`);
  const warm = http.post(URL, payload, params);
  console.log(`[setup] 预热完成 status=${warm.status} duration=${warm.timings.duration}ms`);
  return {};
}