/**
 * 枚举辅助函数和映射
 */

import {
  TestCaseStatus,
  TestCasePriority,
  DataType,
  ExpectedBehavior,
  HealingLevel,
  RiskLevel
} from './core';

// ==================== 数据类型 ====================

export const DataTypeLabels: Record<DataType, string> = {
  [DataType.VALID]: '正常数据',
  [DataType.BOUNDARY]: '边界数据',
  [DataType.INVALID]: '异常数据',
  [DataType.NULL]: '空值',
  [DataType.EMPTY]: '空字符串'
};

export const DataTypeColors: Record<DataType, string> = {
  [DataType.VALID]: 'bg-green-100 text-green-700',
  [DataType.BOUNDARY]: 'bg-yellow-100 text-yellow-700',
  [DataType.INVALID]: 'bg-red-100 text-red-700',
  [DataType.NULL]: 'bg-gray-100 text-gray-700',
  [DataType.EMPTY]: 'bg-gray-100 text-gray-700'
};

// ==================== 预期行为 ====================

export const ExpectedBehaviorLabels: Record<ExpectedBehavior, string> = {
  [ExpectedBehavior.SUCCESS]: '成功响应',
  [ExpectedBehavior.CLIENT_ERROR]: '客户端错误',
  [ExpectedBehavior.SERVER_ERROR]: '服务器错误'
};

export const ExpectedBehaviorColors: Record<ExpectedBehavior, string> = {
  [ExpectedBehavior.SUCCESS]: 'bg-green-100 text-green-700',
  [ExpectedBehavior.CLIENT_ERROR]: 'bg-orange-100 text-orange-700',
  [ExpectedBehavior.SERVER_ERROR]: 'bg-red-100 text-red-700'
};

// ==================== 优先级 ====================

export const PriorityLabels: Record<TestCasePriority, string> = {
  [TestCasePriority.CRITICAL]: 'P0',
  [TestCasePriority.HIGH]: 'P1',
  [TestCasePriority.MEDIUM]: 'P2',
  [TestCasePriority.LOW]: 'P3'
};

export const PriorityColors: Record<TestCasePriority, string> = {
  [TestCasePriority.CRITICAL]: 'bg-red-100 text-red-700',
  [TestCasePriority.HIGH]: 'bg-orange-100 text-orange-700',
  [TestCasePriority.MEDIUM]: 'bg-yellow-100 text-yellow-700',
  [TestCasePriority.LOW]: 'bg-gray-100 text-gray-700'
};

// ==================== 状态 ====================

export const StatusLabels: Record<TestCaseStatus, string> = {
  [TestCaseStatus.PENDING]: '待执行',
  [TestCaseStatus.RUNNING]: '执行中',
  [TestCaseStatus.PASSED]: '通过',
  [TestCaseStatus.FAILED]: '失败',
  [TestCaseStatus.SKIPPED]: '跳过',
  [TestCaseStatus.BLOCKED]: '阻塞'
};

export const StatusColors: Record<TestCaseStatus, string> = {
  [TestCaseStatus.PENDING]: 'bg-gray-100 text-gray-700',
  [TestCaseStatus.RUNNING]: 'bg-blue-100 text-blue-700',
  [TestCaseStatus.PASSED]: 'bg-green-100 text-green-700',
  [TestCaseStatus.FAILED]: 'bg-red-100 text-red-700',
  [TestCaseStatus.SKIPPED]: 'bg-yellow-100 text-yellow-700',
  [TestCaseStatus.BLOCKED]: 'bg-purple-100 text-purple-700'
};

// ==================== 修复级别 ====================

export const HealingLevelLabels: Record<HealingLevel, string> = {
  [HealingLevel.L1_RETRY]: 'L1-重试',
  [HealingLevel.L2_DATA]: 'L2-数据重建',
  [HealingLevel.L3_TOLERANCE]: 'L3-容错',
  [HealingLevel.L4_MANUAL]: 'L4-人工'
};

export const HealingLevelColors: Record<HealingLevel, string> = {
  [HealingLevel.L1_RETRY]: 'bg-blue-100 text-blue-700',
  [HealingLevel.L2_DATA]: 'bg-green-100 text-green-700',
  [HealingLevel.L3_TOLERANCE]: 'bg-yellow-100 text-yellow-700',
  [HealingLevel.L4_MANUAL]: 'bg-red-100 text-red-700'
};

// ==================== 风险等级 ====================

export const RiskLevelLabels: Record<RiskLevel, string> = {
  [RiskLevel.CRITICAL]: '严重',
  [RiskLevel.HIGH]: '高',
  [RiskLevel.MEDIUM]: '中',
  [RiskLevel.LOW]: '低'
};

export const RiskLevelColors: Record<RiskLevel, string> = {
  [RiskLevel.CRITICAL]: 'bg-red-100 text-red-700',
  [RiskLevel.HIGH]: 'bg-orange-100 text-orange-700',
  [RiskLevel.MEDIUM]: 'bg-yellow-100 text-yellow-700',
  [RiskLevel.LOW]: 'bg-gray-100 text-gray-700'
};
