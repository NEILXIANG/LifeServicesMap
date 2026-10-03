#!/usr/bin/env bash
# deploy.sh — Kamloops Life Map 的「Worker + 静态资源」部署自动化脚本
# ============================================================================
# Phase A 起：部署形态从「拖 zip 到 Dashboard」改为「wrangler deploy」。
#   - 因为 Worker 现在带了 Analytics Engine binding + ASSETS binding，
#   - 这两种 binding 必须在 wrangler.toml 里声明、随 Worker 代码一起上传，
#   - CF Dashboard 的 "Direct Upload" 模式不支持这些 binding 的拖拽上传。
#
# 流程：
#   build  →  wrangler login 检查  →  wrangler deploy  →
#   跑线上探针（首页 + /api/event + 敏感文件全 404）
#
# 用法：
#   ./deploy.sh                    # 重建 + 部署 + 验证（推荐）
#   ./deploy.sh --no-build         # 跳过构建，仅部署当前 public/index.html
#   ./deploy.sh --verify-only      # 仅跑线上验证脚本（不动本地）
#   ./deploy.sh --login            # 仅做 wrangler login（首次部署前必跑）
#
# 依赖：python3、npx（或全局 wrangler）、curl
# 一次性：第一次跑会提示 `npx -y wrangler login` 完成 CF 账户授权。
# ============================================================================
set -euo pipefail

# 本次运行专属的临时文件，退出时清掉；固定路径会让 curl 失败时
# 把上一轮残留的文件当成这次的线上页面来读。
IDX_TMP="$(mktemp -t deploy-idx.XXXXXX)"
trap 'rm -f "$IDX_TMP"' EXIT

# ---- 路径与常量 -----------------------------------------------------------
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
INDEX_FILE="${PROJECT_ROOT}/public/index.html"
BUILD_SCRIPT="${PROJECT_ROOT}/build.py"
WRANGLER_TOML="${PROJECT_ROOT}/wrangler.toml"
WORKER_FILE="${PROJECT_ROOT}/worker.js"
DEPLOY_URL="https://kamloops-lifemap.neilxiang.workers.dev"

# ---- 颜色（终端醒目）------------------------------------------------------
RED='\033[0;31m'; GRN='\033[0;32m'; YEL='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
say()   { printf "${CYAN}▸ %s${NC}\n" "$*"; }
ok()    { printf "${GRN}✓ %s${NC}\n" "$*"; }
WARN_COUNT=0
warn()  { WARN_COUNT=$((WARN_COUNT+1)); printf "${YEL}⚠ %s${NC}\n" "$*"; }
fail()  { printf "${RED}✗ %s${NC}\n" "$*" >&2; exit 1; }

# ---- 参数解析 --------------------------------------------------------------
NO_BUILD=0
VERIFY_ONLY=0
LOGIN_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build)     NO_BUILD=1; shift ;;
    --verify-only)  VERIFY_ONLY=1; shift ;;
    --login)        LOGIN_ONLY=1; shift ;;
    -h|--help)
      sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) fail "未知参数: $1  （用 --help 看用法）" ;;
  esac
done

# ---- 跨平台毫秒时间戳 ------------------------------------------------------
# macOS ships BSD date, which has no %3N (that is a GNU extension). Building
# the timestamp with python3 keeps the probe payload valid JSON everywhere —
# an invalid "d" makes the Worker reject the event with 400 and the probe
# reports a false failure.
now_ms() {
  python3 -c 'import time;print(int(time.time()*1000))'
}
# Wrangler 版本锁在 package.json 里（2026-10-03 起），`npm install` 装到本项目的
# node_modules/。查找顺序：项目内 → PATH 上的 wrangler → npx 临时下载。
# 不再写死任何本机路径，换电脑、换人都能直接跑。
LOCAL_WRANGLER="${PROJECT_ROOT}/node_modules/.bin/wrangler"
if [[ -x "$LOCAL_WRANGLER" ]]; then
  WRANGLER_CMD() { "$LOCAL_WRANGLER" "$@"; }
elif command -v wrangler >/dev/null 2>&1; then
  warn "项目内没有 wrangler（先跑 npm install），改用 PATH 上的 $(command -v wrangler)"
  WRANGLER_CMD() { wrangler "$@"; }
