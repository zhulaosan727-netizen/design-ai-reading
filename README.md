# 读本 · 设计 & AI

Zhu 的私人中文阅读室（noindex，robots.txt 禁止抓取）。

## 结构
- `index.html`：首页，读取 `articles.json` 渲染，按 `added`（收录日期）倒序
- `articles/<slug>.html`：单篇文章页（开篇封面 + 中文导读 + 编者点评）
- `covers/<slug>.svg`：原创封面（不要外链原站图片）
- `assets/style.css`：共享样式

## 每日新增一篇
1. 复制现有文章页为 `articles/<slug>.html`，替换开篇信息和正文。正文统一采用「深度精讲」风格：不翻译、不逐句转述原文，而是用编者自己的结构和语言讲透原文的观点与技巧，加入自己的例子、对照表、可直接使用的模板或清单；设计术语保留英文括注；英文原句最多引用几句很短的，并注明出处；保留醒目的「阅读原文」按钮。编者点评写成 `<div class="note"><p>…</p></div>`。
2. 在 `articles.json` 追加一项：slug、title_zh、title_en、author、author_role、source、date、added、tags、dek，以及必填的 category（`独特审美` / `AI 设计工作流` / `提示词与 Skill`）。可选 `cover_credit`（出版方名称，默认取域名）。
3. 运行 `python3 scripts/build.py <slug>`（需要 Pillow 和 google-chrome）。脚本会：
   - 抓取原文的 og:image（没有就取 twitter:image），下载到 `covers/<slug>.png`，不外链；
   - 写入 `cover`、`cover_source_url`、`cover_credit`、`dominant`（封面主色），以及 `tint`（OKLCH L=0.93、C≤0.015 的极淡底色）；
   - 改写文章页：给 body 加上 `--tint`，生成开篇封面 figure 和「封面图来源」署名；
   - 用真实封面渲染聊天卡片 `cards/<slug>.png`（1200×630）。
   原文没有封面时，退回使用自制的 `covers/<slug>.svg`（需手动提供），且不加底色。
4. 打开本地页面检查，然后提交并 push 到 main，GitHub Pages 会自动更新。

首页保持中性灰 `#E6E6E6`，只有文章页使用 tint 底色。

版权说明：正文为编者原创的深度精讲，只少量短引原文，除非获得原作者授权，否则不发布全文译本。
