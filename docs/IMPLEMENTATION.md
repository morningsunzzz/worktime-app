# 落地方案

## 1. 技术选型

### 1.1 方案对比

| 方案 | 开发成本 | 安装方式 | 离线 | 适合场景 |
|------|---------|----------|------|---------|
| **PWA (推荐)** | 低 | 浏览器添加到桌面 | ✅ | 个人工具，无需应用商店 |
| React Native | 高 | App Store / APK | ✅ | 需要原生能力、上架分发 |
| 微信小程序 | 中 | 微信内 | ❌ | 依赖微信生态 |
| Flutter | 高 | App Store / APK | ✅ | 跨平台原生体验 |

**选择 PWA 方案**，原因：
- 个人使用，无需分发
- 零安装成本，扫码/链接即用
- 完整体验接近原生 App（全屏、图标、离线、推送）
- 不依赖应用商店审核
- 开发周期最短

### 1.2 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 框架 | **React 18 + TypeScript** | 组件化开发，类型安全 |
| 构建 | **Vite** | 极快的开发体验 |
| UI | **Tailwind CSS** | 原子化 CSS，mobile-first |
| 路由 | **React Router v6** | 客户端路由 |
| 存储 | **Dexie.js** (IndexedDB 封装) | 本地数据库，支持复杂查询 |
| 图表 | **recharts** | 轻量图表库 |
| 日期 | **dayjs** | 2KB 的 moment.js 替代 |
| PWA | **vite-plugin-pwa** | 自动生成 Service Worker |
| 图标 | **Lucide React** | 轻量图标库 |

### 1.3 项目结构

```
workTime-app/
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── public/
│   ├── favicon.svg
│   ├── manifest.json
│   └── icons/               # PWA 图标
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── db/
│   │   └── database.ts      # Dexie 数据库定义
│   ├── models/
│   │   └── WorkRecord.ts    # 类型定义
│   ├── hooks/
│   │   ├── useTodayRecord.ts    # 今日打卡状态
│   │   ├── useRecords.ts        # 历史记录查询
│   │   └── useStats.ts          # 统计数据
│   ├── pages/
│   │   ├── ClockPage.tsx        # 打卡首页
│   │   ├── HistoryPage.tsx      # 历史记录
│   │   ├── StatsPage.tsx        # 统计页
│   │   └── SettingsPage.tsx     # 设置页
│   ├── components/
│   │   ├── Layout.tsx           # 底部导航布局
│   │   ├── ClockButton.tsx      # 打卡按钮
│   │   ├── TodaySummary.tsx     # 今日概览
│   │   ├── RecordCard.tsx       # 记录卡片
│   │   └── MonthChart.tsx       # 月度图表
│   └── utils/
│       ├── time.ts              # 时间计算工具
│       └── export.ts            # 数据导出
```

---

## 2. 开发阶段

### 第一阶段：MVP（3-4 天）
**目标**: 能打卡、能回看，手机可用

- [ ] 项目初始化（Vite + React + TS + Tailwind + PWA 插件）
- [ ] 数据库设计与 Dexie 初始化
- [ ] 打卡页面 UI + 上下班打卡逻辑
- [ ] 今日状态展示（实时计算已工作时长）
- [ ] 历史记录列表页
- [ ] 底部导航 + 路由
- [ ] PWA manifest + 图标生成
- [ ] 部署到 Vercel/Netlify，手机访问测试

### 第二阶段：完善（2-3 天）
**目标**: 统计、加班计算、离线完整

- [ ] 月度统计页（出勤天数、总工时、加班）
- [ ] 加班自动计算逻辑
- [ ] 编辑记录（补卡）
- [ ] 设置页（标准工时配置）
- [ ] 离线 Service Worker 缓存策略
- [ ] 数据导出 CSV

### 第三阶段：增强（可选）
- [ ] 午休分段打卡
- [ ] 手机通知提醒
- [ ] 暗色模式
- [ ] 指纹/面容解锁

---

## 3. 核心逻辑设计

### 3.1 打卡状态机

```
        上班打卡              下班打卡
空闲 ──────────→ 工作中 ──────────→ 已完成
  ↑                                    │
  └────────────────────────────────────┘
              次日自动重置
```

### 3.2 工时计算

```
if clockIn && clockOut:
    workMinutes = clockOut - clockIn - lunchBreak
    totalHours = ceil(workMinutes / 30) * 0.5  // 精确到0.5h
    overtimeHours = max(0, totalHours - standardHours)
```

### 3.3 今日状态实时显示

- 已上班但未下班：显示"已工作 X小时X分"（实时计时器）
- 已下班：显示"今日工时 Xh，加班 Xh"

---

## 4. 部署与使用

### 4.1 部署
- 推送到 GitHub
- 连接 Vercel 自动部署
- 获得 `https://xxx.vercel.app` 域名

### 4.2 手机使用
1. Safari/Chrome 打开链接
2. iOS: 点击分享 → "添加到主屏幕"
3. Android: Chrome 菜单 → "添加到主屏幕"
4. 桌面出现 App 图标，点击即可全屏使用

### 4.3 日常使用流程
1. 上班：打开 App → 点击"上班打卡"
2. 下班：打开 App → 点击"下班打卡"
3. 月底：进入统计页查看本月汇总
4. 需要时：导出 CSV 用于报销或记录

---

## 5. UI 草图

```
┌─────────────────────┐
│   05月15日 星期四     │  ← 日期
│     14:35:22        │  ← 实时时钟
│                     │
│    ⏰ 09:05 上班     │  ← 今日打卡信息
│    已工作 5h 30m    │
│                     │
│   ┌─────────────┐   │
│   │             │   │
│   │  下班打卡    │   │  ← 大按钮（红色）
│   │             │   │
│   └─────────────┘   │
│                     │
├─────────────────────┤
│  🔘打卡  📋记录  📊统计 ⚙️设置 │ ← 底部导航
└─────────────────────┘
```

---

## 6. 风险与对策

| 风险 | 对策 |
|------|------|
| IndexedDB 数据被清除 | 定期提醒导出备份；提供导出功能 |
| iOS PWA 限制（存储可能被清理） | 提供导出功能，数据随时可备份 |
| 时区问题（跨时区打卡） | 明确以用户设备本地时间为准 |
| 浏览器兼容性 | 仅支持 iOS Safari 14+ / Android Chrome 90+ |
