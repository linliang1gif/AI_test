/**
 * API 响应类型定义
 */

import { TestCase, ExecutionResult, TestReport } from './core';

// ==================== 通用响应 ====================

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

// ==================== 测试用例相关 ====================

export interface GenerateTestCasesRequest {
  file: File;
}

export interface GenerateTestCasesResponse {
  success: boolean;
  count: number;
  testCases: TestCase[];
  message: string;
  stats?: {
    testcases: number;
  };
}

export interface GetTestCasesResponse {
  success: boolean;
  data: TestCase[];
  count: number;
}

export interface BatchDeleteRequest {
  ids: number[];
}

export interface BatchDeleteResponse {
  success: boolean;
  deleted_count: number;
  message: string;
}

// ==================== 测试执行相关 ====================

export interface ExecuteTestCaseRequest {
  config?: {
    base_url?: string;
    timeout?: number;
    auth_config?: any;
  };
}

export interface ExecuteTestCaseResponse {
  success: boolean;
  result: ExecutionResult;
}

export interface ExecuteBatchRequest {
  test_case_ids: string[];
  config?: any;
}

export interface ExecuteBatchResponse {
  success: boolean;
  results: ExecutionResult[];
}

// ==================== 报告相关 ====================

export interface GenerateReportRequest {
  results: ExecutionResult[];
  format?: 'json' | 'html' | 'txt';
}

export interface GenerateReportResponse {
  success: boolean;
  report: TestReport;
}

export interface GetReportsResponse {
  success: boolean;
  data: TestReport[];
  count: number;
}

// ==================== 测试数据相关 ====================

export interface GenerateDataRequest {
  schema: Record<string, any>;
  data_type?: 'valid' | 'boundary' | 'invalid';
}

export interface GenerateDataResponse {
  success: boolean;
  data: any;
}

export interface GetDatasetsResponse {
  success: boolean;
  datasets: any[];
  count: number;
}

export interface BindDatasetRequest {
  dataset_id: string;
}

export interface BindDatasetResponse {
  success: boolean;
  message: string;
  test_case_id: number;
  dataset_id: string;
}

// ==================== AI相关 ====================

export interface AIGenerateRequest {
  prompt: string;
}

export interface AIGenerateResponse {
  success: boolean;
  response: string;
  message: string;
}

export interface GetAIProvidersResponse {
  success: boolean;
  providers: Array<{
    id: string;
    name: string;
    status: string;
  }>;
}

export interface SwitchAIProviderRequest {
  provider: string;
  model?: string;
}

export interface SwitchAIProviderResponse {
  success: boolean;
  message: string;
  provider: string;
  model?: string;
}
