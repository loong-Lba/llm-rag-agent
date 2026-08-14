---
name: 可视化 RAG 助手
description: 让混合检索证据链可观察、可学习、可核查的中文信号链工作台。
colors:
  canvas: "#e7ebea"
  surface: "#f7f9f8"
  panel: "#eef2f1"
  ink: "#17201f"
  muted: "#53615f"
  faint: "#72807d"
  line: "#aebbb8"
  line-strong: "#788784"
  active: "#007c70"
  active-strong: "#005e56"
  active-soft: "#d2ebe7"
  progress: "#a85f00"
  progress-soft: "#f6e6c9"
  error: "#b23628"
  error-soft: "#f5dcd7"
  dark: "#111918"
  focus: "#005fcc"
typography:
  display:
    fontFamily: '"Smiley Sans", "Microsoft YaHei UI", sans-serif'
    fontSize: "clamp(42px, 6vw, 84px)"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "-0.04em"
  headline:
    fontFamily: '"Smiley Sans", "Microsoft YaHei UI", sans-serif'
    fontSize: "clamp(28px, 4vw, 48px)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.04em"
  title:
    fontFamily: '"Smiley Sans", "Microsoft YaHei UI", sans-serif'
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  body:
    fontFamily: '"Microsoft YaHei UI", "Noto Sans SC", "Segoe UI", sans-serif'
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.8
    letterSpacing: "normal"
  label:
    fontFamily: '"Microsoft YaHei UI", "Noto Sans SC", "Segoe UI", sans-serif'
    fontSize: "11px"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.08em"
  data:
    fontFamily: '"Cascadia Mono", "SFMono-Regular", Consolas, monospace'
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
rounded:
  control: "3px"
  square: "0"
spacing:
  xs: "6px"
  sm: "10px"
  md: "12px"
  lg: "18px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "10px 16px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.active-strong}"
    textColor: "#ffffff"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 16px"
    height: "44px"
  input-standard:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 13px"
    height: "46px"
  textarea-composer:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "12px 13px"
    height: "48px"
  card-answer:
    backgroundColor: "#ffffff"
    textColor: "{colors.ink}"
    rounded: "{rounded.square}"
    padding: "24px 26px"
---

# Design System: 可视化 RAG 助手

## Overview

**Creative North Star: "证据信号链工作台"**

这是一个冷灰仪器世界：石墨色工作面承载信息，青绿表示有效信号，琥珀表示运行或证据不足，朱红表示错误与中断。轨道、探针、通道标签、读数和细分隔线把 RAG 从黑盒回答转化为可以逐段检查的过程；视觉重点始终是证据状态与可追溯性，而不是聊天气泡的亲和感。

界面密度偏高但分区明确。桌面工作台同时呈现历史架、问答通道和证据检查器，深色信号轨横贯主工作区；登录与注册页沿用深色仪器故事面和浅色身份控制台。系统以简体中文为主，技术缩写、请求标识、排名和分数使用等宽数据字体。

**Key Characteristics:**
- 冷灰浅表面与石墨深轨并置，青绿信号只标记有效、选中和完成。
- 五段轨道、方形探针、细线表格和等宽读数构成可复用的仪器语法。
- 自托管 Smiley Sans Oblique 只承担显示标题；正文保持清晰克制。
- 控件近方角、边界可见、状态不只依赖颜色，并保留明确键盘焦点。
- 响应式布局把并列检查工具变成有焦点约束的抽屉，而非删除证据能力。

## Colors

低彩度冷灰建立仪器底盘，青绿、琥珀、朱红分别承担有效信号、过程判断和故障语义。

### Primary
- **有效信号青绿** (`active`, `active-strong`, `active-soft`): 用于完成探针、当前来源、可用状态、链接和选择反馈；深色值承载浅底文字，柔和底色承载选中行与通过判断。

### Secondary
- **过程琥珀** (`progress`, `progress-soft`): 用于流式接收、运行中探针、降级和证据不足；它表达“仍需判断”，不表达成功。

