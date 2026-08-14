<template>
  <section ref="thread" class="message-thread" aria-label="对话内容" tabindex="-1">
    <div v-if="!messages.length" class="thread-empty">
      <h2>从一条问题开始追踪证据。</h2>
      <p>选择演示知识库后提出问题。系统会在顶部信号轨展示每个检索阶段，并把可核查来源送入右侧检查器。</p>
    </div>

    <article v-for="(item, index) in messages" :key="item.localId || index" :class="['message', 'message--' + normalizedRole(item.role), { error: item.status === 'error' }]">
      <header class="message-head">
        <span class="message-origin">{{ roleLabel(item.role) }}</span>
        <span v-if="item.status === 'streaming'" class="message-state"><i aria-hidden="true"></i>流式接收中</span>
        <span v-else-if="item.status === 'error'" class="message-state error">链路中断</span>
      </header>

      <div class="message-content" v-html="$renderMarkdown(item.content)"></div>

      <div v-if="item.retrievalSummary" class="evidence-summary" aria-label="检索摘要">
        <button type="button" @click="$emit('select-stage', 'vector')"><span class="signal-data">{{ value(item, 'vectorHitCount') }}</span>向量命中</button>
        <button type="button" @click="$emit('select-stage', 'bm25')"><span class="signal-data">{{ value(item, 'bm25HitCount') }}</span>BM25 命中</button>
        <button type="button" @click="$emit('select-stage', 'rrf')"><span class="signal-data">{{ value(item, 'fusedCandidateCount') }}</span>融合候选</button>
        <button type="button" @click="$emit('select-stage', 'rerank')"><span class="signal-data">{{ value(item, 'returnedSourceCount') }}</span>返回来源</button>
        <span :class="['decision', item.retrievalSummary.decision === 'answer' ? 'pass' : 'reject']">
          {{ item.retrievalSummary.decision === 'answer' ? '证据充足' : '证据不足' }}
        </span>
      </div>

      <div v-if="item.sources && item.sources.length" class="source-strip">
        <button v-for="(source, sourceIndex) in item.sources" :key="source.index || sourceIndex" type="button" @click="$emit('open-source', source)">
          <span class="source-number signal-data">[{{ source.index || sourceIndex + 1 }}]</span>
          <span class="source-copy">
            <strong>{{ sourceLocation(source) }}</strong>
            <small>{{ knowledgeBaseName(source) }} · {{ source.sourceFile || '来源文件未记录' }}</small>
          </span>
          <span class="source-score signal-data">{{ primaryScore(source) }}</span>
        </button>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'MessageThread',
  props: { messages: { type: Array, default: () => [] } },
  watch: {
    messages: {
      deep: true,
      handler() { this.scrollToBottom() }
    }
  },
  methods: {
    scrollToBottom() { this.$nextTick(() => { if (this.$refs.thread) this.$refs.thread.scrollTop = this.$refs.thread.scrollHeight }) },
    normalizedRole(role) { return role === 'AI' ? 'assistant' : (role || 'system').toLowerCase() },
    roleLabel(role) { const normalized = this.normalizedRole(role); return normalized === 'user' ? '你的问题' : normalized === 'assistant' ? 'RAG 回答' : '系统通道' },
    value(item, key) { return item.retrievalSummary[key] || 0 },
    sourceLocation(source) {
      if (source && source.articleNumber) return source.articleNumber
      if (source && source.rowNumber !== undefined && source.rowNumber !== null) return '第 ' + source.rowNumber + ' 行'
      return '位置未记录'
    },
    knowledgeBaseName(source) { return source && source.knowledgeBase && source.knowledgeBase.name ? source.knowledgeBase.name : '知识库未记录' },
    primaryScore(source) {
      if (!source || !source.scores) return '查看详情'
      const score = source.scores.rerankScore
      return score === undefined || score === null ? '查看详情' : '重排 ' + Number(score).toFixed(3)
    }
  }
}
</script>

