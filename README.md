# 读本 · 设计 & AI

Zhu 的私人中文阅读室（noindex，robots.txt 禁止抓取）。

## 结构
- `index.html`：首页，读取 `articles.json` 渲染，按 `added`（收录日期）倒序
- `articles/<slug>.html`：单篇文章页（开篇封面 + 中文导读 + 编者点评）
- `covers/<slug>.svg`：原创封面（不要外链原站图片）
- `assets/style.css`：共享样式

## 封面系统（v1，所有封面统一）
全部封面为编者原创 SVG，不使用原站图片。规格：
- 画布 1200×750，底色 `#E6E6E6`；四条网格线（x=60 / x=1140，y=90 / y=660），墨色 `#1B2B26`，不透明度 0.12。
- 顶部左：IBM Plex Mono 15px、字距 3，写 `读本 · NO.xx · 分类`；顶部右：同字体，0.6 不透明度，写本篇核心概念的英文短语（大写）。
- 主图区（y 90–660）：抽象线描母题（line-art motif），表达这篇文章的核心观点；墨色描边 1.5–2px，不透明度约 0.75；不用照片、不用渐变、不用具象插画。
- 每篇只用一个强调色（accent），只用在母题中最关键的一个元素上；在根元素写 `data-accent="#RRGGBB"`。强调色选中等明度、饱和度适中的颜色，篇与篇之间换色相。
- 底部左：Instrument Serif 斜体 30px 写英文原标题；底部右：Plex Mono 14px，0.6 不透明度，写出版方。
- 例：No.01「分布收敛」，一组曲线向中心收拢，一条锈红色（`#B0452A`）的线逃离中心。

## 每日新增一篇
1. 复制现有文章页为 `articles/<slug>.html`，替换开篇信息和正文。正文统一采用「深度精讲」风格：不翻译、不逐句转述原文，用编者自己的结构和语言讲透原文的观点与技巧，加入自己的例子、对照表、可直接使用的模板或清单；设计术语保留英文括注；英文原句最多引用几句很短的，并注明出处；保留醒目的「阅读原文」按钮。编者点评写成 `<div class="note"><p>…</p></div>`。
2. 按上面的封面系统画 `covers/<slug>.svg`（记得写 `data-accent`）。
3. 在 `articles.json` 追加一项：slug、title_zh、title_en、author、author_role、source、date、added、tags、dek，以及必填的 category（`独特审美` / `AI 设计工作流` / `提示词与 Skill`）。
4. 运行 `python3 scripts/build.py <slug>`（需要 google-chrome）。脚本读取 SVG 的强调色，写入 `cover`、`accent`，以及 `tint`（同色相，OKLCH L=0.93、C≤0.014 的极淡阅读底色）；给文章页加上 `--tint` 和开篇封面；渲染紧凑聊天卡片 `cards/<slug>.png`（1000×420：左侧封面居中裁切，右侧中文标题、一句 dek、作者）。
5. 本地检查后提交并 push 到 main，GitHub Pages 会自动更新。

首页卡片为紧凑样式：2:1 封面、中文标题（最多两行）、`dek` 单行省略、一行「作者 · 日期」，所以 dek 尽量写成一句短钩子。首页保持中性灰 `#E6E6E6`，只有文章页使用 tint 底色。

版权说明：正文为编者原创的深度精讲，只少量短引原文，除非获得原作者授权，否则不发布全文译本。
