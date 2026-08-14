<template>
  <aside ref="drawer" :class="['evidence-inspector', { open: open }]" :aria-hidden="String(!desktop && !open)" aria-label="证据检查器" :role="!desktop && open ? 'dialog' : null" :aria-modal="!desktop && open ? 'true' : null" @keydown.tab="trapFocus">
    <header class="inspector-head">
      <div>
        <h2>证据检查器</h2>
      </div>
      <button v-if="!desktop" ref="closeButton" class="inspector-close" type="button" aria-label="关闭证据检查器" @click="$emit('close')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>
      </button>
    </header>

    <div class="stage-context">
      <span>当前探针</span>
      <strong>{{ stageLabel }}</strong>
      <p>{{ stageDescription }}</p>
    </div>

    <div v-if="!sources.length" class="inspector-empty">
      <div class="empty-probe" aria-hidden="true"></div>
      <strong>等待来源信号</strong>
      <p>完成检索后，来源片段及其评分会出现在这里。选择顶部阶段可了解每一步的作用。</p>
    </div>

    <div v-else class="source-index">
      <p class="source-count"><span class="signal-data">{{ sources.length }}</span> 条返回来源</p>
      <button v-for="(source, index) in sources" :key="source.index || index" type="button" :class="{ active: sameSource(source, selectedSource) }" @click="$emit('select-source', source)">
        <span class="signal-data">[{{ source.index || index + 1 }}]</span>
        <span><strong>{{ sourceLocation(source) }}</strong><small>{{ knowledgeBaseName(source) }}</small></span>
      </button>
    </div>

    <section v-if="selectedSource" class="source-detail" aria-labelledby="source-detail-title">
      <div class="detail-heading">
        <span class="signal-data">SOURCE {{ selectedSource.index || '—' }}</span>
        <h3 id="source-detail-title">{{ sourceLocation(selectedSource) }}</h3>
        <p>{{ knowledgeBaseName(selectedSource) }} · {{ selectedSource.sourceFile || '来源文件未记录' }}</p>
      </div>
      <div class="source-text">{{ selectedSource.content || '来源内容未记录。' }}</div>
      <h4>检索读数</h4>
      <dl v-if="scoreEntries.length" class="score-list">
        <template v-for="entry in scoreEntries">
          <dt :key="entry.key + '-label'">{{ entry.label }}</dt>
          <dd :key="entry.key + '-value'" class="signal-data">{{ entry.value }}</dd>
        </template>
      </dl>
      <p v-else class="no-scores">这条来源没有可用的评分记录。</p>
    </section>
  </aside>
</template>

