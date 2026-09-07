# 方案 A 操作手册：Cloudflare Pages 部署 Kamloops 生活服务地图

> 适用对象：把 `Kamloops生活服务地图.html` 部署成可通过 URL/二维码访问的网站，手机和电脑打开都能用。
> 所需时间：**全程 5-10 分钟**，含账号注册。
> 所需费用：**永久免费**。

---

## 速览流程

```
准备文件 → 注册 Cloudflare → 建 Pages 项目 → 拖文件上传 → 拿到 URL → 做二维码 → 发出去
   1分钟      3分钟              1分钟           30秒        10秒       1分钟
```

所有操作都在**浏览器**里完成，不需要命令行、不需要 git。

---

## 第 0 步：准备文件（1 分钟）

Cloudflare Pages 把上传到根目录的 `index.html` 当作网站首页。所以要先做一个副本改名。

### 在 Finder（macOS）里做
1. 打开 Finder，进 `Documents/me/canada/Guide to Life in Canada/`
2. **复制一份** `Kamloops生活服务地图.html`（按住 Option 拖拽 → 在同目录产生副本）
3. 把副本**改名**为 `index.html`（只改副本，原文件保留）
4. 大功告成，下一步。

### 改名后要注意
- 副本和原文件都在同一目录、互不干扰
- 原文件（中文名）不动，**只在副本上操作**
- 改名前后内容一样，只是文件名不同

### 为什么要改名
- Cloudflare Pages 的**根目录**对应的就是 URL 主入口（不带路径）
- 没有 `index.html` 就会返回 404 / 或只能通过文件名访问（很丑）

---

## 第 1 步：注册 Cloudflare（3 分钟）

> 国内访问 Cloudflare 偶有波动，可能需要稳定网络。手机号填中国大陆的 +86 大多数情况能收到短信（2024 后改善明显）。

### 推荐：GitHub 账号一键登录
1. 浏览器打开 **https://dash.cloudflare.com/**
2. 点击 **Sign Up**（或直接 Log In）→ 选择 **Continue with GitHub**
3. 浏览器跳到 GitHub → 授权 Cloudflare 访问 → 完成
4. 自动回到 Cloudflare dashboard

> GitHub 一键登录比邮箱注册快 5 倍，还能跳过邮箱验证。如果已有 GitHub 账号，这是首选。

### 备选：邮箱注册
1. **Sign Up** → 填邮箱 + 密码
2. 邮箱查收验证邮件（可能慢，5 分钟内到达）
3. 填手机号收短信验证码（+86 在多数省份可用）

### 注册后第一件事
Dashboard 默认会问"要不要添加一个网站（引导去用 DNS）"——**直接关掉它**，我们这一步只需要 Pages，不需要添加域名。点左边的 **Workers & Pages** 就到下一步。

---

## 第 2 步：创建 Pages 项目（1 分钟）

### 进入创建流程
1. 左侧菜单 → **Workers & Pages**
2. 第一次进入会看到空白页 → 点蓝色按钮 **Get started**（或 **Create application**）
3. 选择 **Pages** 卡片（不要选 Workers）
4. 在 **Set up a Pages project** 页面选第四个标签：**Direct Upload**（不是 Connect to Git）

### 填项目名
1. Project name 输入框，填你想要的名字，比如 `kamloops-map`
2. 命名规则：
   - 只能小写字母、数字、`-`
   - 全局唯一（别人已经用了的会被提示）
3. 确认你的最终域名会是：**`<你填的名字>.pages.dev`**
   - 例：填 `kamloops-map` → `https://kamloops-map.pages.dev`

### 建项目
4. 点 **Create project**
5. 进入上传页面（看到 "Upload your site files" 大标题）

---

## 第 3 步：上传文件（30 秒，最关键）

### 操作
1. 把刚才改好名的 **`index.html`** 拖进页面中央的虚线框（或者点 "Select files" 选文件）
2. 上传很快（只有 658KB），页面会显示文件大小和上传进度
3. 上传完成后，点 **Deploy site**（蓝色按钮）

### 等多久
- 单文件部署：**10-20 秒**就完事
- 完成后自动跳到项目概览页，第一行有个 **Production deployment** 绿色标签，后面有 **View project** 链接

---

## 第 4 步：拿到 URL 并测试（30 秒）

### 拿到 URL
- 项目概览页右上角就有你的 URL：`https://<项目名>.pages.dev`
- 例：`https://kamloops-map.pages.dev`
- 复制下来

### 立即测试（三端验证）
用以下三种设备/方式逐一打开这个 URL，确认能正常用：

| 设备 | 打开方式 | 期望看到 |
|---|---|---|
| **桌面浏览器** | 直接地址栏访问 | 全屏地图 + 250 个图钉 + 顶部工具条 |
| **手机浏览器** | 直接地址栏访问 | 地图自适应手机屏幕、面板可点击 |
| **手机扫码** | 系统相机/微信扫一扫 | 同上 |

**如果三个都正常**：恭喜，部署完成 🎉

### 测试清单
- [ ] 地图瓦片能加载（看得见街道/卫星图）
- [ ] 顶部"类别 / 区域 / 公交 / 语言 / 分享 / 收藏"按钮都在
- [ ] 点击图钉能弹出地点详情弹窗
- [ ] 切换语言（上 ZH / 下 EN）文案随之变化
- [ ] 刷新页面后筛选/语言能保留吗？（**默认不会保留**——见 FAQ #4）

---

## 第 5 步：生成二维码（30 秒）

