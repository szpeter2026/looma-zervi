/**
 * API Client - axios instance with JWT interceptor.
 * Shared by both planetx and saas packages.
 * Each brand creates its own instance with its own token storage.
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from "axios";

export interface ApiClientConfig {
  baseURL: string;
  getToken: () => string | null;
  onUnauthorized?: () => void;
}

export class ApiClient {
  private instance: AxiosInstance;
  private getToken: () => string | null;
  private onUnauthorized?: () => void;

  constructor(config: ApiClientConfig) {
    this.instance = axios.create({
      baseURL: config.baseURL,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });
    this.getToken = config.getToken;
    this.onUnauthorized = config.onUnauthorized;

    // Request interceptor: attach JWT
    this.instance.interceptors.request.use(
      (req: InternalAxiosRequestConfig) => {
        const token = this.getToken();
        if (token) {
          req.headers.Authorization = `Bearer ${token}`;
        }
        return req;
      },
      (err) => Promise.reject(err)
    );

    // Response interceptor: handle 401
    this.instance.interceptors.response.use(
      (resp) => resp,
      (err) => {
        if (err.response?.status === 401 && this.onUnauthorized) {
          this.onUnauthorized();
        }
        return Promise.reject(err);
      }
    );
  }

  async get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    const resp = await this.instance.get<T>(url, { params });
    return resp.data;
  }

  async post<T = any>(url: string, data?: any): Promise<T> {
    const resp = await this.instance.post<T>(url, data);
    return resp.data;
  }

  async put<T = any>(url: string, data?: any): Promise<T> {
    const resp = await this.instance.put<T>(url, data);
    return resp.data;
  }

  async delete<T = any>(url: string): Promise<T> {
    const resp = await this.instance.delete<T>(url);
    return resp.data;
  }
}

/**
 * Factory function to create an ApiClient instance.
 * Each brand calls this with its own token getter.
 */
export function createApiClient(config: ApiClientConfig): ApiClient {
  return new ApiClient(config);
}
