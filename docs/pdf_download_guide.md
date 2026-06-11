# 巨潮资讯网 PDF 下载指南

## 问题分析

### 原始问题
巨潮资讯网的 PDF 文件无法直接下载，因为：
1. AKShare 返回的 `pdf_url` 是**详情页链接**，不是直接的 PDF 下载链接
2. 网站需要登录才能访问 PDF 下载 API
3. 下载 API 使用 **POST** 方法而不是 GET 方法

### 解决方案
通过分析巨潮资讯网的 JavaScript 代码，找到了 PDF 下载的完整流程：
1. 从详情页 URL 提取参数（`announcementId`、`announcementTime`）
2. 调用 API `/new/announcement/bulletin_detail`（使用 POST 方法）
3. 从返回数据中提取 `adjunctUrl`
4. 构建完整 PDF URL：`https://static.cninfo.com.cn/{adjunctUrl}`
5. 下载 PDF 文件

## 使用方法

### 1. 获取 Cookie

#### 步骤 1：登录巨潮资讯网
1. 打开浏览器访问：https://www.cninfo.com.cn
2. 使用账号密码登录

#### 步骤 2：获取 Cookie
1. 打开浏览器开发者工具（F12）
2. 切换到 **Network** 标签
3. 刷新页面
4. 选择任意一个请求
5. 在请求头中找到 **Cookie** 字段
6. 复制完整的 Cookie 字符串

#### 注意事项
- Cookie 会过期，建议定期更新
- Cookie 包含敏感信息，请妥善保管
- 不要将 Cookie 提交到代码仓库

### 2. 运行下载脚本

#### 基本用法
```bash
cd /Users/zhujie/大三下/数据挖掘与机器学习/poject_B
python src/download_pdfs.py --cookie "你的Cookie"
```

#### 完整参数说明

```bash
python src/download_pdfs.py \
  --metadata data/metadata/metadata.csv \      # metadata 文件路径
  --output-dir data/pdf \                      # PDF 保存目录
  --failed-log outputs/logs/failed_downloads.csv \  # 失败记录文件
  --sleep-seconds 2.0 \                        # 请求间隔秒数
  --retries 3 \                               # 重试次数
  --timeout 30 \                              # 请求超时时间
  --cookie "你的Cookie"                        # 巨潮资讯网登录 Cookie
```

#### 推荐参数
```bash
python src/download_pdfs.py \
  --cookie "你的Cookie" \
  --sleep-seconds 2.0 \
  --retries 3 \
  --timeout 30
```

### 3. 监控下载进度

下载过程中会显示：
- 当前进度：`[1/156]`
- 股票信息：`601398 工商银行`
- 下载状态：成功/失败/跳过
- 文件大小

### 4. 查看下载结果

```bash
# 查看已下载的 PDF 文件
ls -lh data/pdf/

# 查看失败记录
cat outputs/logs/failed_downloads.csv

# 查看下载日志
cat outputs/logs/download.log
```

## Cookie 配置建议

### 方法 1：命令行传入（推荐用于测试）
```bash
python src/download_pdfs.py --cookie "JSESSIONID=xxx; insert_cookie=xxx; ..."
```

### 方法 2：保存到环境变量（推荐用于生产）
```bash
# 在 .bashrc 或 .zshrc 中添加
export CNINFO_COOKIE="你的Cookie"

# 在脚本中使用
python src/download_pdfs.py --cookie "$CNINFO_COOKIE"
```

### 方法 3：使用 .env 文件（需要 python-dotenv）
```bash
# .env 文件
CNINFO_COOKIE=你的Cookie

# 脚本中加载
from dotenv import load_dotenv
import os
load_dotenv()
cookie = os.getenv('CNINFO_COOKIE')
```

### 方法 4：使用配置文件
```bash
# configs/cookie.txt（添加到 .gitignore）
JSESSIONID=xxx; insert_cookie=xxx; ...

# 运行
python src/download_pdfs.py --cookie "$(cat configs/cookie.txt)"
```

## 注意事项

### 1. Cookie 有效期
- Cookie 通常在几个小时到几天后过期
- 如果下载中断，重新登录获取新的 Cookie

### 2. 访问频率限制
- 建议设置 `--sleep-seconds 2.0` 或更大
- 避免短时间内大量请求
- 可以在夜间运行大批量下载任务

### 3. 失败处理
- 失败记录会自动保存到 `outputs/logs/failed_downloads.csv`
- 重新运行时，已存在的文件会被跳过
- 可以手动修复失败记录后重新运行

### 4. 文件名说明
文件名格式：`{stock_code}_{publish_date}_{title_hash}.pdf`
- `stock_code`：股票代码（如 601398）
- `publish_date`：发布日期（如 2023-09-06）
- `title_hash`：标题的哈希值前 8 位

### 5. 文件验证
下载完成后可以验证 PDF 文件：
```bash
# 检查文件类型
file data/pdf/*.pdf

# 检查文件大小
du -sh data/pdf/

# 验证 PDF 内容
python -c "import PyPDF2; print(PyPDF2.__version__)"
```

## 测试脚本

项目中包含两个测试脚本：

### test_api.py
测试 API 调用是否正常
```bash
python test_api.py
```

### test_pdf_download.py
测试单个 PDF 下载
```bash
python test_pdf_download.py
```

## 常见问题

### Q1: Cookie 过期怎么办？
**A**: 重新登录巨潮资讯网，获取新的 Cookie

### Q2: 下载失败率很高怎么办？
**A**: 
- 增加 `--sleep-seconds` 参数值
- 减少 `--retries` 参数值
- 在非高峰时段运行

### Q3: 如何只下载前 N 个文件？
**A**: 
```bash
# 创建只包含前 N 条记录的 metadata 文件
head -$((N+1)) data/metadata/metadata.csv > data/metadata/metadata_test.csv

# 运行下载
python src/download_pdfs.py --metadata data/metadata/metadata_test.csv --cookie "你的Cookie"
```

### Q4: 如何继续中断的下载？
**A**: 脚本会自动跳过已存在的文件，直接重新运行即可：
```bash
python src/download_pdfs.py --cookie "你的Cookie"
```

### Q5: 如何查看详细的日志信息？
**A**: 
```bash
# 实时查看日志
tail -f outputs/logs/download.log

# 查看所有日志（包括调试信息）
python src/download_pdfs.py --cookie "你的Cookie" --verbose
```

## 安全建议

1. **不要将 Cookie 提交到代码仓库**
   - 添加到 `.gitignore`
   ```bash
   echo ".env" >> .gitignore
   echo "configs/cookie.txt" >> .gitignore
   ```

2. **定期更新 Cookie**
   - 建议每周检查一次
   - 过期后及时更新

3. **使用环境变量**
   - 生产环境推荐使用环境变量或密钥管理服务

4. **限制 Cookie 权限**
   - 只使用必要的 Cookie
   - 避免泄露其他敏感信息

## 参考资料

- [巨潮资讯网](https://www.cninfo.com.cn)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [Requests 库文档](https://docs.python-requests.org/)
