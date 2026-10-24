# AI Newcomer Assistant（KIS 工作人员试用）

KIS 工作人员用任何语言提问，助手**只根据 Kamloops 生活指南里已核实的内容**回答，每一步附来源和核实日期。
产品与设计说明见 `docs/assistant/AI-Newcomer-Assistant-产品与设计说明.md`；开发记录见 `docs/assistant/开发记录.md`。

2026-10-24 起**公开**（像生活指南一样任何人都能用，`PUBLIC = "1"`）；界面六种语言，默认英文。

和生活指南完全分开：独立的 Worker（`kamloops-assistant`）和网址（`kamloops-assistant.neilxiang.workers.dev`）。
指南的代码、网址、隐私承诺都不变；助手只**读**指南的数据（构建时生成，不另存副本）。

## 一次提问怎么走

```
提问 ─→ 危机识别（指南的规则 + 第三人称说法）── 命中 → 直接给求助电话，不调用 AI
     ─→ 检索：全部办事卡 + 相关地点 + 热线
     ─→ Claude（只许根据这些内容回答，每步标来源编号，按固定 JSON 格式）
     ─→ 程序校验：来源编号必须是本次给的；电话、网址必须出自它引用的来源；否则删掉这一步
     ─→ 回答 + 来源（名称、链接、核实日期全部由程序从数据里取）
```

## 文件

| 文件 | 作用 |
|---|---|
| `build.py` | 从 `cities/kamloops/` 和引擎生成 `build/knowledge.json`、`build/crisis.js`（不入仓） |
| `src/retrieve.js` | 检索（中日韩按两字、拉丁字母按词，BM25） |
| `src/prompt.js` | 给 Claude 的规则、指南内容排版、回答格式 |
| `src/ground.js` | 程序校验（来源、电话、网址、过期提醒、翻译核对） |
| `src/crisis.js` | 危机识别：指南的规则 + 工作人员第三人称的说法 |
| `src/assistant.js` | 一次提问的完整流程（和网络无关，测试直接调用） |
| `src/claude.js` | 调用 Claude API（官方 SDK） |
| `src/access.js` | 登录校验：Cloudflare Access；没配好时线上一律拒绝 |
| `src/worker.js` | Worker：页面、`/api/ask`、`/api/quota`（今天还剩几题）、`/api/translate`（只在工作人员版）、`/api/feedback`、`/api/health` |
| `src/limits.js` | 公开版的费用保护：每人每天 10 题、每分钟 5 题、全站每天 200 题（只存 IP+日期的散列） |
| `public/` | 界面和隐私说明（六种语言：中、英、法、西、韩、日） |
| `tests/` | 把关测试，用假模型，不花钱 |
| `eval/` | 用真实 Claude 跑的测试题（花钱） |

## 本机运行

```sh
cd assistant
npm install                      # 只装 @anthropic-ai/sdk；wrangler 用仓库根目录的
python3 build.py
node --test tests/*.test.mjs     # 把关测试：假模型，不调用 Claude，可随便重复
# 本机密钥：~/.anthropic_key（chmod 600）。生成 .dev.vars（不入仓）：
umask 077; printf 'ANTHROPIC_API_KEY=%s\n' "$(cat ~/.anthropic_key)" > .dev.vars
../node_modules/.bin/wrangler dev --local --port 8787   # http://localhost:8787
```

## 真实测试题（花钱）

```sh
node eval/run.mjs --dry          # 先看要跑哪些、预计多少钱
node eval/run.mjs                # 默认只跑 smoke 的 3 道（约 $0.10；Neil：测试用 AI 只跑 3 题）
node eval/run.mjs q10 q18        # 只跑指定的题
node eval/run.mjs --regrade eval/results/<文件>.json   # 改了评分规则：用保存的回答重评，不调用
```

全部 30 道约 $1.5，跑之前先问 Neil。危机题不调用 AI，免费。

## 上线（每次都要 Neil 同意）

**1. 开 Access（Neil 在 Cloudflare 网页上操作，一次性）**

1. Cloudflare 后台 → **Workers & Pages** → 选 `kamloops-assistant`（第一次部署后才会出现）→ **Access** 标签页；
2. 选 **Protect this Worker behind Access** → **All traffic**；
3. **Authentication policy**：建一个只包含指定邮箱的策略（Zero Trust → Access → Policies → Include → **Emails**，填 Neil 和 KIS 试用人员的邮箱）；
4. **Apply Access**。之后打开网址会先要求输入邮箱、收验证码登录。

Worker 用 `ctx.access` 确认请求已通过 Access；没通过的一律 403。
（备用：若 `ctx.access` 不可用，在 Zero Trust 里找到应用的 AUD 和团队名，`wrangler secret put ACCESS_AUD` / `ACCESS_TEAM`，Worker 会自己验证令牌签名。）

**为了不出现"没开 Access 就能访问"的空档**：Access 没开时，线上所有页面和接口都返回 403。所以顺序是：先部署（此时谁都打不开）→ 开 Access → 登记邮箱 → 自己登录试一次。

**2. 部署**

```sh
cd assistant && python3 build.py && node --test tests/*.test.mjs
../node_modules/.bin/wrangler secret put ANTHROPIC_API_KEY < ~/.anthropic_key
../node_modules/.bin/wrangler deploy
```

**3. 费用保护**：Worker 每日上限 `DAILY_LIMIT`（默认 200 次）；Anthropic Console 预充值 + 月度上限。

## 指南更新后

重新 `python3 build.py` 并部署，助手就读到新内容。危机规则也从指南的引擎里重新抄，测试会检查两边是否一致。
