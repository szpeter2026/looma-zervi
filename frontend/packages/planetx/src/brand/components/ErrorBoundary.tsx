import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: string | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
}

/**
 * PlanetX Error Boundary
 * 捕获 React 渲染错误，显示星空主题品牌化错误页
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('[PlanetX ErrorBoundary]', error, errorInfo);
    this.setState({ errorInfo: errorInfo.componentStack || null });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        const Fallback = this.props.fallback;
        return <Fallback error={this.state.error!} reset={this.handleReset} />;
      }

      const isDev = import.meta.env.DEV;
      return (
        <div style={styles.container}>
          {/* 星空背景装饰 */}
          <div style={styles.starfield}>
            {Array.from({ length: 20 }, (_, i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  width: `${Math.random() * 3 + 1}px`,
                  height: `${Math.random() * 3 + 1}px`,
                  background: '#FFFFFF',
                  borderRadius: '50%',
                  left: `${Math.random() * 100}%`,
                  top: `${Math.random() * 100}%`,
                  opacity: Math.random() * 0.6 + 0.2,
                  animation: `twinkle ${Math.random() * 3 + 2}s ease-in-out infinite alternate`,
                }}
              />
            ))}
          </div>
          <div style={styles.card}>
            <div style={styles.icon}>🌌</div>
            <h2 style={styles.title}>任务异常</h2>
            <p style={styles.subtitle}>
              星系信号受到干扰，请尝试重新连接。
            </p>
            {isDev && this.state.error && (
              <details style={styles.details}>
                <summary style={styles.summary}>调试信息</summary>
                <pre style={styles.errorMsg}>{this.state.error.toString()}</pre>
                {this.state.errorInfo && (
                  <pre style={styles.errorMsg}>{this.state.errorInfo}</pre>
                )}
              </details>
            )}
            <div style={styles.actions}>
              <button onClick={this.handleReset} style={styles.btnSecondary}>
                重新尝试
              </button>
              <button onClick={this.handleReload} style={styles.btnPrimary}>
                返回基地
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0A0A1A 0%, #1A0A2E 50%, #0D1B2A 100%)',
    padding: '24px',
    position: 'relative',
    overflow: 'hidden',
  },
  starfield: {
    position: 'absolute',
    inset: 0,
    pointerEvents: 'none',
    zIndex: 0,
  },
  card: {
    background: 'rgba(26, 26, 46, 0.85)',
    backdropFilter: 'blur(12px)',
    border: '1px solid rgba(200, 255, 80, 0.15)',
    borderRadius: '16px',
    padding: '48px',
    maxWidth: '520px',
    textAlign: 'center',
    position: 'relative',
    zIndex: 1,
  },
  icon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  title: {
    fontSize: '22px',
    fontWeight: 900,
    color: '#C8FF50',
    marginBottom: '8px',
    letterSpacing: '0.5px',
  },
  subtitle: {
    fontSize: '14px',
    color: 'rgba(255,255,255,0.6)',
    marginBottom: '28px',
    lineHeight: 1.6,
  },
  details: {
    background: 'rgba(0,0,0,0.4)',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '24px',
    textAlign: 'left',
    maxHeight: '200px',
    overflow: 'auto',
    border: '1px solid rgba(255,255,255,0.08)',
  },
  summary: {
    cursor: 'pointer',
    fontSize: '13px',
    color: 'rgba(255,255,255,0.5)',
    marginBottom: '8px',
  },
  errorMsg: {
    fontSize: '12px',
    color: '#FF6B6B',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-all',
    margin: 0,
    fontFamily: 'monospace',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
  },
  btnSecondary: {
    padding: '10px 24px',
    borderRadius: '10px',
    border: '1px solid rgba(255,255,255,0.15)',
    background: 'transparent',
    color: 'rgba(255,255,255,0.8)',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 600,
    transition: 'all 0.2s',
  },
  btnPrimary: {
    padding: '10px 24px',
    borderRadius: '10px',
    border: 'none',
    background: 'linear-gradient(135deg, #C8FF50 0%, #A0E040 100%)',
    color: '#0A0A1A',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 700,
    transition: 'all 0.2s',
  },
};

export default ErrorBoundary;
