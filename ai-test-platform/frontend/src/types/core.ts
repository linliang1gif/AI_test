/**
 * 核心数据模型类型定义
 * 与后端 core/models.py 保持一致
 */

export enum TestCaseStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  PASSED = 'passed',
  FAILED = 'failed',
  SKIPPED = 'skipped',
  BLOCKED = 'blocked'
}

export enum TestCasePriority {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum DataType {
  VALID = 'valid',
  BOUNDARY = 'boundary',
  INVALID = 'invalid',
  NULL = 'null',
  EMPTY = 'empty'
}

export enum ExpectedBehavior {
  SUCCESS = 'success',
  CLIENT_ERROR = 'client_error',
  SERVER_ERROR = 'server_error'
}

export enum AssertionOperator {
  EQUALS = 'equals',
  NOT_EQUALS = 'not_equals',
  CONTAINS = 'contains',
  NOT_CONTAINS = 'not_contains',
  GREATER_THAN = 'greater_than',
  LESS_THAN = 'less_than',
  GREATER_THAN_OR_EQUAL = 'greater_than_or_equal',
  LESS_THAN_OR_EQUAL = 'less_than_or_equal',
  IN = 'in',
  NOT_IN = 'not_in',
  MATCHES = 'matches',
  EXISTS = 'exists',
  NOT_EXISTS = 'not_exists',
  IS_TYPE = 'is_type'
}

export enum HealingLevel {
  L1_RETRY = 'L1',
  L2_DATA = 'L2',
  L3_TOLERANCE = 'L3',
  L4_MANUAL = 'L4'
}

export enum RiskLevel {
  CRITICAL = 'critical',
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum TestType {
  FUNCTIONAL = 'functional',
  PERFORMANCE = 'performance',
  SECURITY = 'security',
  COMPATIBILITY = 'compatibility',
  BOUNDARY = 'boundary',
  EXCEPTION = 'exception'
}

export interface ExecutionConfig {
  method: string;
  url: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  body?: Record<string, any>;
  timeout?: number;
  retry_count?: number;
  retry_delay?: number;
}

export interface Assertion {
  field: string;
  operator: AssertionOperator;
  expected: any;
  description?: string;
}

export interface TestCase {
  id: string;
  title: string;
  module: string;
  priority: TestCasePriority;
  status: TestCaseStatus;
  steps: string[];
  expected: string;
  
  // 🆕 数据语义字段
  data_type: DataType;
  expected_behavior: ExpectedBehavior;
  
  // 执行配置
  execution_config?: ExecutionConfig;
  assertions?: Assertion[];
  
  // 元数据
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  tags?: string[];
  
  // 关联信息
  test_point_id?: string;
  api_id?: string;
  dataset_id?: string;
}

export interface ExecutionResult {
  test_case_id: string;
  status: TestCaseStatus;
  start_time: string;
  end_time: string;
  duration: number;
  
  // 请求响应
  request?: any;
  response?: any;
  status_code?: number;
  
  // 断言结果
  assertions_passed: number;
  assertions_failed: number;
  assertion_details?: any[];
  
  // 错误信息
  error?: string;
  error_type?: string;
  stack_trace?: string;
  
  // 修复信息
  healing_applied: boolean;
  healing_level?: HealingLevel;
  healing_details?: string;
}

export interface HealingRecord {
  test_case_id: string;
  error_type: string;
  healing_level: HealingLevel;
  healing_strategy: string;
  success: boolean;
  timestamp: string;
  details?: string;
  retry_count?: number;
}

export interface TestReport {
  report_id: string;
  title: string;
  start_time: string;
  end_time: string;
  duration: number;
  
  // 统计信息
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  pass_rate: number;
  
  // 测试结果
  results: ExecutionResult[];
  
  // 修复信息
  healing_summary: Record<string, number>;
  healed_cases: string[];
  
  // 元数据
  environment: string;
  tags: string[];
}

export interface TestPoint {
  id: string;
  name: string;
  description: string;
  risk_level: RiskLevel;
  test_type: TestType;
  module: string;
  priority: TestCasePriority;
  
  // 关联信息
  api_path?: string;
  api_method?: string;
  
  // 元数据
  created_at?: string;
  tags?: string[];
}

export interface APISpec {
  path: string;
  method: string;
  summary?: string;
  description?: string;
  parameters?: any[];
  request_body?: any;
  responses?: Record<string, any>;
  tags?: string[];
}
