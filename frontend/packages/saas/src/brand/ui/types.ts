/**
 * SaaS UI component Props type definitions.
 * Internal team uses these interfaces to wire data into components.
 */

// ============================================================
// Button
// ============================================================
export type ButtonVariant = "primary" | "secondary" | "outline" | "danger" | "ghost";
export type ButtonSize = "sm" | "md" | "lg";

export interface SaasButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
}

// ============================================================
// Input / Select / TextArea
// ============================================================
export interface SaasInputProps {
  value: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  size?: "sm" | "md" | "lg";
  label?: string;
  helperText?: string;
  type?: "text" | "password" | "email" | "number" | "tel";
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
}

export interface SaasSelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SaasSelectProps {
  value: string;
  options: SaasSelectOption[];
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  size?: "sm" | "md";
  label?: string;
  helperText?: string;
}

export interface SaasTextAreaProps {
  value: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: boolean;
  label?: string;
  helperText?: string;
  rows?: number;
  maxLength?: number;
}

// ============================================================
// Card
// ============================================================
export interface SaasCardProps {
  padding?: "sm" | "md" | "lg";
  hoverable?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
  className?: string;
}

// ============================================================
// Sidebar
// ============================================================
export interface SidebarNavItem {
  path: string;
  label: string;
  icon?: React.ReactNode;
  badge?: string | number;
  children?: SidebarNavItem[];
}

export interface SaasSidebarProps {
  items: SidebarNavItem[];
  collapsed?: boolean;
  onToggleCollapse?: () => void;
  brandName?: string;
  brandSlogan?: string;
  activePath?: string;
  onItemClick?: (path: string) => void;
  footer?: React.ReactNode;
}

// ============================================================
// Header
// ============================================================
export interface SaasHeaderProps {
  title?: string;
  user?: { name?: string; email?: string; avatar?: string } | null;
  notifications?: number;
  onLogout?: () => void;
  onNotificationsClick?: () => void;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
}

// ============================================================
// KPICard
// ============================================================
export type KPITrend = "up" | "down" | "flat";

export interface SaasKPICardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: KPITrend;
  trendValue?: string;
  sparklineData?: number[];
  loading?: boolean;
  error?: string;
}

// ============================================================
// DataTable
// ============================================================
export interface DataTableColumn<T = Record<string, unknown>> {
  key: string;
  title: string;
  width?: string | number;
  align?: "left" | "center" | "right";
  render?: (row: T) => React.ReactNode;
  sortable?: boolean;
}

export interface SaasDataTableProps<T = Record<string, unknown>> {
  columns: DataTableColumn<T>[];
  data: T[];
  rowKey?: string;
  loading?: boolean;
  emptyText?: string;
  compact?: boolean;
  selectable?: boolean;
  selectedKeys?: string[];
  onRowSelect?: (key: string, selected: boolean) => void;
  onSort?: (columnKey: string, direction: "asc" | "desc") => void;
  pageSize?: number;
  currentPage?: number;
  total?: number;
  onPageChange?: (page: number) => void;
}

// ============================================================
// ChatBubble
// ============================================================
export type ChatRole = "user" | "ai";

export interface SaasChatBubbleProps {
  role: ChatRole;
  content: string;
  markdown?: boolean;
  timestamp?: string;
  avatar?: string;
  loading?: boolean;
}

// ============================================================
// StreamingText
// ============================================================
export interface SaasStreamingTextProps {
  text: string;
  done?: boolean;
  cursorBlink?: boolean;
  speed?: number;
}

// ============================================================
// ResumeUploader
// ============================================================
export type UploadState = "idle" | "dragging" | "uploading" | "success" | "error";

export interface SaasResumeUploaderProps {
  state?: UploadState;
  fileName?: string;
  fileSize?: string;
  progress?: number;
  error?: string;
  acceptedFormats?: string[];
  onFileSelect?: (file: File) => void;
  onRetry?: () => void;
  onClear?: () => void;
}

// ============================================================
// Loading / Skeleton
// ============================================================
export interface SaasLoadingProps {
  size?: "sm" | "md" | "lg";
  text?: string;
  fullscreen?: boolean;
}

export interface SaasSkeletonProps {
  width?: string | number;
  height?: string | number;
  rounded?: boolean;
  count?: number;
}

// ============================================================
// EmptyState / ErrorState
// ============================================================
export interface SaasEmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

export interface SaasErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}