elif command -v npx >/dev/null 2>&1; then
  warn "项目内没有 wrangler（先跑 npm install），将通过 npx 下载（约 30s）"
  WRANGLER_CMD() { npx -y wrangler "$@"; }
else
  fail "找不到 wrangler 也找不到 npx；请先装 Node，然后在项目目录跑 npm install"
fi

# ---- verify-only / login-only 快捷路径 -------------------------------------
if [[ $VERIFY_ONLY -eq 1 ]]; then
  say "[verify-only] 跑线上探针"
  echo
  # 1. 首页 200 + DATA_VERSION
  curl -s -o "$IDX_TMP" -w '  HTTP %{http_code}\n' "${DEPLOY_URL}/"
  INDEX_VER=$(grep -oE "DATA_VERSION=[^,]+" "$IDX_TMP" 2>/dev/null | head -1 || echo "DATA_VERSION=?")
  INDEX_TRACK=$(grep -o "trackEvent(" "$IDX_TMP" 2>/dev/null | wc -l | tr -d " ")
  INDEX_BEACON=$(grep -o "sendBeacon" "$IDX_TMP" 2>/dev/null | wc -l | tr -d " ")
  ok "首页  ${INDEX_VER}  trackEvent=${INDEX_TRACK}  sendBeacon=${INDEX_BEACON}"
  # 2. /api/event GET → 404. The Worker only handles POST here; a GET falls
  #    through to env.ASSETS, which has no such file, so 404 proves the Worker
  #    ran rather than the request being swallowed by static hosting.
  EP_CODE=$(curl -s -o /dev/null -w '%{http_code}' "${DEPLOY_URL}/api/event")
  if [[ "$EP_CODE" == "404" ]]; then ok "/api/event GET → 404（Worker 已接管，GET 落到 ASSETS）"; else warn "/api/event GET → ${EP_CODE}"; fi
  # 3. /api/event POST → 200
  POST_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H "Origin: ${DEPLOY_URL}" \
    --data "{\"t\":\"ping\",\"p\":{\"source\":\"verify-only\",\"env\":\"dev\"},\"d\":$(now_ms),\"sid\":\"verify-script\"}" \
    "${DEPLOY_URL}/api/event")
  if [[ "$POST_CODE" == "200" ]]; then ok "/api/event POST → 200（事件已写入 Analytics Engine）"; else warn "/api/event POST → ${POST_CODE}"; fi
  # 3b. 2026-09-11: a POST from another origin must be refused (403)
  XO_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H 'Origin: https://example.org' \
    --data '{"t":"ping","p":{},"sid":"verify-script"}' "${DEPLOY_URL}/api/event")
  if [[ "$XO_CODE" == "403" ]]; then ok "/api/event 跨站 POST → 403（Origin 校验生效）"; else warn "/api/event 跨站 POST → ${XO_CODE}（应为 403）"; fi
  # 3c. security headers on the page
  # || true：grep 零匹配时退出码 1，set -e 会直接杀掉脚本，
  # 于是"缺少 CSP"这条警告永远不可能打印出来
  HDRS=$(curl -s -D - -o /dev/null "${DEPLOY_URL}/")
  for h in content-security-policy x-content-type-options x-frame-options referrer-policy; do
    if grep -qi "^${h}:" <<<"$HDRS"; then ok "首页带 ${h}"; else warn "首页缺少 ${h}"; fi
  done
  # 对照一组：没有对应静态文件的路径会真正进 Worker。
  # 如果这里有头、首页没有，说明静态资源根本没经过 Worker（[assets] 的默认行为），
  # withSecurityHeaders 对首页从来没生效过。
  if ! grep -qi '^content-security-policy:' <<<"$HDRS" \
     && curl -s -D - -o /dev/null "${DEPLOY_URL}/__no_such_asset__" | grep -qi '^content-security-policy:'; then
    warn "安全头只在 Worker 响应上有，静态首页绕过了 Worker —— 见 wrangler.toml 的 [assets]"
  fi
  # 4. 敏感路径应全 404
  PATHS=(
    "data/business-hypothesis.md" ".git/HEAD" ".git/config"
    ".workbuddy/memory/2026-09-04.md" "src/engine.html" "app/engine/parts.txt" "cities/kamloops/places.json" "scripts/validate.py"
    "package-lock.json" "README.md" "wrangler.toml" "worker.js"
  )
  FAIL=0
  for p in "${PATHS[@]}"; do
    code=$(curl -s -o /dev/null -w '%{http_code}' "${DEPLOY_URL}/$p")
    [[ "$code" == "404" ]] && ok "404  /$p" || { warn "$code  /$p"; FAIL=$((FAIL+1)); }
  done
  echo
  if [[ $FAIL -gt 0 ]]; then
    warn "${FAIL} 个敏感路径没有返回 404"
  fi
  # 警告也要算数：上面任何一条 ⚠ 都说明线上和预期不一致
  if [[ $WARN_COUNT -eq 0 ]]; then
    ok "全部检查通过"
    exit 0
  else
    warn "有 ${WARN_COUNT} 项不符合预期（见上面的 ⚠），不能算通过"
    exit 1
  fi
