// 快速检查前端代码是否有语法错误
const fs = require('fs');
const path = require('path');

console.log('检查前端代码...\n');

// 检查关键文件是否存在
const files = [
  'src/pages/SwaggerWorkbench.jsx',
  'src/services/api.js',
  'src/App.jsx',
];

let hasError = false;

files.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    console.log(`✅ ${file} 存在`);
    
    // 简单的语法检查
    const content = fs.readFileSync(filePath, 'utf-8');
    
    // 检查是否有明显的语法错误
    const openBraces = (content.match(/{/g) || []).length;
    const closeBraces = (content.match(/}/g) || []).length;
    const openParens = (content.match(/\(/g) || []).length;
    const closeParens = (content.match(/\)/g) || []).length;
    
    if (openBraces !== closeBraces) {
      console.log(`   ⚠️  大括号不匹配: { ${openBraces} vs } ${closeBraces}`);
      hasError = true;
    }
    if (openParens !== closeParens) {
      console.log(`   ⚠️  小括号不匹配: ( ${openParens} vs ) ${closeParens}`);
      hasError = true;
    }
  } else {
    console.log(`❌ ${file} 不存在`);
    hasError = true;
  }
});

console.log('\n' + (hasError ? '❌ 发现问题' : '✅ 检查通过'));
process.exit(hasError ? 1 : 0);