<style scoped>
.message-thread { min-height: 0; flex: 1; overflow-y: auto; padding: clamp(18px, 3vw, 36px); background-color: #f3f6f5; background-image: linear-gradient(rgba(84,105,101,.055) 1px, transparent 1px); background-size: 100% 28px; scroll-behavior: smooth; }
.thread-empty { max-width: 690px; margin: clamp(54px, 12vh, 130px) auto; }
.thread-empty h2 { max-width: 560px; margin: 0 0 18px; font-size: clamp(28px, 4vw, 48px); line-height: 1.08; letter-spacing: -.04em; }
.thread-empty p { max-width: 65ch; margin: 0; color: var(--signal-muted); line-height: 1.8; }
.message { max-width: 760px; margin: 0 auto 34px; }
.message--user { max-width: 620px; margin-right: 0; }
.message--system { padding: 14px 16px; color: var(--signal-muted); background: #e7eeec; border: 1px solid var(--signal-line); }
.message-head { min-height: 24px; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.message-origin { color: var(--signal-muted); font-size: 11px; font-weight: 800; letter-spacing: .08em; }
.message-state { display: flex; align-items: center; gap: 7px; color: var(--signal-progress); font-size: 11px; }
.message-state i { width: 7px; height: 7px; background: var(--signal-progress); animation: receive 800ms ease-out infinite alternate; }
.message-state.error { color: var(--signal-error); }
.message-content { color: var(--signal-ink); font-size: 15px; line-height: 1.8; overflow-wrap: anywhere; }
.message--assistant .message-content { padding: 24px 26px; background: #fff; border: 1px solid var(--signal-line); box-shadow: 0 10px 30px rgba(29,46,42,.07); }
.message--user .message-content { padding: 16px 19px; color: #eaf4f1; background: #24322f; border: 1px solid #3d504b; }
.message.error .message-content { border-color: var(--signal-error); }
.message-content >>> p:first-child { margin-top: 0; }
.message-content >>> p:last-child { margin-bottom: 0; }
.message-content >>> pre { max-width: 100%; padding: 14px; overflow-x: auto; color: #eef5f3; background: var(--signal-dark); }
.message-content >>> code { font-family: var(--signal-data-font); }
.message-content >>> a { color: var(--signal-active-strong); text-underline-offset: 3px; }
.evidence-summary { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px; }
.evidence-summary button, .decision { min-height: 34px; padding: 7px 10px; display: flex; align-items: center; gap: 6px; color: var(--signal-muted); background: #e5ebe9; border: 1px solid #c5cfcc; font-size: 10px; }
.evidence-summary button { cursor: pointer; }
.evidence-summary button:hover { color: var(--signal-active-strong); border-color: var(--signal-active); }
.evidence-summary .signal-data { color: var(--signal-ink); font-size: 12px; font-weight: 700; }
.decision.pass { color: var(--signal-active-strong); background: var(--signal-active-soft); border-color: #8bc7be; font-weight: 700; }
.decision.reject { color: #704200; background: var(--signal-progress-soft); border-color: #daa34c; font-weight: 700; }
.source-strip { margin-top: 10px; display: grid; border-top: 1px solid var(--signal-line); }
.source-strip button { min-width: 0; padding: 11px 8px; display: grid; grid-template-columns: 34px minmax(0,1fr) auto; align-items: center; gap: 9px; text-align: left; color: var(--signal-ink); background: transparent; border: 0; border-bottom: 1px solid var(--signal-line); cursor: pointer; }
.source-strip button:hover { background: var(--signal-active-soft); }
.source-number { color: var(--signal-active-strong); font-size: 11px; }
.source-copy { min-width: 0; display: grid; gap: 3px; }
.source-copy strong { overflow: hidden; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.source-copy small { overflow: hidden; color: var(--signal-muted); font-size: 9px; text-overflow: ellipsis; white-space: nowrap; }
.source-score { color: var(--signal-muted); font-size: 9px; }
@keyframes receive { to { opacity: .35; } }
@media (max-width: 620px) {
  .message-thread { padding: 20px 14px; }
  .message { margin-bottom: 27px; }
  .message--assistant .message-content { padding: 18px 16px; }
  .source-strip button { grid-template-columns: 28px minmax(0,1fr); }
  .source-score { grid-column: 2; }
}
</style>
