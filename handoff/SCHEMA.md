# 读本交接包（选稿 → DeepSeek 翻译上线）

## 分工
- **AI设计文章（本 bot）**：选稿、封面 SVG/PNG 卡片、中文标题、一句话推荐语（dek）、分类、accent/tint
- **DeepSeek Harness 插件**：读本交接 JSON → 拉原文 → 深度精讲/翻译正文 → 写入 `articles/`、更新 `articles.json`、构建卡片（若缺）、推送 GitHub Pages

## 目录约定
每日（或每篇）一个文件夹：

```
handoff/inbox/<YYYY-MM-DD>-<slug>/
  job.json          # 必填：元数据与任务说明
  cover.svg         # 必填：统一风格封面（已由选稿方生成）
  card.png          # 可选：若已生成推送卡片则带上；否则插件按现有 build 生成
  source.md         # 可选：原文摘录或全文（有版权时宁缺勿滥，优先用 source_url）
  NOTES.md          # 可选：选稿备注
```

处理完后插件把文件夹移到：

```
handoff/done/<YYYY-MM-DD>-<slug>/
```

失败写入：

```
handoff/failed/<YYYY-MM-DD>-<slug>/error.json
```

## job.json 字段
见同目录 `job.example.json`。

关键字段：
- `slug`：kebab-case，与文章页文件名一致
- `title_zh` / `title_en` / `author` / `source_url` / `category` / `dek` / `accent` / `tint`
- `mode`：`depth_guide`（默认，深度精讲非全文翻译）| `full_zh`（仅公域/已授权）
- `status`：`ready` → 插件认领后改为 `processing` → 成功 `published` / 失败 `failed`

## 触发方式（建议）
1. 选稿方写好 `handoff/inbox/.../job.json` 并 commit/push 到 `design-ai-reading`
2. DeepSeek 插件监听该路径（本地 watch / GitHub Action / 定时扫 inbox）
3. 或选稿方在聊天里丢一句：`handoff ready: handoff/inbox/2026-11-03-foo/`

版权：默认 `depth_guide`，禁止整篇 verbatim 译文上线。
