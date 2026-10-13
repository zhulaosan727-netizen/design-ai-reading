# 读本 · 设计 & AI

Zhu 的私人中文阅读室（noindex，robots.txt 禁止抓取）。

## 结构
- `index.html`：首页，读取 `articles.json` 渲染，按 `added`（收录日期）倒序
- `articles/<slug>.html`：单篇文章页（开篇封面 + 中文导读 + 编者点评）
- `covers/<slug>.svg`：原创封面（不要外链原站图片）
- `assets/style.css`：共享样式

## 每日新增一篇
1. 复制 `articles/improving-frontend-design-through-skills.html` 为 `articles/<新slug>.html`，替换开篇信息和正文
2. 编者点评写成 `<div class="note"><p>…</p></div>`
3. 在 `covers/` 放一张 `<新slug>.svg` 封面（1200×750）
4. 在 `articles.json` 里追加一项（slug、title_zh、title_en、author、author_role、source、date、added、cover、tags、dek）
5. 提交并 push 到 main，GitHub Pages 会自动更新

版权说明：正文以中文导读和少量引用为主，除非获得原作者授权，否则不发布全文译本。
