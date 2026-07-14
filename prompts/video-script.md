# HKU AI+BIM Compliance Checker — 演示脚本

> 目标时长：2 分 30 秒

---

## 开场 (0:00-0:15)

"This is a web-based BIM compliance checker built for the HKU AI+BIM technical test.
Upload a building model, see it in 3D, and get instant violation reports — 
all powered by AI-generated rules."

---

## IFC 上传 + 3D 渲染 (0:15-0:45)

- 拖拽 `Ifc4_Revit_ARC.ifc` 到页面
- 3D 模型自动渲染
- 指出红色 = 门宽不合格，黄色 = 缺 FireRating
- "The left panel shows statistics: X passed, Y failed, Z warnings."

---

## 合规检查结果 (0:45-1:15)

- 滚动右侧问题列表
- "Two built-in rules are running: door width >= 900mm for fire egress,
  and FireRating completeness on all doors and walls."
- 点击一个 issue → 绿色高亮
- "Click any violation to highlight it in 3D."

---

## AI 规则生成 (1:15-1:50)

- 聚焦 AI Rule Generator 区域
- 输入: `egress doors at least 1000mm`
- 点击 Preview → 展示解析结果
- 点击 Run → 结果更新
- "The AI rule engine parses natural language regulations
  and runs them against the loaded model."

---

## PDF 导出 (1:50-2:05)

- 点击 Export PDF
- PDF 下载完成，打开展示
- "Export a professional compliance report with one click."

---

## 结尾 (2:05-2:30)

- 切换到 JSON 文件演示: 上传 `sample.json`
- "The checker also supports JSON models and CAD DXF files."
- "Built with FastAPI + ifcopenshell on the backend,
  web-ifc-viewer + Three.js on the frontend,
  and DeepSeek LLM for advanced rule parsing."
- "Source code available on GitHub. Thank you."

---

## 录制准备清单

- [ ] 打开 http://localhost:5173
- [ ] 确保后端在 8000 端口运行
- [ ] `samples/Ifc4_Revit_ARC.ifc` 放桌面方便拖拽
- [ ] `samples/sample.json` 备好
- [ ] 填入 DeepSeek API key
- [ ] 录屏软件（OBS / Windows 自带 Xbox Game Bar: Win+G）
- [ ] 麦克风测试
