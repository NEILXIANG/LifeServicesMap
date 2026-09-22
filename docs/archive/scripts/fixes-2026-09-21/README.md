# 2026-09-21/22 按全面检查结论修复的补丁脚本（已应用，勿重复运行）

这些脚本已经应用到 `src/`，这里只保存作为出处记录：每条改动的依据都写在脚本注释里。

注意：每个脚本对要替换的原文都做了"恰好出现一次"的断言。如果再运行一次，会在第一处断言失败并退出，不会重复修改。

| 脚本 | 阶段 |
|---|---|
| p1_patch.py | 安全与信任：危机词、求助按钮、隐私、共用设备、热线、移民措辞 |
| p2_patch.py | 47 条严重数据问题，以及税务卡 |
| p3_patch.py | 法定假日、需预约地点、"收录于 / 已核实"标注 |
| p4_patch.py | ⭐ 移出名称、公园条例时间、戏水池、门店链接、银行时间 |
| p5_patch.py | 办事卡条件；小学入学材料说明 |
| p6_patch.py, p6b_patch.py | 覆盖补充：法律援助、精神健康、女性安全、StrongStart、CDCP、南亚社区、冬季庇护所 |
| p7_patch.py | 常住居民内容；Tk̓emlúps 写法、Powwow 月份、原住民 24 小时热线 |

对应测试：`tests/phase1test.py` … `tests/phase7test.py`。
| p8_patch.py | 新卡：家庭医生、安全找房、失业了；首屏季节提醒（冬季出行 / 野火）；冬胎日期措辞 |
| p9_patch.py | 链接核对：18 处死链 / 错页 / 只到首页的链接换成已核实的具体页面 |
| p10_patch.py | 埋点补缺：task_src、task_link、guide_link、feedback_click、season_shown |

对应测试：`tests/phase8test.py`、`tests/phase9test.py`。
| p11_patch.py | 独立复查：公交末班（11 条线路）、21 个地点坐标、泳池电话、West End 庇护所、家庭司法中心链接、310- 号码可拨打 |
| p12_patch.py | Aberdeen Tiny Library 周六营业时间（按 TNRL 分馆页） |
| p13_patch.py | 办事卡电话点击统计 task_call（只记卡，不记号码） |
| p14_patch.py | 删除 47 个无法与官方来源核对的电话；8 个连锁店链接换成分店页 |
| p15_patch.py | 5 条"先打电话"说明随之改写（6 种语言） |
| p16_patch.py | 数据版本号 2026.09.22；北岸 UPCC 加 walk-in clinic 搜索词（6 种语言）；维护者设备标记 `?maintainer=1` |
| p17_patch.py | 搜索没结果：显示最接近的结果、办事卡置顶、看病答案框；修复快速连续搜索时的 hasLayer 脚本错误 |

对应测试：`tests/phase10test.py`、`tests/phase11test.py`。
| p18_patch.py | 统一同义词表 SYN（6 种语言，按分类）；最接近结果不再被筛选挡住；输入完整地点名称时只按整个名称匹配；过时的地图聚焦请求自动作废 |

对应测试：`tests/phase12test.py`；`scripts/validate.py` 第 20 项检查同义词表。
| p19_patch.py | 方案 B：搜索时暂停分类筛选（区域、主题、现在营业、附近照常）；搜索中点选分类或快捷选择会结束搜索 |

对应测试：`tests/phase13test.py`；`tests/regress.py` 第 65、73 轮两条断言按新规则改写。
