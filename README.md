# 读本 · 设计 & AI

Zhu 的私人中文阅读室（noindex，robots.txt 禁止抓取）。

## 结构
- `index.html`：首页，读取 `articles.json` 渲染，按 `added`（收录日期）倒序
- `articles/<slug>.html`：单篇文章页（开篇封面 + 中文导读 + 编者点评）
- `covers/<slug>.svg`：原创封面（不要外链原站图片）
- `assets/style.css`：共享样式

## 每日新增一篇
1. 复制 `articles/improving-frontend-design-through-skills.html` 为 `articles/<新slug>.html`，替换开篇信息和正文。正文统一采用「深度精讲」风格：不翻译、不逐句转述原文，而是用编者自己的结构和语言，讲透原文的每个观点与具体技巧，并加入自己的例子、对照表（如 默认 AI 选择 vs 推荐做法）、可直接使用的模板或清单；设计术语保留英文括注；英文原句最多引用几句很短的，并注明出处；保留开篇信息和醒目的「阅读原文」按钮
2. 编者点评写成 `<div class="note"><p>…</p></div>`
3. 在 `covers/` 放一张 `<新slug>.svg` 封面（1200×750）
4. 在 `articles.json` 里追加一项（必填 category，取值为 `独特审美` / `AI 设计工作流` / `提示词与 Skill` 之一；以及 slug、title_zh、title_en、author、author_role、source、date、added、cover、tags、dek）
5. 提交并 push 到 main，GitHub Pages 会自动更新

版权说明：正文为编者原创的深度精讲，只少量短引原文，除非获得原作者授权，否则不发布全文译本。
