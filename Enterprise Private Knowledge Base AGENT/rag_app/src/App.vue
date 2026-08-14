<template>
  <div id="app">
    <!--
    THESIS: 回答不是黑盒输出，而是一条可逐段探测的证据信号链；拒绝通用聊天卡片。
    OWN-WORLD: 冷灰仪器表面、石墨文字、青绿有效信号、琥珀过程状态、朱红错误，以及轨道、探针与通道标签。
    STORY: 用户登录，选择演示知识库，提出问题，观察检索信号如何汇成可核查回答。
    FIRST VIEWPORT: 桌面以历史架、中央问答和证据检查器并列，五段信号轨横贯顶部，输入动作锚定底部。
    FORM: 信号链工作台；自有方向第 7 项；seed 334da845。
    FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md
    -->
    <a class="skip-link" href="#main-content">跳到主要内容</a>
    <router-view/>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
#app { min-height: 100vh; }
</style>
