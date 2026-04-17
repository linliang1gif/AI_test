/**
 * 数据类型标签组件
 * 显示 data_type 和 expected_behavior
 */

import React from 'react';
import { DataType, ExpectedBehavior } from '../types/core';
import {
  DataTypeLabels,
  DataTypeColors,
  ExpectedBehaviorLabels,
  ExpectedBehaviorColors
} from '../types/enums';

interface DataTypeTagProps {
  dataType: DataType;
}

export const DataTypeTag: React.FC<DataTypeTagProps> = ({ dataType }) => {
  const label = DataTypeLabels[dataType] || dataType;
  const colorClass = DataTypeColors[dataType] || 'bg-gray-100 text-gray-700';
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  );
};

interface ExpectedBehaviorTagProps {
  behavior: ExpectedBehavior;
}

export const ExpectedBehaviorTag: React.FC<ExpectedBehaviorTagProps> = ({ behavior }) => {
  const label = ExpectedBehaviorLabels[behavior] || behavior;
  const colorClass = ExpectedBehaviorColors[behavior] || 'bg-gray-100 text-gray-700';
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colorClass}`}>
      {label}
    </span>
  );
};
