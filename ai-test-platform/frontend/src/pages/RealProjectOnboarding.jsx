import { useState } from 'react';
import { Card, Form, Input, Button, Steps, message, Space, Alert, Descriptions, Tag, Checkbox, Radio, Spin } from 'antd';
import { CheckCircleOutlined, InfoCircleOutlined, ApiOutlined, LinkOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
const { Step } = Steps;

// 通用POST请求
const postJSON = async (url, data) => {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const body = await resp.json();
  if (!resp.ok) {
    const err = new Error(body.detail?.message || body.detail || `HTTP ${resp.status}`);
    err.response = { status: resp.status, data: body };
    throw err;
  }
  return body;
};

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
  const [saveToken, setSaveToken] = useState(true);
  const [loading, setLoading] = useState(false);
  // Swagger来源: 'auto'(从baseUrl推导) | 'manual'(手动填URL) | 'yapi'(YApi项目)
  const [swaggerSource, setSwaggerSource] = useState('auto');
  const [autoDetecting, setAutoDetecting] = useState(false);
  const [autoDetectPaths, setAutoDetectPaths] = useState([]);
  // 检测阶段返回的 source_type: 'openapi' | 'swagger' | 'yapi'
  const [sourceType, setSourceType] = useState(null);
  // YApi 检测成功时保存的元数据
  const [yapiMeta, setYapiMeta] = useState(null);

  // 步骤1：填写项目信息 + 检测连接 + 检测Swagger（一步完成）
  const handleCheckAll = async () => {
    try {
      const requiredFields = ['projectName', 'baseUrl'];
      if (swaggerSource === 'manual') requiredFields.push('swaggerUrl');
      if (swaggerSource === 'yapi') requiredFields.push('yapiUrl', 'yapiEmail', 'yapiPassword');
      
      const values = await form.validateFields(requiredFields);
      setLoading(true);
      setConnectionResult(null);
      setSwaggerResult(null);

      // === 1. 检测连接 ===
      const connResp = await postJSON('/api/v2/real-project/check-connection', {
        base_url: values.baseUrl,
        token: values.token || null,
        health_path: values.healthPath || '/health',
        auth_type: values.token ? 'bearer' : 'none',
        timeout: 10
      });
      setConnectionResult(connResp);

      if (!connResp.success) {
        message.error('连接检测失败: ' + (connResp.message || '无法连接'));
        return;
      }
      message.success('连接成功！');

      // === 2. 检测Swagger ===
      let swaggerUrl = '';
      
      if (swaggerSource === 'manual') {
        swaggerUrl = values.swaggerUrl;
      } else if (swaggerSource === 'yapi') {
        // YApi模式：直接用YApi URL + 登录信息
        const yapiResp = await postJSON('/api/v2/real-project/check-swagger', {
          swagger_url: values.yapiUrl,
          yapi_email: values.yapiEmail,
          yapi_password: values.yapiPassword,
          timeout: 15
        });
        setSwaggerResult(yapiResp);
        if (yapiResp.success) {
          message.success(`YApi检测成功！发现 ${yapiResp.swagger_info?.total_operations || 0} 个接口`);
          setSourceType('yapi');
          setYapiMeta({
            yapi_base: yapiResp.yapi_base,
            yapi_project_id: yapiResp.yapi_project_id,
          });
          form.setFieldsValue({ swaggerUrl: values.yapiUrl });
          setCurrent(1);
        } else {
          message.error(yapiResp.message || 'YApi检测失败');
        }
        return;
      } else {
        // 自动推导模式：尝试常见Swagger路径
        const baseUrl = values.baseUrl.replace(/\/+$/, '');
        swaggerUrl = await autoDetectSwagger(baseUrl, values.token);
        if (!swaggerUrl) {
          message.warning('自动检测未找到Swagger文档，请切换到"手动填写"或"YApi"模式');
          return;
        }
        form.setFieldsValue({ swaggerUrl });
      }

      // 标准Swagger检测
      const swagResp = await postJSON('/api/v2/real-project/check-swagger', {
        swagger_url: swaggerUrl,
        token: values.token || null,
        auth_type: values.token ? 'bearer' : 'none',
        timeout: 10
      });
      setSwaggerResult(swagResp);

      if (swagResp.success) {
        message.success(`Swagger检测成功！发现 ${swagResp.swagger_info?.total_operations || 0} 个接口`);
        setSourceType(swagResp.source_type || 'openapi');
        setYapiMeta(null);
        setCurrent(1);
      } else {
        message.error(swagResp.message || 'Swagger检测失败');
      }

    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      const safeErrorMsg = errorMsg?.replace?.(/Bearer\s+[^\s]+/gi, 'Bearer ***') || errorMsg;
      message.error('检测失败: ' + safeErrorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 自动检测Swagger文档路径
  const autoDetectSwagger = async (baseUrl, token) => {
    const commonPaths = [
      '/swagger.json', '/openapi.json', '/v2/api-docs', '/v3/api-docs',
      '/api/swagger.json', '/api/openapi.json', '/docs/swagger.json',
      '/swagger/v1/swagger.json', '/api-docs'
    ];
    setAutoDetecting(true);
    setAutoDetectPaths([]);
    
    for (const path of commonPaths) {
      const url = baseUrl + path;
      try {
        const resp = await postJSON('/api/v2/real-project/check-swagger', {
          swagger_url: url,
          token: token || null,
          auth_type: token ? 'bearer' : 'none',
          timeout: 5
        });
        setAutoDetectPaths(prev => [...prev, { path, success: resp.success }]);
        if (resp.success) {
          setAutoDetecting(false);
          return url;
        }
      } catch {
        setAutoDetectPaths(prev => [...prev, { path, success: false }]);
      }
    }
    setAutoDetecting(false);
    return null;
  };

  // 步骤2：确认并创建
  const handleCreateAndImport = async () => {
    try {
      const values = form.getFieldsValue(true);
      setLoading(true);
      
      let projectId = null;
      let envId = null;
      
      try {
        // 1. 创建项目
        const projectResp = await postJSON('/api/v2/projects', {
          name: values.projectName,
          description: '通过真实项目接入向导创建'
        });
        projectId = projectResp.id;
        setCreatedProjectId(projectId);
        message.success('项目创建成功');
        
        // 2. 创建环境
        const envResp = await postJSON('/api/v2/environments', {
          project_id: projectId,
          name: 'prod',
          base_url: values.baseUrl
        });
        envId = envResp.id;
        message.success('环境创建成功');
        
        // 3. 自动保存Token（用户步骤1已填的Token直接复用）
        if (saveToken && values.token) {
          await postJSON('/api/v2/auth-profiles', {
            environment_id: envId,
            auth_type: 'bearer',
            auth_config: values.token,
            default_headers: {
              'Authorization': `Bearer ${values.token}`
            }
          });
          message.success('鉴权配置已保存');
        }
        
        // 4. 导入Swagger（根据 source_type 选择导入方式）
        const swaggerUrl = values.swaggerUrl?.trim();
        if (swaggerUrl || sourceType === 'yapi') {
          try {
            if (sourceType === 'yapi' && yapiMeta) {
              // YApi 导入：走专用接口，服务端登录 + 转换 + 保存
              await postJSON('/api/v2/swagger/import-yapi', {
                project_id: projectId,
                yapi_base: yapiMeta.yapi_base,
                yapi_project_id: yapiMeta.yapi_project_id,
                yapi_email: values.yapiEmail,
                yapi_password: values.yapiPassword,
                generate_cases: true
              });
            } else {
              // 标准 OpenAPI/Swagger 导入：带鉴权
              await postJSON('/api/v2/swagger/import-url', {
                project_id: projectId,
                url: swaggerUrl,
                generate_cases: true,
                auth_type: values.token ? 'bearer' : 'none',
                token: values.token || null
              });
            }
            message.success('Swagger导入成功，测试用例已生成');
            setCurrent(2);
          } catch (swaggerError) {
            if (swaggerError.response?.status === 409) {
              message.warning('该Swagger文档已导入过');
              setCurrent(2);
            } else if (swaggerError.response?.status === 401) {
              message.error('Swagger导入鉴权失败：Token无效或已过期，请检查后在Swagger工作台重新导入。');
              setTimeout(() => navigate(`/projects-v2/${projectId}`), 2000);
            } else {
              const detail = swaggerError.response?.data?.detail || swaggerError.message;
              const safeDetail = typeof detail === 'string' ? detail.replace(/Bearer\s+[^\s]+/gi, 'Bearer ***') : detail;
              message.warning(`项目和环境已创建，但Swagger导入失败: ${safeDetail}。可稍后在Swagger工作台重新导入。`);
              setTimeout(() => navigate(`/projects-v2/${projectId}`), 2000);
            }
            return;
          }
        } else {
          // 无Swagger也可创建项目
          message.success('项目创建完成（未导入Swagger）');
          setCurrent(2);
        }
        
      } catch (error) {
        if (!projectId) {
          message.error('项目创建失败: ' + (error.response?.data?.detail || error.message));
        } else if (!envId) {
          message.error(`项目已创建，但环境创建失败。请在项目详情中手动创建。`);
          setTimeout(() => navigate(`/projects-v2/${projectId}`), 2000);
        } else {
          message.error('操作失败: ' + (error.response?.data?.detail || error.message));
        }
        throw error;
      }
      
    } catch (error) {
      if (!error.response) {
        // 表单验证失败等
      }
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: '项目信息 & 检测',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="真实项目接入向导"
            description="填写项目信息，一键检测连接和Swagger。所有信息只填一次，Token自动复用。"
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
          />
          
          <Form form={form} layout="vertical">
            <Card size="small" title={<><ApiOutlined /> 基本信息</>} style={{ marginBottom: 16 }}>
              <Form.Item
                label="项目名称"
                name="projectName"
                rules={[{ required: true, message: '请输入项目名称' }]}
              >
                <Input placeholder="例如：商城后端API" />
              </Form.Item>
              
              <Form.Item
                label="真实环境地址（base_url）"
                name="baseUrl"
                rules={[{ required: true, message: '请输入环境地址' }]}
              >
                <Input placeholder="https://api.example.com" />
              </Form.Item>
              
              <Form.Item
                label="Bearer Token（可选）"
                name="token"
                extra="填写后将同时用于连接检测和Swagger鉴权，创建时自动保存到 auth_profiles"
              >
                <Input.Password placeholder="Token" />
              </Form.Item>
              
              <Form.Item
                label="健康检查路径"
                name="healthPath"
                initialValue="/health"
              >
                <Input placeholder="/health" />
              </Form.Item>
            </Card>
            
            <Card size="small" title={<><LinkOutlined /> Swagger / API文档来源</>} style={{ marginBottom: 16 }}>
              <Radio.Group 
                value={swaggerSource} 
                onChange={(e) => setSwaggerSource(e.target.value)}
                style={{ marginBottom: 16 }}
              >
                <Space direction="vertical">
                  <Radio value="auto">自动检测（从 base_url 推导常见路径）</Radio>
                  <Radio value="manual">手动填写 Swagger URL</Radio>
                  <Radio value="yapi">YApi 项目（需登录）</Radio>
                </Space>
              </Radio.Group>
              
              {swaggerSource === 'manual' && (
                <Form.Item
                  label="Swagger文档地址"
                  name="swaggerUrl"
                  rules={[{ required: true, message: '请输入Swagger地址' }]}
                >
                  <Input placeholder="https://api.example.com/swagger.json" />
                </Form.Item>
              )}
              
              {swaggerSource === 'yapi' && (
                <>
                  <Form.Item
                    label="YApi项目地址"
                    name="yapiUrl"
                    rules={[{ required: true, message: '请输入YApi地址' }]}
                    extra="直接粘贴浏览器中的YApi项目页地址即可"
                  >
                    <Input placeholder="https://yapi.xxx.com/project/123/interface/api" />
                  </Form.Item>
                  <Form.Item
                    label="YApi邮箱"
                    name="yapiEmail"
                    rules={[{ required: true, message: '请输入YApi邮箱' }]}
                  >
                    <Input placeholder="your@email.com" />
                  </Form.Item>
                  <Form.Item
                    label="YApi密码"
                    name="yapiPassword"
                    rules={[{ required: true, message: '请输入YApi密码' }]}
                  >
                    <Input.Password placeholder="YApi密码" />
                  </Form.Item>
                </>
              )}
              
              {autoDetecting && (
                <Alert
                  message={<><Spin size="small" /> 正在自动检测Swagger路径...</>}
                  description={
                    <div style={{ fontSize: 12, marginTop: 4 }}>
                      {autoDetectPaths.map(p => (
                        <div key={p.path}>{p.success ? '✅' : '❌'} {p.path}</div>
                      ))}
                    </div>
                  }
                  type="info"
                />
              )}
            </Card>

            {form.getFieldValue('token') && (
              <Card size="small" style={{ marginBottom: 16 }}>
                <Checkbox
                  checked={saveToken}
                  onChange={(e) => setSaveToken(e.target.checked)}
                >
                  创建时自动保存Token到鉴权配置（推荐）
                </Checkbox>
              </Card>
            )}
          </Form>
          
          {connectionResult && (
            <Card size="small" title="检测结果">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="连接">
                  {connectionResult.success ? (
                    <Tag color="success">成功 ({connectionResult.duration_ms}ms)</Tag>
                  ) : (
                    <Tag color="error">失败</Tag>
                  )}
                </Descriptions.Item>
                {swaggerResult && (
                  <Descriptions.Item label="Swagger">
                    {swaggerResult.success ? (
                      <Tag color="success">{swaggerResult.swagger_info?.total_operations || 0} 个接口</Tag>
                    ) : (
                      <Tag color="error">{swaggerResult.message}</Tag>
                    )}
                  </Descriptions.Item>
                )}
                {swaggerResult?.success && (
                  <>
                    <Descriptions.Item label="文档标题">
                      {swaggerResult.swagger_info?.title}
                    </Descriptions.Item>
                    <Descriptions.Item label="安全/写操作">
                      <Tag color="success">{swaggerResult.swagger_info?.safe_operations} GET</Tag>
                      {' '}
                      <Tag color="warning">{swaggerResult.swagger_info?.write_operations} 写</Tag>
                    </Descriptions.Item>
                  </>
                )}
              </Descriptions>
            </Card>
          )}
          
          <Button
            type="primary"
            onClick={handleCheckAll}
            loading={loading}
            block
            size="large"
          >
            一键检测
          </Button>
        </Space>
      ),
    },
    {
      title: '确认并创建',
      content: (
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="确认信息并创建项目"
            description="以下配置将一次性写入：projects → environments → auth_profiles → api_specs → test_cases"
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
              <Descriptions.Item label="Swagger来源">
                {swaggerSource === 'auto' ? '自动检测' : swaggerSource === 'yapi' ? 'YApi' : '手动'}
                {' → '}{form.getFieldValue('swaggerUrl') || form.getFieldValue('yapiUrl') || '(无)'}
              </Descriptions.Item>
              <Descriptions.Item label="接口数量">
                <Tag color="blue">{swaggerResult?.swagger_info?.total_operations || 0} 个</Tag>
              </Descriptions.Item>
              {form.getFieldValue('token') && (
                <Descriptions.Item label="Token">
                  {maskToken(form.getFieldValue('token'))}
                  {saveToken ? <Tag color="green" style={{ marginLeft: 8 }}>将保存</Tag> : <Tag>不保存</Tag>}
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
          
          <Space>
            <Button onClick={() => setCurrent(0)}>上一步修改</Button>
            <Button
              type="primary"
              onClick={handleCreateAndImport}
              loading={loading}
              size="large"
            >
              确认创建并导入
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
            description="真实项目已成功接入平台"
            type="success"
            showIcon
            icon={<CheckCircleOutlined />}
          />
          
          <Card>
            <p>✅ 项目已创建（projects表）</p>
            <p>✅ 环境已配置（environments表）</p>
            {saveToken && form.getFieldValue('token') && <p>✅ 鉴权已保存（auth_profiles表）</p>}
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
            size="large"
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
