# outreach/ — 对外材料的源文件与构建脚本

2026-10-04 从 `docs/source/`、`flyers/` 和根目录的 `logo.svg` 合并到这里：`docs/` 只放文档，对外材料单独一处。
**成品（PDF、传单、邮件）不在仓库里**，在运营资料目录 `../Guide to Life in Canada - ops/`（决策 D4）。

| 路径 | 是什么 |
|---|---|
| `pdf/content/*.txt` | 对外说明文档的正文（中英各四份：brief、quickstart、detailed、complete）。数字用占位符，构建时现取 |
| `pdf/assets/` | 文档里的截图；界面改版后重拍 |
| `pdf/builddocs.py` | 构建 HTML / PDF；**只在部署之后**（对照线上版本号，不一致就拒绝）；`--html-only` 只出 HTML 到 `pdf/_build/` |
| `flyers/buildflyer.py`、`flyers/mapart.py` | 传单、海报、二维码卡片、地图插画（目前只做 Kamloops，网址写死） |
| `logo.svg` | 标志原稿；`app/pwa/icon.svg` 是同一个图形加底色和留白 |

用法和规则见 `docs/README.md` 第四节"对外材料（PDF）怎么做"。功能改了，要回来检查这里的文字（经验 L-082）。
