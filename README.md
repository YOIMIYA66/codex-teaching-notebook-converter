# Teaching Notebook Converter

Codex 专用 skill：将工程化 Jupyter Notebook 转换成图文并茂、结构清晰、适合教学演示的教学 Notebook。

这个 skill 沉淀自一次 PaddleFormers + Qwen3-0.6B + LoRA 病历生成实验 notebook 的改造过程。它面向 Codex 使用，不是 Python 包，也不是独立命令行工具。

## 适用场景

当你已经有一个可运行但偏工程化的 `.ipynb`，希望 Codex 将它改造成教学版本时使用，例如：

- AI 模型训练 notebook
- 数据处理与建模 notebook
- 推理验收、模型导出、交付打包流程
- 科研复现实验 notebook
- 需要加入海报、流程图、卡片式讲解和质量门禁说明的课程材料

## 主要能力

- 保留原工程 notebook 的可运行逻辑
- 创建 `*.teaching.ipynb` 教学副本
- 使用 `imagegen` 生成教学插图
- 顶部添加 16:9 横版宣传海报
- 正文使用白底浅色教学流程图
- 用 Markdown + inline HTML 卡片美化说明区
- 增加项目定位、课程路线图、成果卡、质量门禁、交付清单
- 校验 notebook JSON、Python 代码单元和 HTML 预览

## 推荐视觉规范

- 首屏：深色科技风 16:9 宣传海报，用来抓住主题和成果。
- 正文：白底或浅蓝底 16:9 教学图，更适合 notebook 阅读。
- 卡片：使用 inline `<div style="...">`，避免依赖全局 `<style>`。
- 图数量：通常 1 张首屏海报 + 3 到 5 张正文教学图即可。

## 为什么用 `<div style="...">` 做卡片

很多云端 notebook 对全局 CSS 或 `<style>` 支持不稳定，但通常能渲染 Markdown 单元里的 inline HTML。因此这个 skill 推荐直接在 Markdown 里写：

```html
<div style="display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:12px;margin:12px 0;">
  <div style="padding:12px 14px;border:1px solid #d9e2f2;border-radius:12px;background:#f7fbff;">
    <b>Step 1</b><br/>数据准备
  </div>
  <div style="padding:12px 14px;border:1px solid #d9e2f2;border-radius:12px;background:#f7fbff;">
    <b>Step 2</b><br/>LoRA 训练
  </div>
  <div style="padding:12px 14px;border:1px solid #f1d9ae;border-radius:12px;background:#fff8ed;">
    <b>风险提示</b><br/>部署时保留 fallback 逻辑
  </div>
</div>
```

常用样式含义：

- `display:grid` / `display:flex`：控制卡片排列。
- `gap`：控制卡片间距。
- `padding`：控制卡片内部留白。
- `border`：添加边框。
- `border-radius`：添加圆角。
- `background`：设置卡片底色。
- `margin`：控制卡片组与上下内容的距离。

## 安装

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/YOIMIYA66/codex-teaching-notebook-converter.git "$env:USERPROFILE\.codex\skills\teaching-notebook-converter"
```

### macOS / Linux

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/YOIMIYA66/codex-teaching-notebook-converter.git ~/.codex/skills/teaching-notebook-converter
```

如果目录已经存在，使用 `git pull` 更新：

```bash
cd ~/.codex/skills/teaching-notebook-converter
git pull
```

## 使用方式

在 Codex 中直接提出类似请求：

```text
使用 teaching-notebook-converter，把这个工程化 notebook 改成图文并茂的教学 notebook。
```

或：

```text
把 xxx.ipynb 转成教学版 notebook，要求用 imagegen 生成首屏横版海报和流程图，并用卡片式 Markdown 美化。
```

## 工作流摘要

1. 先读取原 notebook，识别数据、训练、推理、导出、交付阶段。
2. 创建教学副本，保留原工程逻辑。
3. 生成首屏海报、正文流程图、关键概念图。
4. 加入教学讲解、路线图、成果卡和风险提示。
5. 使用 inline HTML 卡片增强可读性。
6. 校验 JSON、代码单元、图片引用和 HTML 预览。

## Codex 专用说明

本仓库是 Codex skill 仓库，核心文件是：

- `SKILL.md`
- `agents/openai.yaml`

Codex 会通过 `SKILL.md` 的 frontmatter 判断何时触发该 skill。README 仅用于 GitHub 页面说明，不参与 skill 的触发逻辑。
