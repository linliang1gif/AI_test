import React, { useState, useEffect } from 'react';
import { Card, Button, Select, Input, InputNumber, Table, Tag, Space, Tabs, message, Modal, Form } from 'antd';
import { 
  ThunderboltOutlined, 
  BulbOutlined, 
  CheckCircleOutlined,
  ExperimentOutlined,
  BarChartOutlined,
  FileTextOutlined
} from '@ant-design/icons';

const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

const TestDataFactory = () => {
  const [loading, setLoading] = useState(false);
  const [generatedData, setGeneratedData] = useState(null);
  const [dataType, setDataType] = useState('user');
  const [count, setCount] = useState(1);
  const [templates, setTemplates] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [stats, setStats] = useState(null);
  const [qualityResult, setQualityResult] = useState(null);

  // 数据类型选项
  const dataTypes = [
    { value: 'user', label: '用户' },
    { value: 'order', label: '订单' },
    { value: 'product', label: '产品' },
    { value: 'address', label: '地址' },
    { value: 'payment', label: '支付' },
    { value: 'inventory', label: '库存' },
  ];

  // 加载模板列表
  useEffect(() => {
    loadTemplates();
    loadStats();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-data/templates');
      const data = await response.json();
      if (data.success) {
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('加载模板失败:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/test-data/stats');
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  // 生成测试数据
  const handleGenerate = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/test-data/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_type: dataType,
          count: count,
          context: {},
          overrides: {}
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setGeneratedData(data.data);
        message.success(data.message);
        loadStats(); // 刷新统计
      } else {
        message.error('生成失败');
      }
    } catch (error) {
      message.error('生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // AI智能生成
  const handleSmartGenerate = async () => {
    setLoading(true);
    try {
      const schema = {
        'user_id': 'string',
        'username': 'string',
        'email': 'string',
        'phone': 'string',
        'age': 'integer',
        'status': 'string'
      };

      const response = await fetch('http://localhost:8000/api/test-data/smart-object', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_schema: schema,
          context: { role: 'adult', country: 'CN' }
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setGeneratedData(data.data);
        message.success('AI智能生成成功');
      }
    } catch (error) {
      message.error('AI生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 评估数据质量
  const handleEvaluate = async () => {
    if (!generatedData) {
      message.warning('请先生成数据');
      return;
    }

    setLoading(true);
    try {
      const dataToEvaluate = Array.isArray(generatedData) ? generatedData[0] : generatedData;
      
      const response = await fetch('http://localhost:8000/api/test-data/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: dataToEvaluate,
          schema: null
        })
      });
      
      const data = await response.json();
      if (data.success) {
        setQualityResult(data.evaluation);
        message.success('质量评估完成');
      }
    } catch (error) {
      message.error('评估失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 加载测试场景
  const handleLoadScenarios = async (entityType) => {
    try {
      const response = await fetch(`http://localhost:8000/api/test-data/scenarios/${entityType}`);
      const data = await response.json();
      if (data.success) {
        setScenarios(data.scenarios);
      }
    } catch (error) {
      message.error('加载场景失败: ' + error.message);
    }
  };

  // 渲染生成的数据
  const renderGeneratedData = () => {
    if (!generatedData) return null;

    const dataArray = Array.isArray(generatedData) ? generatedData : [generatedData];
    
    if (dataArray.length === 0) return null;

    const columns = Object.keys(dataArray[0]).map(key => ({
      title: key,
      dataIndex: key,
      key: key,
      ellipsis: true,
      render: (text) => {
        if (typeof text === 'object') {
          return JSON.stringify(text);
        }
        return String(text);
      }
    }));

    return (
      <Table 
        dataSource={dataArray.map((item, index) => ({ ...item, key: index }))}
        columns={columns}
        pagination={{ pageSize: 10 }}
        scroll={{ x: true }}
      />
    );
  };

  // 渲染质量评估结果
  const renderQualityResult = () => {
    if (!qualityResult) return null;

    const getScoreColor = (score) => {
      if (score >= 90) return 'success';
      if (score >= 75) return 'processing';
      if (score >= 60) return 'warning';
      return 'error';
    };

    return (
      <Card title="质量评估结果" style={{ marginTop: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <strong>总分: </strong>
            <Tag color={getScoreColor(qualityResult.total_score)}>
              {qualityResult.total_score}
            </Tag>
            <Tag>{qualityResult.level}</Tag>
          </div>
          
          <div>
            <strong>维度评分:</strong>
            <div style={{ marginTop: 8 }}>
              <Tag>完整性: {qualityResult.dimensions.completeness.toFixed(1)}</Tag>
              <Tag>有效性: {qualityResult.dimensions.validity.toFixed(1)}</Tag>
              <Tag>一致性: {qualityResult.dimensions.consistency.toFixed(1)}</Tag>
              <Tag>合理性: {qualityResult.dimensions.reasonableness.toFixed(1)}</Tag>
            </div>
          </div>

          {qualityResult.issues && qualityResult.issues.length > 0 && (
            <div>
              <strong>问题:</strong>
              <ul>
                {qualityResult.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {qualityResult.suggestions && qualityResult.suggestions.length > 0 && (
            <div>
              <strong>建议:</strong>
              <ul>
                {qualityResult.suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            </div>
          )}
        </Space>
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h1>测试数据工厂</h1>
      
      <Tabs defaultActiveKey="1">
        {/* 基础生成 */}
        <TabPane tab={<span><ThunderboltOutlined />基础生成</span>} key="1">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Space>
                  <span>数据类型:</span>
                  <Select 
                    value={dataType} 
                    onChange={setDataType}
                    style={{ width: 200 }}
                  >
                    {dataTypes.map(type => (
                      <Option key={type.value} value={type.value}>
                        {type.label}
                      </Option>
                    ))}
                  </Select>

                  <span>数量:</span>
                  <InputNumber 
                    min={1} 
                    max={100} 
                    value={count} 
                    onChange={setCount}
                  />

                  <Button 
                    type="primary" 
                    icon={<ThunderboltOutlined />}
                    onClick={handleGenerate}
                    loading={loading}
                  >
                    生成数据
                  </Button>

                  <Button 
                    icon={<CheckCircleOutlined />}
                    onClick={handleEvaluate}
                    disabled={!generatedData}
                  >
                    评估质量
                  </Button>
                </Space>
              </div>

              {renderGeneratedData()}
              {renderQualityResult()}
            </Space>
          </Card>
        </TabPane>

        {/* AI智能生成 */}
        <TabPane tab={<span><BulbOutlined />AI智能生成</span>} key="2">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Button 
                  type="primary" 
                  icon={<BulbOutlined />}
                  onClick={handleSmartGenerate}
                  loading={loading}
                >
                  AI智能生成用户
                </Button>
                <span style={{ marginLeft: 16, color: '#666' }}>
                  基于上下文和规则智能生成数据
                </span>
              </div>

              {renderGeneratedData()}
              {renderQualityResult()}
            </Space>
          </Card>
        </TabPane>

        {/* 测试场景 */}
        <TabPane tab={<span><ExperimentOutlined />测试场景</span>} key="3">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <span>实体类型: </span>
                <Select 
                  style={{ width: 200 }}
                  placeholder="选择实体类型"
                  onChange={handleLoadScenarios}
                >
                  <Option value="user">用户</Option>
                  <Option value="order">订单</Option>
                  <Option value="product">产品</Option>
                  <Option value="payment">支付</Option>
                </Select>
              </div>

              {scenarios.length > 0 && (
                <Table
                  dataSource={scenarios.map((s, i) => ({ ...s, key: i }))}
                  columns={[
                    { title: '场景名称', dataIndex: 'name', key: 'name' },
                    { 
                      title: '类型', 
                      dataIndex: 'type', 
                      key: 'type',
                      render: (type) => {
                        const colors = {
                          positive: 'green',
                          negative: 'red',
                          boundary: 'orange',
                          performance: 'blue'
                        };
                        return <Tag color={colors[type]}>{type}</Tag>;
                      }
                    },
                    { 
                      title: '优先级', 
                      dataIndex: 'priority', 
                      key: 'priority',
                      render: (priority) => {
                        const colors = {
                          high: 'red',
                          medium: 'orange',
                          low: 'default'
                        };
                        return <Tag color={colors[priority]}>{priority}</Tag>;
                      }
                    }
                  ]}
                  pagination={false}
                />
              )}
            </Space>
          </Card>
        </TabPane>

        {/* 统计信息 */}
        <TabPane tab={<span><BarChartOutlined />统计信息</span>} key="4">
          <Card>
            {stats && (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <strong>总生成次数: </strong>
                  <Tag color="blue">{stats.total}</Tag>
                </div>
                
                {stats.fields && Object.keys(stats.fields).length > 0 && (
                  <div>
                    <strong>字段统计:</strong>
                    <div style={{ marginTop: 8 }}>
                      {Object.entries(stats.fields).map(([field, count]) => (
                        <Tag key={field} style={{ margin: 4 }}>
                          {field}: {count}
                        </Tag>
                      ))}
                    </div>
                  </div>
                )}
              </Space>
            )}
          </Card>
        </TabPane>

        {/* 模板管理 */}
        <TabPane tab={<span><FileTextOutlined />模板管理</span>} key="5">
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <strong>可用模板:</strong>
              </div>
              <div>
                {templates.map(template => (
                  <Tag key={template} color="blue" style={{ margin: 4 }}>
                    {template}
                  </Tag>
                ))}
              </div>
            </Space>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default TestDataFactory;