<script>
export default {
  name: 'EvidenceInspector',
  props: {
    open: { type: Boolean, default: false },
    desktop: { type: Boolean, default: true },
    sources: { type: Array, default: () => [] },
    selectedSource: { type: Object, default: null },
    selectedStage: { type: String, default: 'vector' },
    scoreEntries: { type: Array, default: () => [] }
  },
  watch: {
    open(value) {
      if (value && !this.desktop) this.focusCloseButton()
    },
    desktop(value) {
      if (!value && this.open) this.focusCloseButton()
    }
  },
  computed: {
    stageLabel() { return { vector: '向量检索', bm25: 'BM25 检索', rrf: 'RRF 融合', rerank: '候选重排', answer: '回答生成' }[this.selectedStage] || '证据来源' },
    stageDescription() {
      return {
        vector: '按语义相近程度召回候选片段。查看向量距离、相似度与排名。',
        bm25: '按问题中的关键词匹配候选。查看 BM25 分数与排名。',
        rrf: '合并两条检索通道的顺序，降低单一检索方式的偏差。',
        rerank: '用重排模型再次评估候选，只把最相关来源送给回答。',
        answer: '模型只能依据返回来源生成回答；证据不足时应明确拒答。'
      }[this.selectedStage] || '选择一条来源查看完整内容和评分。'
    }
  },
  methods: {
    focusCloseButton() {
      this.$nextTick(() => {
        setTimeout(() => { if (this.$refs.closeButton) this.$refs.closeButton.focus() }, 0)
      })
    },
    trapFocus(event) {
      if (this.desktop || !this.open || !this.$refs.drawer) return
      const controls = Array.from(this.$refs.drawer.querySelectorAll('button:not(:disabled), select:not(:disabled), input:not(:disabled)'))
      if (!controls.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    },
    sourceLocation(source) {
      if (source && source.articleNumber) return source.articleNumber
      if (source && source.rowNumber !== undefined && source.rowNumber !== null) return '第 ' + source.rowNumber + ' 行'
      return '位置未记录'
    },
    knowledgeBaseName(source) { return source && source.knowledgeBase && source.knowledgeBase.name ? source.knowledgeBase.name : '知识库未记录' },
    sameSource(a, b) { if (!a || !b) return false; return a === b || (a.index !== undefined && a.index === b.index) }
  }
}
</script>

<style scoped>
.evidence-inspector { width: 330px; min-width: 330px; min-height: 0; overflow-y: auto; color: var(--signal-ink); background: #edf1f0; border-left: 1px solid var(--signal-line); }
.inspector-head { min-height: 76px; padding: 16px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--signal-line); }
h2 { margin: 0; font-size: 20px; }
.inspector-close { width: 40px; height: 40px; display: grid; place-items: center; color: var(--signal-ink); background: transparent; border: 1px solid var(--signal-line-strong); cursor: pointer; }
.inspector-close svg { width: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; }
.stage-context { padding: 17px 18px; background: #dde6e3; border-bottom: 1px solid var(--signal-line); }
.stage-context > span { color: var(--signal-faint); font-size: 10px; }
.stage-context strong { margin-left: 8px; color: var(--signal-active-strong); font-size: 12px; }
.stage-context p { margin: 9px 0 0; color: var(--signal-muted); font-size: 12px; line-height: 1.6; }
.inspector-empty { padding: 70px 28px; text-align: center; }
.empty-probe { width: 54px; height: 22px; margin: 0 auto 22px; border-top: 1px solid var(--signal-line-strong); position: relative; }
.empty-probe::before { content: ''; position: absolute; top: -5px; left: calc(50% - 5px); width: 9px; height: 9px; background: var(--signal-line-strong); }
.inspector-empty strong { display: block; }
.inspector-empty p { color: var(--signal-muted); font-size: 12px; line-height: 1.7; }
.source-index { border-bottom: 1px solid var(--signal-line); }
.source-count { margin: 0; padding: 12px 17px; color: var(--signal-muted); font-size: 10px; }
.source-index button { width: 100%; padding: 11px 17px; display: grid; grid-template-columns: 34px minmax(0,1fr); gap: 8px; text-align: left; color: var(--signal-ink); background: transparent; border: 0; border-top: 1px solid #cbd4d1; cursor: pointer; }
.source-index button:hover, .source-index button.active { background: var(--signal-active-soft); }
.source-index button > span:first-child { color: var(--signal-active-strong); font-size: 10px; }
.source-index button > span:last-child { min-width: 0; display: grid; gap: 3px; }
.source-index strong, .source-index small { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-index strong { font-size: 11px; }
.source-index small { color: var(--signal-muted); font-size: 9px; }
.source-detail { padding: 20px 18px 34px; }
.detail-heading > span { color: var(--signal-active-strong); font-size: 9px; }
h3 { margin: 5px 0 3px; font-size: 18px; overflow-wrap: anywhere; }
.detail-heading p { margin: 0; color: var(--signal-muted); font-size: 10px; overflow-wrap: anywhere; }
.source-text { margin: 18px 0 23px; padding: 15px; max-height: 260px; overflow-y: auto; color: #27302f; background: #fff; border: 1px solid var(--signal-line); font-size: 12px; line-height: 1.75; white-space: pre-wrap; overflow-wrap: anywhere; }
h4 { margin: 0 0 10px; font-size: 12px; }
.score-list { margin: 0; display: grid; grid-template-columns: 1fr auto; }
.score-list dt, .score-list dd { margin: 0; padding: 8px 0; border-top: 1px solid var(--signal-line); font-size: 10px; }
.score-list dt { color: var(--signal-muted); }
.score-list dd { color: var(--signal-ink); }
.no-scores { color: var(--signal-muted); font-size: 11px; }
@media (max-width: 1180px) {
  .evidence-inspector { position: fixed; z-index: 55; top: 0; right: 0; bottom: 0; width: min(88vw, 390px); min-width: min(88vw, 390px); box-shadow: -18px 0 46px rgba(0,0,0,.2); transform: translateX(105%); transition: transform 180ms ease-out; }
  .evidence-inspector.open { transform: translateX(0); }
  .evidence-inspector:not(.open) { visibility: hidden; }
}
@media (max-width: 620px) { .evidence-inspector { width: 100%; min-width: 100%; } }
</style>
