# HKU AI+BIM 笔试 — 工作记录

> 截止日：2026-07-20 | 项目：`D:\Python\Projects\hku-bim-checker\`

---

## Day 1 — 2026-07-13：全栈开发 ✅

**完成的工作：**

### 环境
- [x] Python 3.12 + ifcopenshell 0.8.5
- [x] Node.js v24 + npm + Vite
- [x] Git 初始化 + 8 次提交

### 后端 (FastAPI + ifcopenshell)
- [x] 两条合规检查规则（门宽 >= 900mm + FireRating 完整性）
- [x] 规则智能化：名字含 "Fire/1-hr" 但缺 FireRating → fail；普通缺失 → warning
- [x] 多格式支持：IFC / JSON / DXF / DWG
- [x] 空间分析：自动分类门为 egress / interior / stairwell
- [x] AI 规则生成器：自然语言 → 可执行检查规则
- [x] 支持按门分类筛选：`egress doors at least 1000mm`

### 前端 (Vite + web-ifc-viewer)
- [x] 专业深色主题 UI
- [x] 3D IFC 模型渲染
- [x] 失败元素红色标记、警告黄色标记
- [x] 点击问题列表 → 相机飞到对应构件
- [x] AI 规则输入框 + Run 按钮
- [x] 拖拽上传支持 .ifc / .json / .dxf / .dwg

### 项目文件
```
hku-bim-checker/
├── backend/
│   ├── main.py              FastAPI 入口
│   ├── checker.py           合规规则（IFC + JSON）
│   ├── ai_rule_gen.py       自然语言 → 规则
│   ├── spatial_analysis.py  门分类（疏散/室内/楼梯）
│   ├── cad_checker.py       DXF 检查
│   ├── cad_utils.py         DWG 版本检测
│   └── requirements.txt
├── frontend/
│   ├── index.html           主页面
│   ├── main.js              交互逻辑
│   └── package.json
├── samples/                 测试数据（IFC + JSON + DWG）
├── prompts/                 AI prompt 记录
├── README.md
├── .gitignore
├── render.yaml
└── just-work.md
```

### 关键设计决策
| 决策 | 理由 |
|------|------|
| web-ifc-viewer 替代自建 Three.js | 专业 IFC 渲染，省 3 天开发 |
| ifcopenshell 做后端检查 | IFC Pset 提取最可靠 |
| 空间分析 + AI 规则分离 | 先分类再检查，架构清晰 |
| 正则匹配替代 LLM | 系统可独立运行，不依赖 API |
| MeshStandardMaterial 纯色 | 红色醒目，不被原模型混色 |

---

## 待做
- [ ] 录 3 分钟演示视频
- [ ] 推送到 GitHub
- [ ] 邮件提交 (junnaifj@hku.hk)