### Tertiary
- **故障朱红** (`error`, `error-soft`): 用于无效字段、中断、不可用和危险动作；柔和底色承载可恢复的停止状态。
- **键盘焦点蓝** (`focus`): 专供全局 `:focus-visible` 和字段聚焦，不承担产品状态。

### Neutral
- **冷灰画布** (`canvas`): 页面最外层和工作台底盘。
- **浅仪器表面** (`surface`, `panel`): 主要内容、输入区与次级面板的层次区分。
- **石墨墨色** (`ink`, `dark`): 浅底正文与深色历史架、故事面、信号轨。
- **读数灰** (`muted`, `faint`): 说明文字、时间、次级标签和占位信息。
- **仪器分隔线** (`line`, `line-strong`): 容器、列表、字段和轨道的结构边界。

### Named Rules
**The Semantic Signal Rule.** 青绿只表示有效、完成、选中或可操作；琥珀只表示进行、降级或证据不足；朱红只表示错误、中断、不可用或危险动作。

**The Contrast Pair Rule.** 深色工作面使用高明度文字与亮青绿探针，浅色表面使用深石墨文字与 `active-strong`；不要把柔和状态底色当作正文文字色。

## Typography

**Display Font:** Smiley Sans（自托管 `SmileySans-Oblique.woff2`，回退到 Microsoft YaHei UI 和 sans-serif）  
**Body Font:** Microsoft YaHei UI（回退到 Noto Sans SC、Segoe UI 和 sans-serif）  
**Label/Mono Font:** Cascadia Mono（回退到 SFMono-Regular、Consolas 和 monospace）

**Character:** Smiley Sans 的倾斜、饱满标题给冷静仪器界面一个清晰的中文识别点；正文保持中性易读，等宽字体把请求号、序号、分数与缩写变成稳定读数。数字读数启用 tabular numerals。

### Hierarchy
- **Display**（700，流体大号，紧凑行高与负字距）: 登录/注册故事面的单一主标题，通常在桌面从约 42px 扩展到 84px。
- **Headline**（700，流体中大号，紧凑行高）: 空状态主叙事与身份控制台标题，典型范围为 28–48px。
- **Title**（700，约 18–20px）: 历史架、证据检查器和工作区标题。
- **Body**（400，15px，1.8）: 回答、说明和长文本；叙事说明通常限制在 65ch 左右，证据正文以 1.75 行高呈现。
- **Label**（700–800，10–13px，0.08–0.14em）: 中文来源标签、字段标签和状态标题；只在短标签中使用扩展字距。
- **Data**（400，9–12px，等宽且数字等宽）: CHANNEL LOG、EVIDENCE PROBE、REQ、编号、时间、命中数和评分。

### Named Rules
**The Three-Voice Rule.** 显示标题用 Smiley Sans，连续中文阅读用正文无衬线，机器读数用等宽字体；三者不得互相替代。

**The Display Restraint Rule.** Smiley Sans 只用于 `h1`/`h2` 级显示文本，并保持 oblique 700；按钮、字段和长答案不用显示字体。

## Layout

桌面工作台是固定视口高度的三段式横向拓扑：历史架宽 278px（中等桌面降至 230px，可折叠到 58px），中心工作区弹性填充，证据检查器宽 330px。中心内部按 76px 左右标题栏、横向五段信号轨、可滚动消息线程和底部问题编辑器垂直堆叠。消息内容居中限制在 760px，用户问题收窄到 620px；证据来源和分数使用规则网格而非卡片瀑布。

间距以 6、10、12、18、24px 一组重复节拍组织控件内部与相邻区域；大场景留白通过 `clamp()` 响应视口。消息线程的背景使用每 28px 一条的低对比水平刻度线，身份故事面使用每 32px 一条的深色刻度线，强化测量台语义。

在 1180px 以下，证据检查器从固定第三列变为右侧抽屉，工具栏显示“检查证据”触发器；在 1050px 以下历史架缩窄；在 900px 以下身份页由双列变单列；在 760px 以下历史架变为左侧模态抽屉，工作台标题栏纵向重排；在 700px 以下五段信号轨保持 560px 最小宽度并横向滚动；在 620px 以下编辑器、消息内边距和检查器切换为单列/全宽；在 480px 以下顶部工具再次纵向堆叠。

