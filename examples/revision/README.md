# 修订新增示例

请在虚拟环境中按需安装 `../../requirements-revision-optional.txt` 的依赖。源文件不含 PDF 行号和折行符。

- `encoding_demo.py`：在内存里构造编码冲突，输出原声明、猜测和已确认的解码方案。无外部请求。
- `playwright_routes.py`：路由全部返回本机夹具；运行前安装 Chromium，或在 PowerShell 设置 `$env:BROWSER_CHANNEL='msedge'` 使用已安装的 Edge。本轮已实测 Edge。
- `font_and_motion.py`：解码自建映射并生成本地控件测试位移；`--font 本地字体路径` 可检查字体 cmap。
- `redis_resume.py`：需本机 Redis 6.2+ 与 redis-py。运行 `python redis_resume.py seed`，再运行 `python redis_resume.py work`；结果写到当前目录 `results.db`。测试时只使用本例 `notes:demo:*` 键空间。BF.* 是正文里单独介绍的可选能力，Streams 骨架不依赖 BloomFilter。

Redis 服务恢复联调、curl_cffi 对自有 TLS 端点的探测未在本轮运行。不会把静态语法检查记作服务测试成功。队列骨架有提交后确认与接管流程，生产所需重试上限、死信、监控和持久化仍需按部署补齐。