任选一种：

### 方式 A：在线生成（最简单）
1. 浏览器打开 **https://www.qrcode-monkey.com/**
2. 顶部把选 "URL" tab
3. 粘贴你的 URL → 右侧立刻生成预览
4. 点 **Create QR Code** → 下载 PNG / 打印
5. 用微信扫一扫测试能否识别

### 方式 B：命令行（顺手）
```bash
brew install qrencode                    # 一次性安装
qrencode -o kamloops-qr.png "https://kamloops-map.pages.dev"
open kamloops-qr.png                     # 立即预览
```

### 方式 C：手机自带二维码
- iPhone：长按相册里"URL 文本"→ "显示二维码"

### 在哪里展示二维码
- 微信群、邮件签名、社区公告栏
- A4 纸打印，贴在超市/教会/补习班门口
- 嵌入 PPT 第二页"扫码查看"

---

## 第 6 步（可选）：绑定自己的域名

比如你有 `yourdomain.com`，想让 URL 变成 `map.yourdomain.com`。

### 在 Cloudflare 配置
1. 项目页 → **Custom domains** 标签 → **Set up a custom domain**
2. 输入 `map.yourdomain.com` → **Continue**
3. Cloudflare 会告诉你需要去域名注册商加一条 DNS 记录（一般是 CNAME）
4. 在域名注册商（阿里云 / Cloudflare Registrar / Namecheap 等）添加：
   - 类型：**CNAME**
   - 主机记录：**map**
   - 记录值：**`<项目名>.pages.dev`**
5. 回到 Cloudflare → **Activate domain**
6. SSL 自动配置，5-15 分钟生效

### 注意事项
- Cloudflare 自动签发免费 SSL（HTTPS）
- 不需要手动申请证书
- 自定义域名也完全免费

---

## 常见问题（FAQ）

### #1 国内访问 Cloudflare 慢 / 加载不出来？
Cloudflare Pages**对中国大陆访问速度中等**（比 GitHub Pages 好很多，但比腾讯云/阿里云慢）。
- **境外读者**主导：完全没问题
- **境内读者**主导：考虑方案 C（腾讯云/阿里云）或自建 VPS

### #2 上传时浏览器显示"文件名包含特殊字符"？
- 不要上传**原文件名**（含中文标点会被部分浏览器弹警告）
- **一定要用改名后的 `index.html`**

### #3 部署好了，但打开是 404？
99% 是**没把文件改名为 `index.html`**，或者上传的不是改名后的那个文件。
- 回到 Cloudflare 项目 → **Deployments** 标签
- 看文件列表：有没有 `index.html`？大小是不是 658K 左右？
- 没有就 **Retry deployment** 再上传一次

### #4 筛选/语言切换后刷新就丢了？
这是已知的应用层问题（不是部署问题）——`localStorage` 只存了收藏，没存筛选/语言。属于之前 UX 审计里的待修复项。需要后端支持时再说。

### #5 部署后怎么更新？
1. 项目概览页 → **Create new deployment** 按钮
2. 改完的文件拖进去 → **Deploy**
3. URL 不变，自动覆盖，几秒生效

### #6 多个城市的文件能在同一个站点部署吗？
可以。所有 `*.html` 文件都能直接传（除了 `index.html` 推荐的是首页）：
- `index.html`（Kamloops）→ 根路径
- `kelowna.html` → `https://xxx.pages.dev/kelowna`
- `vancouver.html` → `https://xxx.pages.dev/vancouver`

### #7 自带数据是中文/英文，可以改吗？
可以。改完后用 `python3 build.py --out ...` 重新构建后上传。或者直接改 `src/data-kamloops.js` 然后重建。

### #8 上传大小有上限？
Cloudflare Pages 单文件**最大 25 MB**，我们这是 658KB，**余量还很够**。

---

## 完整体验小结

发布给别人的时候，建议把下面这段话直接发给使用人：

> 📍 **Kamloops 生活服务地图**已上线！
> 网址：**https://kamloops-map.pages.dev**
> 手机扫码 / 电脑浏览器直接打开都能用。
> 内置 250+ 个新移民常用地点（银行、医院、超市、学校、公交线），全部离线缓存、下飞机没网也能点开（只有地图底图需联网）。
>
> 建议：先用顶部"类别"和"区域"过滤一下，再"收藏"下次常去的地方。

---

## 全部操作复盘（按时间顺序）

| # | 在哪操作 | 做什么 | 时长 |
|---|---|---|---|
| 1 | Finder | 复制 `Kamloops生活服务地图.html` → 改名 `index.html` | 1 分钟 |
| 2 | dash.cloudflare.com | GitHub 一键登录 / 邮箱+手机注册 | 3 分钟 |
| 3 | Workers & Pages → Create → Pages → Direct Upload | 填项目名（如 kamloops-map），点 Create | 1 分钟 |
| 4 | 上传页面 | 拖 `index.html` 进虚线框 → Deploy | 30 秒 |
| 5 | 项目页 | 拿到 `https://<项目名>.pages.dev` | — |
| 6 | 手机/电脑浏览器 | 测试 + 验证可访问 | 1 分钟 |
| 7 | qrcode-monkey.com | 输入 URL 生成二维码下载 | 30 秒 |
| 8 | 微信群 / 邮件 / 公告栏 | 发二维码 + URL | 1 分钟 |

**合计：10 分钟左右**，全程不需要任何技术背景，不会的话随时问我具体某一步卡在哪里。
