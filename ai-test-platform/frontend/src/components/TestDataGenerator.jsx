import { useState } from 'react'

/**
 * 测试数据生成器组件
 * 用于在API测试时自动生成请求参数
 */
function TestDataGenerator({ apiInfo, onDataGenerated, onClose }) {
  const [loading, setLoading] = useState(false)
  const [generatedData, setGeneratedData] = useState(null)
  const [dataSchema, setDataSchema] = useState({})

  // 从API信息中提取参数schema
  const extractSchema = () => {
    const schema = {}
    
    // 如果有parameters（排除body类型的参数，因为已在requestBody中）
    if (apiInfo.parameters) {
      apiInfo.parameters.forEach(param => {
        // 跳过body参数，因为它们在requestBody中处理
        if (param.in !== 'body') {
          schema[param.name] = param.type || 'string'
        }
      })
    }
    
    // 如果有requestBody
    if (apiInfo.requestBody) {
      const rb = apiInfo.requestBody
      
      // 后端格式：{ content_type, schema: { properties: {...} } }
      if (rb.schema && rb.schema.properties) {
        Object.keys(rb.schema.properties).forEach(key => {
          const prop = rb.schema.properties[key]
          schema[key] = prop.type || 'string'
        })
      }
      
      // 兼容OpenAPI 3.0格式：{ content: { 'application/json': { schema: {...} } } }
      if (rb.content && rb.content['application/json']) {
        const jsonSchema = rb.content['application/json'].schema
        if (jsonSchema && jsonSchema.properties) {
          Object.keys(jsonSchema.properties).forEach(key => {
            schema[key] = jsonSchema.properties[key].type || 'string'
          })
        }
      }
    }
    
    return schema
  }

  // 生成测试数据
  const handleGenerate = async () => {
    setLoading(true)
    
    try {
      const schema = extractSchema()
      setDataSchema(schema)
      
      // 调用测试数据工厂API
      const response = await fetch('/api/test-data/smart-object', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_schema: schema,
          context: {
            api_path: apiInfo.path,
            api_method: apiInfo.method
          }
        })
      })
      
      const result = await response.json()
      
      if (result.success) {
        setGeneratedData(result.data)
      } else {
        alert('生成失败: ' + (result.message || '未知错误'))
      }
    } catch (error) {
      alert('生成失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  // 使用生成的数据
  const handleUseData = () => {
    if (generatedData) {
      onDataGenerated(generatedData)
      onClose()
    }
  }

  // 保存为数据集
  const handleSaveDataset = async () => {
    if (!generatedData) {
      alert('请先生成数据')
      return
    }

    const datasetName = prompt('请输入数据集名称:', `${apiInfo.summary || apiInfo.name} - 测试数据`)
    if (!datasetName) return

    setLoading(true)
    try {
      const response = await fetch('/api/test-data/datasets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: datasetName,
          data: generatedData,
          description: `为 ${apiInfo.method} ${apiInfo.path} 生成的测试数据`,
          api_id: apiInfo.id,
          tags: apiInfo.tags || []
        })
      })

      const result = await response.json()

      if (result.success) {
        alert('✅ 数据集保存成功!')
      } else {
        alert('保存失败: ' + (result.message || '未知错误'))
      }
    } catch (error) {
      alert('保存失败: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
        {/* 标题 */}
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-lg font-semibold">🏭 生成测试数据</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {/* API信息 */}
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-2 mb-2">
              <span className="px-2 py-1 text-xs font-semibold rounded bg-blue-100 text-blue-700">
                {apiInfo.method}
              </span>
              <span className="font-mono text-sm">{apiInfo.path}</span>
            </div>
            <p className="text-sm text-gray-600">{apiInfo.summary || apiInfo.name}</p>
          </div>

          {/* 参数Schema */}
          {Object.keys(dataSchema).length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">检测到的参数:</h4>
              <div className="space-y-1">
                {Object.entries(dataSchema).map(([key, type]) => (
                  <div key={key} className="flex items-center space-x-2 text-sm">
                    <span className="text-gray-600">{key}:</span>
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 生成的数据 */}
          {generatedData && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">生成的数据:</h4>
              <pre className="p-4 bg-gray-900 text-green-400 rounded-lg text-sm overflow-x-auto">
                {JSON.stringify(generatedData, null, 2)}
              </pre>
            </div>
          )}

          {/* 提示 */}
          {!generatedData && (
            <div className="text-sm text-gray-500 bg-blue-50 p-3 rounded-lg">
              💡 点击"生成数据"按钮,系统将根据API参数自动生成测试数据
            </div>
          )}
        </div>

        {/* 底部按钮 */}
        <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            取消
          </button>
          {!generatedData ? (
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '生成中...' : '🎲 生成数据'}
            </button>
          ) : (
            <>
              <button
                onClick={handleSaveDataset}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
              >
                💾 保存数据集
              </button>
              <button
                onClick={handleUseData}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                ✅ 使用此数据
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default TestDataGenerator
