# 中国大陆访问部署

`chatgpt.site` 不是面向中国大陆公开访问的域名，可能被 Cloudflare 防护页拦截。本项目已提供独立的国内静态站点构建，不依赖后端、账号、Cookie 或任何国外 API。

## 推荐：腾讯云 EdgeOne Pages

1. 使用已完成实名认证的腾讯云账号进入 [EdgeOne Pages](https://edgeone.cloud.tencent.com/pages/)。
2. 新建项目并连接 GitHub 仓库 `LCPASSION123/ai-job-radar`。
3. 配置构建命令：`cd frontend && npm ci && npm run build:china`。
4. 配置输出目录：`frontend/dist-cn`。
5. 发布生产环境。首次发布可使用平台提供的默认域名；正式对外使用时，绑定你自己的域名。

## 备选：阿里云 OSS + CDN

先在本地执行 `cd frontend; npm.cmd run build:china`，将 `frontend/dist-cn` 内的所有文件上传至 OSS Bucket，并把默认首页设为 `index.html`。再为自有域名配置 CDN 加速并绑定该 Bucket。

若 Bucket 与 CDN 节点在中国内地，域名需完成 ICP 备案；这是中国大陆正式网站对外提供服务的法规要求，不能通过代码或自动化绕过。详见 [阿里云 OSS 静态网站托管说明](https://help.aliyun.com/zh/oss/user-guide/hosting-static-websites)。

## 公开站的数据边界

国内公开站展示的是只读示例任务、筛选与平台直达链接。你的本地导入、SQLite 数据库、浏览器采集和 MCP 分析不会上传到公开站。