fi

if [[ $LOGIN_ONLY -eq 1 ]]; then
  say "[login] 引导 wrangler 登录 CF 账户"
  echo "  这会跳浏览器到 CF 授权页面；登录后会回到终端。"
  WRANGLER_CMD login
  WRANGLER_CMD whoami
  ok "登录完成，下次部署直接跑 ./deploy.sh"
  exit 0
fi

# ---- 步骤 1：构建 ---------------------------------------------------------
if [[ $NO_BUILD -eq 0 ]]; then
  say "[1/5] 运行 build.py 重建 public/index.html"
  if [[ ! -f "$BUILD_SCRIPT" ]]; then fail "找不到 ${BUILD_SCRIPT}"; fi
  python3 "$BUILD_SCRIPT" --city kamloops --out "$INDEX_FILE"
  ok "构建完成"
else
  say "[1/5] 跳过构建（--no-build），使用现有 ${INDEX_FILE}"
  [[ -f "$INDEX_FILE" ]] || fail "${INDEX_FILE} 不存在，先去掉 --no-build 跑一次"
fi

# ---- 步骤 1.5：静态校验（2026-09-07 新增）--------------------------------
# 2026-09-05 那次部署把 19 项校验失败带上了线：4 条记录用了 CI 里不存在的分类
# key，popup() 取 CI[c][L_] 抛异常，初始化循环中断，整页文案全空。validate.py
# 本来就能查出全部 19 项，只是从来没有出现在部署路径里。现在它是一道硬闸门。
if [[ "${VALIDATE_SKIP:-0}" == "1" ]]; then
  warn "[1.5/5] 已按 VALIDATE_SKIP=1 跳过静态校验"
else
say "[1.5/5] 运行 validate.py（校验不过就不部署）"
VALIDATE_PY="${PROJECT_ROOT}/scripts/validate.py"
if [[ ! -f "$VALIDATE_PY" ]]; then
  fail "找不到 ${VALIDATE_PY} — 这道闸门不能跳过"
fi
if ! python3 "$VALIDATE_PY" "$INDEX_FILE"; then
  fail "validate.py 未通过，已中止部署（要临时跳过：VALIDATE_SKIP=1 ./deploy.sh，仅限你清楚后果时）"
fi
ok "校验通过"
fi

# ---- 步骤 2：核对产物 + 部署配置 -----------------------------------------
say "[2/5] 核对产物与 wrangler 配置"
[[ -f "$INDEX_FILE" ]]     || fail "缺 ${INDEX_FILE}"
[[ -f "$WRANGLER_TOML" ]]  || fail "缺 ${WRANGLER_TOML}"
[[ -f "$WORKER_FILE" ]]    || fail "缺 ${WORKER_FILE}"

DATA_VERSION=$(grep -oE "DATA_VERSION=[^,;]+" "$INDEX_FILE" | head -1 || true)
[[ -n "$DATA_VERSION" ]] || fail "index.html 里找不到 DATA_VERSION — 是不是旧文件？"
SIZE_BYTES=$(wc -c < "$INDEX_FILE" | tr -d ' ')
SIZE_KB=$(( (SIZE_BYTES + 1023) / 1024 ))
ok "MD5     $({ md5 -q "$INDEX_FILE" 2>/dev/null || md5sum "$INDEX_FILE" | cut -d" " -f1; })"
ok "版本    ${DATA_VERSION}"

