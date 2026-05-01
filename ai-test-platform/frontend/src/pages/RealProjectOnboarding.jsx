import { useState } from 'react';
import { Card, Form, Input, Button, Steps, message, Space, Alert, Descriptions, Tag, Checkbox } from 'antd';
import { CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const { Step } = Steps;

// Token脱敏函数
const maskToken = (token) => {
  if (!token || token.length < 8) return '***';
  return token.substring(0, 4) + '***' + token.substring(token.length - 4);
};

export default function RealProjectOnboarding() {
  const navigate = useNavigate();
  const [current, setCurrent] = useState(0);
  const [form] = Form.useForm();
  
  // 状态
  const [connectionResult, setConnectionResult] = useState(null);
  const [swaggerResult, setSwaggerResult] = useState(null);
  const [createdProjectId, setCreatedProjectId] = useState(null);
  const [saveToken, setSaveToken] = useState(false);
  const [loading, setLoading] = useState(false);

  // 步骤1：检测连接
  const handleCheckConnection = async () => {
    try {
      const values = await form.validateFields(['baseUrl', 'token', 'healthPath']);
      setLoading(true);
      
      const response = await api.post('/api/v2/real-project/check-connection', {
        base_url: values.baseUrl,
        token: values.token || null,
        health_path: values.healthPath || '/health',
        auth_type: values.token ? 'bearer' : 'none',
        timeout: 10
      });
      
      setConnectionResult(response);
      
      if (response.success) {
        message.success('连接成功！');
        setCurrent(1);
      } else {
        message.error(response.message || '连接失败');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      // 确保错误信息不包含Token
      const safeErrorMsg = errorMsg.replace(/Bearer\s+[^\s]+/gi, 'Bearer ***');
      message.error('连接检测失败: ' + safeErrorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 步骤2：检测Swagger
  const handleCheckSwagger = async () => {
    try {
      const values = await form.validateFields(['swaggerUrl', 'token']);
      setLoading(true);
      
      const response = await api.post('/api/v2/real-project/check-swagger', {
        swagger_url: values.swaggerUrl,
        token: values.token || null,
        auth_type: values.token ? 'bearer' : 'none',
        timeout: 10
      });
      
      setSwaggerResult(response);
      
      if (response.success) {
        message.success('Swagger文档检测成功！');
        setCurrent(2);
      } else {
        message.error(response.message || 'Swagger检测失败');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      // 确保错误信息不包含Token
      const safeErrorMsg = errorMsg.replace(/Bearer\s+[^\s]+/gi, 'Bearer ***');
      message.error('Swagger检测失败: ' + safeErrorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 步骤3：创建项目、环境、鉴权并导入Swagger
  const handleCreateAndImport = async () => {
    try {
      const values = await form.validateFields(['projectName', 'baseUrl', 'token', 'swaggerUrl']);
      setLoading(true);
      
      let projectId = null;
      let envId = null;
      
      try {
        // 1. 创建项目
        const projectResp = await api.post('/api/v2/projects', {
          name: values.projectName,
          description: '通过真实项目接入向导创建'
        });
        
        projectId = projectResp.id;
        setCreatedProjectId(projectId);
        message.success('✅ 项目创建成功');
        
        // 2. 创建环境
        const envResp = await api.post('/api/v2/environments', {
          project_id: projectId,
          name: 'prod',
          base_url: values.baseUrl
        });
        
        envId = envResp.id;
        message.success('✅ 环境创建成功');
        
        // 3. 保存Token到auth_profiles（如果用户选择保存）
        if (saveToken && values.token) {
          await api.post('/api/v2/auth-profiles', {
            environment_id: envId,
            auth_type: 'bearer',
            auth_config: values.token,
            default_headers: {
              'Authorization': `Bearer ${values.token}`
            }
          });
          
          message.success('✅ 鉴权配置已保存');
        }
        
        // 4. 导入Swagger（URL规范化在后端处理）
        try {
          await api.post('/api/v2/swagger/import-url', {
            project_id: projectId,
            url: values.swaggerUrl.trim(),
            generate_cases: true
          });
          
          message.success('✅ Swagger导入成功');
          setCurrent(3);
          
        } catch (swaggerError) {
          // 处理409 Conflict（Swagger已导入）
          if (swaggerError.response?.status === 409) {
            const errorDetail = swaggerError.response?.data?.detail;
            message.warning('该Swagger文档已导入过');
            
            const confirmed = window.confirm(
              `该Swagger文档已导入过（API规范ID: ${errorDetail?.api_spec_id || '未知'}）\n\n` +
              `项目和环境已创建成功，是否跳转到API规范列表查看？`
            );
            
            if (confirmed) {
              navigate('/api-specs');
            } else {
              navigate(`/projects-v2/${projectId}`);
            }
            return;
          }
          
          // 其他Swagger导入错误
          message.error(
            `项目和环境已创建成功，但Swagger导入失败。\n` +
            `错误：${swaggerError.response?.data?.detail || swaggerError.message}\n` +
            `您可以稍后在Swagger工作台重新导入。`
          );
          
          // 跳转到项目详情
          setTimeout(() => {
            navigate(`/projects-v2/${projectId}`);
          }, 3000);
          return;
        }
        
      } catch (error) {
        // 处理项目/环境创建错误
        if (!projectId) {
          message.error('项目创建失败: ' + (error.response?.data?.detail || error.message));
        } else if (!envId) {
          message.error(
            `项目已创建成功，但环境创建失败。\n` +
            `错误：${error.response?.data?.detail || error.message}\n` +
            `请在项目详情中手动创建环境。`
          );
          setTimeout(() => {
            navigate(`/projects-v2/${projectId}`);
          }, 3000);
        } else {
          message.error('操作失败: ' + (error.response?.data?.detail || error.message));
        }
        throw error;
      }
      
    } catch (error) {
      // 最外层错误处理（表单验证失败等）
      if (!error.response) {
        message.error('操作失败: ' + error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: '连接检测',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="真实项目接入向导"
            description="用于首次接入真实项目。接入完成后，项目、环境、鉴权、API规范将统一进入项目详情页维护。"
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
          />
          
          <Alert
            message="步骤1：检测真实项目连接"
            description="此步骤仅用于检测连接，不会保存任何配置"
            type="info"
            showIcon
          />
          
          <Form form={form} layout="vertical">
            <Form.Item
              label="项目名称"
              name="projectName"
              rules={[{ required: true, message: '请输入项目名称' }]}
            >
              <Input placeholder="例如：生产环境API测试" />
            </Form.Item>
            
            <Form.Item
              label="真实环境地址"
              name="baseUrl"
              rules={[{ required: true, message: '请输入环境地址' }]}
            >
              <Input placeholder="https://api.example.com" />
            </Form.Item>
            
            <Form.Item
              label="Token（可选，仅用于检测）"
              name="token"
              extra="Token不会在此步骤保存，仅用于连接测试"
            >
              <Input.Password placeholder="Bearer Token" />
            </Form.Item>
            
            <Form.Item
              label="健康检查路径"
              name="healthPath"
              initialValue="/health"
            >
              <Input placeholder="/health" />
            </Form.Item>
          </Form>
          
          {connectionResult && (
            <Card size="small" title="连接检测结果">
              <Descriptions column={1} size="small">
                <Descriptions.Item label="状态">
                  {connectionResult.success ? (
                    <Tag color="success">连接成功</Tag>
                  ) : (
                    <Tag color="error">连接失败</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="状态码">
                  {connectionResult.status_code}
                </Descriptions.Item>
                <Descriptions.Item label="耗时">
                  {connectionResult.duration_ms}ms
                </Descriptions.Item>
                {connectionResult.error && (
                  <Descriptions.Item label="错误">
                    {connectionResult.error}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          )}
          
          <Button
            type="primary"
            onClick={handleCheckConnection}
            loading={loading}
            block
          >
            检测连接
          </Button>
        </Space>
      ),
    },
    {
      title: 'Swagger检测',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="步骤2：检测Swagger文档"
            description="检测Swagger文档是否可访问，统计接口数量。此步骤不会导入数据。"
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
          />
          
          <Form form={form} layout="vertical">
            <Form.Item
              label="Swagger文档地址"
              name="swaggerUrl"
              rules={[{ required: true, message: '请输入Swagger地址' }]}
            >
              <Input placeholder="https://api.example.com/swagger.json" />
            </Form.Item>
          </Form>
          
          {swaggerResult && swaggerResult.success && (
            <Card size="small" title="Swagger信息">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="标题">
                  {swaggerResult.swagger_info?.title}
                </Descriptions.Item>
                <Descriptions.Item label="版本">
                  {swaggerResult.swagger_info?.version}
                </Descriptions.Item>
                <Descriptions.Item label="路径数">
                  {swaggerResult.swagger_info?.total_paths}
                </Descriptions.Item>
                <Descriptions.Item label="操作数">
                  {swaggerResult.swagger_info?.total_operations}
                </Descriptions.Item>
                <Descriptions.Item label="安全操作(GET)">
                  <Tag color="success">{swaggerResult.swagger_info?.safe_operations}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="写操作">
                  <Tag color="warning">{swaggerResult.swagger_info?.write_operations}</Tag>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          )}
          
          <Space>
            <Button onClick={() => setCurrent(0)}>上一步</Button>
            <Button
              type="primary"
              onClick={handleCheckSwagger}
              loading={loading}
            >
              检测Swagger
            </Button>
          </Space>
        </Space>
      ),
    },
    {
      title: '创建并导入',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="步骤3：创建项目、环境、鉴权并导入Swagger"
            description="配置将保存到标准数据表：projects、environments、auth_profiles、api_specs"
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
          />
          
          <Card size="small" title="即将创建">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="项目名称">
                {form.getFieldValue('projectName')}
              </Descriptions.Item>
              <Descriptions.Item label="环境地址">
                {form.getFieldValue('baseUrl')}
              </Descriptions.Item>
              <Descriptions.Item label="Swagger地址">
                {form.getFieldValue('swaggerUrl')}
              </Descriptions.Item>
              <Descriptions.Item label="接口数量">
                {swaggerResult?.swagger_info?.total_operations || 0}
              </Descriptions.Item>
              {form.getFieldValue('token') && (
                <Descriptions.Item label="Token">
                  {maskToken(form.getFieldValue('token'))}
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
          
          <Card size="small">
            <Checkbox
              checked={saveToken}
              onChange={(e) => setSaveToken(e.target.checked)}
            >
              保存Token到鉴权配置（auth_profiles表）
            </Checkbox>
            {saveToken && (
              <Alert
                message="Token将保存到auth_profiles表，与环境关联。Token仅保存一次，不会重复保存。"
                type="warning"
                showIcon
                style={{ marginTop: 8 }}
              />
            )}
          </Card>
          
          <Alert
            message="配置归属说明"
            description={
              <div>
                <p>• 环境地址 → environments.base_url</p>
                <p>• Token → auth_profiles.auth_config</p>
                <p>• Swagger → api_specs.source_url</p>
                <p>• 项目名称 → projects.name</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginTop: 8 }}
          />
          
          <Space>
            <Button onClick={() => setCurrent(1)}>上一步</Button>
            <Button
              type="primary"
              onClick={handleCreateAndImport}
              loading={loading}
            >
              创建并导入
            </Button>
          </Space>
        </Space>
      ),
    },
    {
      title: '完成',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="接入成功！"
            description="真实项目已成功接入平台，后续请在项目详情中维护环境、鉴权和API规范"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
          />
          
          <Card>
            <p>✅ 项目已创建（projects表）</p>
            <p>✅ 环境已配置（environments表）</p>
            {saveToken && <p>✅ 鉴权已保存（auth_profiles表）</p>}
            <p>✅ Swagger已导入（api_specs表）</p>
            <p>✅ 测试用例已生成（test_cases表）</p>
          </Card>
          
          <Alert
            message="后续维护"
            description="环境配置、Token管理、Swagger更新请前往项目详情页面"
            type="info"
            showIcon
          />
          
          <Button 
            type="primary" 
            onClick={() => navigate(`/projects-v2/${createdProjectId}`)}
            block
          >
            前往项目详情
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title="真实项目接入向导">
        <Steps current={current} style={{ marginBottom: 24 }}>
          {steps.map(item => (
            <Step key={item.title} title={item.title} />
          ))}
        </Steps>
        
        <div style={{ marginTop: 24 }}>
          {steps[current].content}
        </div>
      </Card>
    </div>
  );
}
