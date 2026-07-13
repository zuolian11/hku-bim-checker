# HKU AI+BIM 笔试 — 工作记录

> 截止日：2026-07-20 | 项目：`D:\Python\Projects\hku-bim-checker\`

---

## Day 1 — 2026-07-13：环境搭建 + 全栈框架 ✅

**完成：**
- [x] ifcopenshell 0.8.5 安装
- [x] 下载 3 个样例 IFC 文件
- [x] FastAPI + ifcopenshell + Three.js 全栈框架一次性搭完
- [x] POST /api/upload — 文件上传
- [x] POST /api/check/{id} — 两条规则：门宽检查 + FireRating检查
- [x] GET /api/geo/{id} — 真实几何数据（63 个元素，create_shape 提取）
- [x] 前端：Three.js 3D 渲染 + 拖拽上传 + 报告面板 + 点击定位
- [x] 本地服务 http://localhost:8000 可运行
- [x] render.yaml 部署配置

**API 验证结果：**
- 门宽检查：9 pass / 7 fail ✅
- FireRating：0 pass / 63 fail ✅
- 几何导出：63 elements ✅

**待做：**
- [ ] 前端上传 + 3D 渲染联调实测
- [ ] README.md
- [ ] 录视频
- [ ] 推 GitHub + 部署 Render

---

## Day 2+

剩余时间用于修 Bug + 完善 README + 录视频 + 部署。

---

## 笔记
- 技术栈：Python + FastAPI + ifcopenshell + Three.js
- 无需 git/npm（系统未装），用 OpenCode 直接操作
