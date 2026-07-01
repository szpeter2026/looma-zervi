/**
 * Register - SaaS registration page (MVP simplified).
 * Owner: szbenyx
 *
 * MVP: Direct register via /v1/auth/register (no invite code, no Supabase).
 * Pure CSS + Tailwind (no tdesign-react).
 * Brand: T空间.
 */
import { useState } from "react";
import { useNavigate, Link, useSearchParams } from "react-router-dom";
import { BRAND_SAAS, CLOSED_LOOP_EVENTS, trackEvent } from "@looma/shared-core";
import { useSaasAuthStore } from "./authStore";

export default function Register() {
  const [searchParams] = useSearchParams();
  const fromShare = searchParams.get("from") === "share";
  const shareCode = searchParams.get("code") || undefined;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const { register, isAuthenticated } = useSaasAuthStore();
  const navigate = useNavigate();

  if (isAuthenticated) {
    navigate("/", { replace: true });
    return null;
  }

  const handleRegister = async () => {
    if (!email.trim() || !password) {
      setErrorMsg("请输入邮箱和密码");
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg("两次密码不一致");
      return;
    }
    if (password.length < 6) {
      setErrorMsg("密码至少6位");
      return;
    }

    setLoading(true);
    setErrorMsg("");
    try {
      await register(email, password, name.trim() || undefined);
      if (fromShare) {
        trackEvent(CLOSED_LOOP_EVENTS.HR_REGISTER_FROM_SHARE, {
          share_code: shareCode,
          properties: { from: searchParams.get("from") },
        });
      }
      navigate("/", { replace: true });
    } catch (err) {
      const msg = (err as { detail?: string })?.detail ?? "注册失败，请稍后再试";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50">
      <div
        className="w-[420px] rounded-xl p-8"
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
            创建账号
          </p>
        </div>

        {/* 表单 */}
        <div className="space-y-4">
          <div>
            <input
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setErrorMsg("");
              }}
              placeholder="姓名（选填）"
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
            />
          </div>
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
              placeholder="密码（至少6位）"
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
            />
          </div>
          <div>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                setErrorMsg("");
              }}
              placeholder="确认密码"
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
                if (e.key === "Enter") handleRegister();
              }}
            />
          </div>

          {errorMsg && (
            <p className="text-sm" style={{ color: "var(--color-danger)" }}>
              {errorMsg}
            </p>
          )}

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full py-3 text-sm rounded-lg text-white border-none cursor-pointer disabled:opacity-60 transition-colors font-medium"
            style={{ backgroundColor: "var(--color-primary)" }}
          >
            {loading ? "注册中..." : "注册"}
          </button>
        </div>

        {/* 登录链接 */}
        <div className="text-center mt-6">
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            已有账号？{" "}
            <Link
              to="/login"
              className="no-underline hover:underline"
              style={{ color: "var(--color-primary)" }}
            >
              登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