# 2026-09-22: the 22 Sept release went live still calling itself 2026.09.13f, so
# nine days of old-version events and the new version's could not be told apart.
# If the page differs from what is live, its DATA_VERSION must differ too.
LOCAL_VER=$(grep -oE "DATA_VERSION='[^']+'" "$INDEX_FILE" | head -1 || true)
LIVE_TMP="$(mktemp -t deploy-live.XXXXXX)"
if curl -s -o "$LIVE_TMP" -w '' "${DEPLOY_URL}/" 2>/dev/null && [[ -s "$LIVE_TMP" ]]; then
  LIVE_VER=$(grep -oE "DATA_VERSION='[^']+'" "$LIVE_TMP" | head -1 || true)
  LIVE_MD5=$({ md5 -q "$LIVE_TMP" 2>/dev/null || md5sum "$LIVE_TMP" | cut -d" " -f1; })
  LOCAL_MD5=$({ md5 -q "$INDEX_FILE" 2>/dev/null || md5sum "$INDEX_FILE" | cut -d" " -f1; })
  rm -f "$LIVE_TMP"
  if [[ "$LIVE_MD5" != "$LOCAL_MD5" && -n "$LIVE_VER" && "$LIVE_VER" == "$LOCAL_VER" ]]; then
    fail "页面内容变了，但版本号仍是 ${LOCAL_VER}（和线上相同）— 先改 app/engine/js/20-versions-templates-tasks.js 里的 DATA_VERSION"
  fi
  ok "线上    ${LIVE_VER:-未知}  →  本次 ${LOCAL_VER}"
else
  rm -f "$LIVE_TMP"; warn "读不到线上页面，跳过版本号比对"
fi
ok "大小    ${SIZE_BYTES} 字节 (${SIZE_KB} KB)"
ok "Worker  $(basename "$WORKER_FILE") + $(basename "$WRANGLER_TOML")"

# ---- 步骤 3：wrangler 登录检查 -------------------------------------------
say "[3/5] wrangler 登录检查"
if ! WRANGLER_CMD whoami >/dev/null 2>&1; then
  warn "wrangler 未登录。即将自动引导登录..."
  echo
  echo "  提示：首次部署需要把 wrangler 绑定到 CF 账户。"
  echo "  下一步会在浏览器里打开 CF 授权页，登录后回到终端继续。"
  echo
  WRANGLER_CMD login
  WRANGLER_CMD whoami
fi
ok "wrangler 已登录"

# ---- 步骤 4：wrangler deploy ----------------------------------------------
say "[4/5] wrangler deploy（Worker + Assets + Analytics Engine binding 一起发布）"
# Analytics Engine has to be switched on once per Cloudflare account before a
# Worker that binds to it can be created. Wrangler's raw error for this is a
# wall of red API stack trace, so catch it and print the fix instead.
DEPLOY_LOG=$(mktemp)
set +e
WRANGLER_CMD deploy 2>&1 | tee "$DEPLOY_LOG"
DEPLOY_RC=${PIPESTATUS[0]}
set -e
if [[ $DEPLOY_RC -ne 0 ]]; then
  if grep -q "10089\|enable Analytics Engine" "$DEPLOY_LOG"; then
    echo
    printf "${YEL}══════════════════════════════════════════════════════════════════${NC}\n"
    printf "${YEL} Analytics Engine 还没在这个 CF 账户里启用（免费功能，只需启用一次）${NC}\n"
    printf "${YEL}══════════════════════════════════════════════════════════════════${NC}\n"
    echo
    echo "  1. 打开：https://dash.cloudflare.com/d25d00a8131224f4d2caf2165d134db0/workers/analytics-engine"
    echo "  2. 点 Enable / Set up（免费额度 100K 事件/天，本项目用不到 5%）"
    echo "  3. 回来重跑：./deploy.sh"
    echo
    printf "${YEL} 注意：静态资源已经上传成功，只是 Worker script 版本创建失败了，${NC}\n"
    printf "${YEL}       所以线上目前还是旧版本 —— 启用后重跑即可切换。${NC}\n"
    echo
    rm -f "$DEPLOY_LOG"
    exit 1
  fi
  rm -f "$DEPLOY_LOG"
  fail "wrangler deploy 失败（退出码 ${DEPLOY_RC}），看上面的错误信息"
fi
rm -f "$DEPLOY_LOG"

