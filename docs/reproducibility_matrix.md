# 复现矩阵

在 `book_crawler/` 目录运行下表命令。Python 完整依赖版本见 `requirements-lock.txt`，Node 依赖见 `examples/package-lock.json`。Python 3.12、Node.js 22、Playwright 浏览器为已验证环境；浏览器示例需要本机 Edge 或 `playwright install chromium`。`pytest -q` 执行成功与失败路径回归。

| 章 | 示例文件 | 额外依赖 | 运行命令 | 期望观察 |
|---:|---|---|---|---|
| 1 | `ch01_links.py` | 标准库 | `python examples/ch01_links.py` | 两条允许域名的绝对链接 |
| 2 | `ch02_local_requests.py`、`ch02_payloads.py` | Requests | `python examples/ch02_payloads.py` | 查询串、表单、JSON 正文与中文 HTML 均可区分 |
| 3 | `ch03_cards.py` | Beautiful Soup | `python examples/ch03_cards.py` | 两条完整卡片，跳过缺链接卡片 |
| 4 | `ch04_xpath.py` | lxml | `python examples/ch04_xpath.py` | `One`、`Two` 各配自己的链接 |
| 5 | `ch05_cursor.py` | Requests | `python examples/ch05_cursor.py` | 本地 HTTP 翻页后得 `[1, 2, 3, 4]` |
| 6 | `ch06_xml.py`、`ch06_tabular.py` | 标准库 | `python examples/ch06_tabular.py` | 命名空间 XML 与两条中文 CSV/JSON Lines 记录 |
| 7 | `ch07_sqlite.py` | 标准库 | 连续运行两次 `python examples/ch07_sqlite.py` | 文件数据库两次均输出 1，无建表错误 |
| 8 | `ch08_async.py`、`ch08_failure.py` | 标准库 | `python examples/ch08_failure.py` | 保留三条成功和编号 2 的失败 |
| 9 | `ch09_async_http.py`、`ch09_failures.py` | aiohttp | `python examples/ch09_failures.py` | 1 条成功，429/503/超时各一条 |
| 10 | `ch10_browser.py` | Playwright + 浏览器 | `python examples/ch10_browser.py` | `Ready` |
| 11 | `ch11_spider.py`、`ch11_follow_spider.py` | Scrapy | `python -m scrapy runspider examples/ch11_follow_spider.py -O build/follow.jsonl --loglevel ERROR` | 跟进第二页，仅导出两条有效记录 |
| 12 | `ch12_pipeline.py` | Scrapy | `python examples/ch12_pipeline.py` | 空标题被拒，双页 Spider 中该组件也已启用 |
| 13 | `ch13_robots.py` | 标准库 | `python examples/ch13_robots.py` | 私有路径 False，公开路径 True |
| 14 | `ch14_diagnostics.py` | 标准库 | `python examples/ch14_diagnostics.py` | 分别报告登录页、缺字段、重复游标 |
| 15 | `ch15_session.py` | Requests | `python examples/ch15_session.py` | `401 200` |
| 16 | `ch16_retry.py` | Requests | `python examples/ch16_retry.py` | GET 成功/停止各三次，POST 状态请求一次 |
| 17 | `ch17_binary.py` | Requests | `python examples/ch17_binary.py` | 22528 字节临时保存后发布，HTML 被拒 |
| 18 | `ch18_har.py` | 标准库 | `python examples/ch18_har.py` | 两条带开始时间和耗时的脱敏摘要 |
| 19 | `ch19_ast.js` | Node + Babel | `node examples/ch19_ast.js` | `const total = 14;` |
| 20 | `ch20_pipeline.py` | Requests + Beautiful Soup | 连续运行两次 `python examples/ch20_pipeline.py` | 每次两页、四条候选、三条正确且唯一的记录 |
| 21 | `ch21_queue.py` | 标准库 | `python examples/ch21_queue.py` | 同次运行的重复任务只计一次 |
| 22 | `ch22_config.py`、`ch22_run.py` | 标准库 + 第 20 章依赖 | `python examples/ch22_run.py --db build/job.sqlite3` | JSON 报表、失败退出码与检查点恢复 |

`tests/test_contracts.py`、`tests/test_revision.py`、`tests/test_teaching_examples.py` 断言 404、429、503、登录页、空字段、跨来源重定向、重复分页、中断恢复和重复记录。失败输出以异常类型与提示片段为准，不能把这些情况当成空记录继续写入。