**The Persistent Chain Rule.** 窄屏可滚动或抽屉化证据工具，但五段信号链、来源入口和输入动作必须保留。

## Elevation & Depth

系统以色调分层和 1px 结构线为主、低扩散阴影为辅。回答面板使用轻微环境阴影从刻度背景上抬起；身份控制台和移动抽屉使用较宽侧向阴影表达覆盖关系；青绿状态点可带小范围信号辉光。阴影不塑造厚重卡片，也不使用硬偏移轮廓。

### Shadow Vocabulary
- **回答浮层** (`0 10px 30px rgba(29,46,42,.07)`): 仅用于浅色助手回答面板。
- **控制台分界** (`-18px 0 46px rgba(0,0,0,.12)`；窄屏改为 `0 -18px 46px rgba(0,0,0,.1)`): 区分身份故事面与表单控制台。
- **左侧抽屉** (`18px 0 46px rgba(0,0,0,.28)`): 移动会话历史覆盖层。
- **右侧抽屉** (`-18px 0 46px rgba(0,0,0,.2)`): 中窄屏证据检查器覆盖层。
- **有效信号辉光** (`0 4px 12px rgba(0,124,112,.28)`): 小型青绿状态探针，不用于大面积容器。

### Named Rules
**The Instrument Layer Rule.** 默认表面靠色调和细线分层；只有回答、控制台、抽屉和小型状态信号获得阴影。

## Shapes

形态近方角、薄边界、几何明确。通用按钮与标准字段使用轻微 3px 圆角，选择器、编辑器、消息面板、状态条和大多数仪器容器保持直角。探针、状态灯和品牌信号均为实心或描边小方块；轨道是一像素直线。图标均为内联描边 SVG，约 18–19px、方形端点，作为有文字或无障碍名称的控制辅助。

**The Near-Square Rule.** 3px 是交互控件的最大常规圆角；结构容器与数据面保持直角，避免胶囊和大圆角聊天气泡。

**The Probe Geometry Rule.** 状态标记使用 5–9px 方形探针和一像素轨道，不能替换成装饰性圆点或表情符号。

## Components

组件整体应“可探测且可信”：边界明确、状态有文本、数值像仪表读数，交互反馈短促直接。

### Buttons
- **Shape:** 轻微方角（3px），最小高度 44px，默认 1px 边框；图标使用内联描边 SVG。
- **Primary:** 石墨底白字、700 字重与 10px × 16px 内边距；深色历史架上的“新建对话”反转为亮青绿底和深墨文字。
- **Hover / Focus:** 160ms ease-out 的颜色与边框转换，hover 进入深青绿，active 下移 1px；所有可见键盘焦点使用 3px 蓝色轮廓并外偏 3px。
- **Quiet / Danger:** Quiet 为透明底、结构线边框，hover 使用柔和青绿；Danger 默认为透明朱红，hover 变为朱红底白字。Disabled 使用灰底灰字和 not-allowed 光标。

### Chips
- **Style:** 命中统计和证据判断是近方形状态块，最小高度 34px、7px × 10px 内边距、1px 边框；数字使用加粗等宽字体。
- **State:** 可点击统计 hover 转青绿边框；证据充足用柔和青绿，证据不足用柔和琥珀。它们是状态读数，不使用圆角胶囊。

### Cards / Containers
- **Corner Style:** 直角。
- **Background:** 助手回答为白色，用户问题为深石墨，系统消息为冷灰面板，检查器为浅冷灰。
- **Shadow Strategy:** 仅助手回答使用“回答浮层”；其他容器依靠色调和结构线。
- **Border:** 1px 仪器分隔线；错误回答将边框切换为故障朱红。
- **Internal Padding:** 助手回答 24px × 26px，用户问题 16px × 19px；移动端助手回答收紧到 18px × 16px。