# ---- 步骤 5：线上验证 ---------------------------------------------------
say "[5/5] 等待 3 秒让边缘生效 + 跑线上探针"
sleep 3
echo

# 首页
INDEX_CODE=$(curl -s -o "$IDX_TMP" -w '%{http_code}' "${DEPLOY_URL}/")
INDEX_VER=$(grep -oE "DATA_VERSION=[^,]+" "$IDX_TMP" 2>/dev/null | head -1 || echo "DATA_VERSION=?")
INDEX_TRACK=$(grep -o "trackEvent(" "$IDX_TMP" 2>/dev/null | wc -l | tr -d " ")
INDEX_BEACON=$(grep -o "sendBeacon" "$IDX_TMP" 2>/dev/null | wc -l | tr -d " ")
LIVE_NOW=$(grep -oE "DATA_VERSION='[^']+'" "$IDX_TMP" 2>/dev/null | head -1 || true)
if [[ "$INDEX_CODE" == "200" && -n "$LOCAL_VER" && "$LIVE_NOW" != "$LOCAL_VER" ]]; then
  warn "线上版本 ${LIVE_NOW:-未知} 与本次 ${LOCAL_VER} 不一致 — 可能是边缘缓存还没生效，稍后跑 bash deploy.sh --verify-only 再看"
fi
if [[ "$INDEX_CODE" == "200" ]]; then
  ok "首页 200  ${INDEX_VER}  trackEvent=${INDEX_TRACK}  sendBeacon=${INDEX_BEACON}"
else
  warn "首页 ${INDEX_CODE}  — 部署可能没成功"
fi

# /api/event GET → 404. The Worker only handles POST; a GET falls through to
# env.ASSETS which has no such file, so 404 proves the Worker ran rather than
# the request being swallowed by static hosting.
GET_CODE=$(curl -s -o /dev/null -w '%{http_code}' "${DEPLOY_URL}/api/event")
[[ "$GET_CODE" == "404" ]] && ok "/api/event GET → 404（Worker 已接管，GET 落到 ASSETS）" || warn "/api/event GET → ${GET_CODE}"

POST_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H "Origin: ${DEPLOY_URL}" \
  --data "{\"t\":\"deploy_smoke\",\"p\":{\"source\":\"deploy.sh\",\"env\":\"dev\"},\"d\":$(now_ms),\"sid\":\"deploy-smoke\"}" \
  "${DEPLOY_URL}/api/event")
[[ "$POST_CODE" == "200" ]] && ok "/api/event POST → 200（事件已被 Analytics Engine 接受）" || warn "/api/event POST → ${POST_CODE}"

# A malformed payload must be rejected with 400 — this is the guard that keeps
# junk out of the Analytics Engine dataset.
BAD_CODE=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H "Origin: ${DEPLOY_URL}" \
  --data '{"t":"NOT VALID!!"}' "${DEPLOY_URL}/api/event")
[[ "$BAD_CODE" == "400" ]] && ok "/api/event 非法 payload → 400（正确拒绝）" || warn "/api/event 非法 payload → ${BAD_CODE}"

# 敏感路径全 404
PATHS=(
  "data/business-hypothesis.md" ".git/HEAD" ".git/config"
  ".workbuddy/memory/2026-09-04.md" "src/engine.html" "app/engine/parts.txt" "cities/kamloops/places.json" "scripts/validate.py"
  "package-lock.json" "README.md" "wrangler.toml" "worker.js"
)
LEAKED=0
for p in "${PATHS[@]}"; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "${DEPLOY_URL}/$p")
  [[ "$code" == "404" ]] && ok "404  /$p" || { warn "$code  /$p   ← 还暴露"; LEAKED=$((LEAKED+1)); }
done

echo
printf "${GRN}══════════════════════════════════════════════════════════════════${NC}\n"
if [[ "$INDEX_CODE" == "200" && "$POST_CODE" == "200" && $LEAKED -eq 0 ]]; then
  printf "${GRN} ✅ Phase A 部署完成 + 端点验证通过${NC}\n"
  printf "${GRN}    现在可以打开 ${DEPLOY_URL} 试用 → 几秒后查 CF Dashboard 看事件${NC}\n"
else
  printf "${RED} ⚠ 还有问题，看上面 ✗ 标记${NC}\n"
fi
printf "${GRN}══════════════════════════════════════════════════════════════════${NC}\n"