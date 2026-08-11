# 安全说明

## 报告安全问题

如果你认为本仓库存在可被滥用的漏洞（例如凭据被写入仓库、危险默认行为、可导致密钥泄露的脚本路径），请优先通过 GitHub 的 **Security Advisory**（仓库 Security 页）私下报告；也可以开 Issue，但请**不要**在 Issue 里粘贴真实密钥、token、cookie 或完整接口响应。

本仓库维护者不在公开讨论里接收明文凭据。

## 凭据放置约定

- 密钥只放在**环境变量**，或用户家目录下权限为 `600` 的本地文件（例如 `~/.secrets.zsh`，由 `~/.zshenv` 加载）。
- **不要**把密钥写进仓库、知识库、聊天记录、截图或可见命令行参数。
- 已经出现在 shell 历史或对话里的 key，视为已泄漏，应去对应服务商后台轮换。
- 更细的「放哪、怎么自查」见 [docs/环境与能力.md](docs/环境与能力.md)。

## 本仓库不含任何密钥

跟踪内容经过公开前扫描，目标状态是：

- 无硬编码 API key / token / 私钥
- 无真实微信 AppID / AppSecret
- 无真实公网出口 IP、SSH 主机名或私人邮箱
- 构建产物与过程目录被 ignore：`dist/`、`_work/`
- 常见凭据文件名被 ignore：`.env*`、`*.pem`、`**/auth.json`、`**/.jing-wechat/`、`**/fixed-egress.json` 等（见 `.gitignore`）

如果你在 clone 后的工作区里看到上述文件，它们应来自**你本机本地配置**，不应被 `git add`。

## Skill 会接触什么（使用面披露）

仓库本身不持有你的账号。以下 Skill 在**你本机已配置凭据或已登录**时，会按设计接触这些材料——这是 BYOK / 本机会话能力，不是仓库内嵌密钥：

| Skill | 会接触什么 | 说明 |
|---|---|---|
| `jing-wechat` | `WECHAT_APPID` / `WECHAT_SECRET` 或 `~/.jing-wechat/config.yaml`；可选固定 SSH 出口（`~/.jing-wechat/fixed-egress.json`） | 仅在你明确要求写草稿时调公众号草稿接口；默认不发布、不群发。接口错误路径会尝试脱敏 secret / token。 |
| `jing-x-article` | 你已登录的浏览器会话 | 用于写入 X Articles **草稿**；不读取或导出 cookie 明文；不点 Publish。 |
| `jing-multimodel` | 本机 Grok CLI 登录态（`~/.grok` 下的 `auth.json` 副本） | 复制到隔离临时 HOME 做只读搜索，用后删除；会主动丢弃无关的 `XAI_API_KEY` 等，避免误走计费 API。详见 `skills/jing-multimodel/references/grok-search-reliability.md`。 |
| `jing-broll` | `GEMINI_API_KEY`、可选 `FAL_KEY` | 标准 BYOK。请用环境变量；CLI `--api-key` 已标记废弃（会出现在进程列表里）。 |
| `jing-cover` / `jing-writer` 配图 | 宿主已登录的图片后端（如 codex-image）或 `GEMINI_API_KEY` | 不内置密钥。 |

安装本工具箱不等于授权任何 Agent 发布内容或转移资产；平台写入与发布仍以各 Skill 文档中的用户确认为准。

## 公开前检查清单

维护者在将本仓库设为 public 之前，应确认：

- [ ] `git ls-files` 中无硬编码密钥、token、私钥
- [ ] 无真实公网 IP、私人邮箱、微信 AppID
- [ ] `dist/` 与 `_work/` 被 ignore，且未被 force-add
- [ ] `.env*`、`auth.json`、`.jing-wechat/`、`fixed-egress.json` 被 ignore
- [ ] broll 脚本不把 CLI 传 key 当作推荐路径（仅 env；`--api-key` 若保留则已 DEPRECATED）
- [ ] `SECURITY.md` 与 README 文档区互相可发现
- [ ] 不在公开说明里粘贴本机运维实测值（出口 IP、SSH 别名等只用占位符）
- [ ] GitHub 已启用 Secret scanning / Push protection（公开后）
- [ ] 公开操作为显式修改 visibility；本清单通过 ≠ 已自动公开

## 许可

安全说明文件与仓库主体相同，遵循根目录 [LICENSE](LICENSE)（CC BY-NC 4.0）；第三方组件许可见各自目录。