### Inputs / Fields
- **Style:** 标准字段白底、1px 强分隔线、3px 圆角、最小高度 46px；问题编辑器浅表面底、直角、最小高度 48px，允许纵向调整至 144px。
- **Focus:** 蓝色边框与 `0 0 0 3px rgba(0,95,204,.16)` 焦点晕圈。
- **Error / Disabled:** `aria-invalid="true"` 切换朱红边框并显示相邻朱红错误文本；disabled 由原生状态和按钮灰阶共同表达。

### Navigation
- **History shelf:** 深石墨固定侧栏，活动会话使用深一阶底色与 5px 青绿方探针；列表以横线分段，长标题省略，时间使用等宽小字。移动端成为左侧模态抽屉并锁定 Tab 循环。
- **Signal rail:** 深色横向五列导航，每阶段包含两位编号、方形探针、名称和文字状态；方向键在相邻阶段间移动焦点，当前阶段使用更深背景和 `aria-current="step"`。
- **Evidence inspector:** 桌面固定右栏，中窄屏为右抽屉，手机全宽；来源索引选中态使用柔和青绿，分数用两列表格排列。抽屉打开时聚焦关闭按钮并锁定 Tab 循环。

### Signal Rail
- 五个固定阶段依次为向量、BM25、RRF、重排、回答。等待为灰探针，运行中为脉冲琥珀，完成为青绿且连接线同步变青绿，错误为朱红。
- 请求标识使用等宽大写短码；链路同时提供完整文字状态，颜色和动画都不是唯一信息通道。

### Message Thread & Sources
- 回答 Markdown 支持长文本、链接和深色代码块；链接使用深青绿和 3px 下划线偏移。
- 检索摘要固定呈现向量命中、BM25 命中、融合候选、返回来源与证据结论；来源条目呈现编号、位置、知识库/文件和主要重排读数。
- 选择阶段或来源应把同一上下文带入证据检查器；流式失败保留已收到内容并明确标记链路中断。

### Question Composer
- 固定在工作区底部，文本域与动作区并列；620px 以下改为上下结构。Enter 发送，Shift+Enter 换行。
- 流式期间发送按钮替换为朱红停止控制；编辑器占位文字必须解释缺少会话、知识库或可提问三种前置状态。

### Access Console
- 登录和注册共用“深色证据故事面 + 浅色身份控制台”双栏结构，故事面展示信号链或保存轨迹，控制台承载字段、状态和主动作。
- 表单使用内联验证、`aria-invalid`、状态直播区域与提交中脉冲；900px 以下垂直堆叠。

## Do's and Don'ts

### Do:
- **Do** 让每个检索阶段同时具备名称、顺序、文字状态和方形探针。
- **Do** 用等宽字体和 tabular numerals 呈现请求号、编号、时间、命中数、排名与分数。
- **Do** 保持 44px 最小动作高度、3px 全局可见焦点轮廓、跳转主内容链接与简体中文无障碍名称。
- **Do** 在移动抽屉打开时聚焦入口控件、约束 Tab 循环、支持 Escape/遮罩关闭并把焦点还给触发器。
- **Do** 尊重 `prefers-reduced-motion`，把动画和过渡压缩到 0.01ms；状态含义必须在无动画时仍完整。
- **Do** 保持来源、评分和证据充分性与当前回答上下文一致。

### Don't:
- **Don't** 把工作台重做成通用圆角聊天卡片、浮动气泡或胶囊标签；证据链和结构线是核心信息架构。
- **Don't** 用青绿装饰无状态内容，或混用青绿、琥珀、朱红的语义。
- **Don't** 只用颜色、动画或图标表达运行、完成、错误和证据判断。
- **Don't** 在窄屏删除信号轨、来源详情或证据入口；应使用滚动和抽屉保留能力。
- **Don't** 给常规容器添加厚重阴影、大圆角或硬偏移阴影；深度只服务明确层级。
- **Don't** 在显示标题之外使用 Smiley Sans，或用等宽字体承载长篇中文回答。
