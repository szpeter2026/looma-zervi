/**
 * Login - SaaS authentication page.
 * Owner: szbenyx
 *
 * Pure CSS + Tailwind (no tdesign-react).
 * Uses authStore for login state.
 * Brand: T空间.
 */
import { useState } from "react";
import { useNavigate, Navigate, Link } from "react-router-dom";
import { BRAND_SAAS } from "@looma/shared-core";
import { useSaasAuthStore } from "./authStore";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const { login, isAuthenticated } = useSaasAuthStore();
  const navigate = useNavigate();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      setErrorMsg("请输入邮箱和密码");
      return;
    }

    setLoading(true);
    setErrorMsg("");
    try {
      await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      const msg = (err as { detail?: string })?.detail ?? "登录失败，请检查邮箱和密码";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div
        className="w-[400px] rounded-xl p-8"
        style={{
          backgroundColor: "var(--color-bg-card)",
          boxShadow: "var(--shadow-lg)",
        }}
      >
        {/* 品牌 */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold" style={{ color: "var(--color-primary)" }}>
            {BRAND_SAAS.name}
          </h1>
          <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
            {BRAND_SAAS.slogan}
          </p>
        </div>

        {/* 表单 */}
        <div className="space-y-4">
          <div>
            <input
              type="email"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setErrorMsg("");
              }}
              placeholder="邮箱地址"
              className="w-full px-4 py-3 text-sm rounded-lg border outline-none transition-colors"
              style={{
                borderColor: "#e0e0e0",
                color: "var(--color-text-primary)",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "var(--color-primary)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e0e0e0";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleLogin();
              }}
            />
          </div>
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setErrorMsg("");
              }}
              placeholder="密码"
              className="w-full px-4 py-3 text-sm rounded-lg border outline-none transition-colors"
              style={{
                borderColor: "#e0e0e0",
                color: "var(--color-text-primary)",
              }}
              onFocus={(e) => {
                e.target.style.borderColor = "var(--color-primary)";
              }}
              onBlur={(e) => {
                e.target.style.borderColor = "#e0e0e0";
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleLogin();
              }}
            />
          </div>

          {errorMsg && (
            <p className="text-sm" style={{ color: "var(--color-danger)" }}>
              {errorMsg}
            </p>
          )}

          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full py-3 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-60 transition-colors font-medium"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            {loading ? "登录中..." : "登录"}
          </button>
        </div>

        {/* 注册链接 */}
        <div className="text-center mt-6">
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            还没有账号？{" "}
            <Link
              to="/register"
              className="no-underline hover:underline"
              style={{ color: "var(--color-primary)" }}
            >
              立即注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
