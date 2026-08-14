<template>
  <nav class="signal-rail" aria-label="本次回答的 RAG 信号链">
    <div class="rail-heading">
      <div>
        <strong>证据信号链</strong>
        <span>{{ chainStatus }}</span>
      </div>
      <span class="rail-request signal-data">{{ requestLabel }}</span>
    </div>
    <ol class="rail-track">
      <li v-for="(stage, index) in stages" :key="stage.id" :class="['rail-stage', stage.status]">
        <button
          type="button"
          :aria-current="selectedStage === stage.id ? 'step' : null"
          :aria-label="stage.label + '，' + statusLabel(stage.status)"
          @click="$emit('select-stage', stage.id)"
          @keydown.left.prevent="focusSibling($event, index - 1)"
          @keydown.right.prevent="focusSibling($event, index + 1)"
        >
          <span class="stage-probe" aria-hidden="true"></span>
          <span class="stage-index signal-data">{{ stageNumber(index) }}</span>
          <strong>{{ stage.label }}</strong>
          <small>{{ statusLabel(stage.status) }}</small>
        </button>
      </li>
    </ol>
  </nav>
</template>

<script>
export default {
  name: 'SignalRail',
  props: {
    message: { type: Object, default: null },
    selectedStage: { type: String, default: '' }
  },
  computed: {
    requestLabel() {
      if (!this.message || !this.message.requestId) return '等待请求'
      return 'REQ ' + this.message.requestId.slice(-8).toUpperCase()
    },
    stages() {
      const statuses = { vector: 'waiting', bm25: 'waiting', rrf: 'waiting', rerank: 'waiting', answer: 'waiting' }
      if (this.message) {
        const raw = this.message.stages || []
        const route = raw.find(item => item.type === 'route')
        const searching = raw.find(item => item.type === 'searching')
        const reranking = raw.find(item => item.type === 'reranking')
        const sources = raw.find(item => item.type === 'sources')
        const answerStart = raw.find(item => item.type === 'answer_start')
        const done = raw.find(item => item.type === 'done')
        const error = raw.find(item => item.type === 'error')
        if (route) statuses.vector = route.status === 'error' ? 'error' : 'active'
        if (searching) { statuses.vector = searching.status; statuses.bm25 = searching.status }
        if (reranking) { statuses.rrf = reranking.status; statuses.rerank = reranking.status }
        if (sources) { statuses.vector = 'done'; statuses.bm25 = 'done'; statuses.rrf = 'done'; statuses.rerank = sources.status }
        if (answerStart) statuses.answer = answerStart.status
        if (done) Object.keys(statuses).forEach(key => { statuses[key] = 'done' })
        if (error) {
          const firstWaiting = Object.keys(statuses).find(key => statuses[key] === 'waiting' || statuses[key] === 'active')
          if (firstWaiting) statuses[firstWaiting] = 'error'
        }
      }
      return [
        { id: 'vector', label: '向量', status: statuses.vector },
        { id: 'bm25', label: 'BM25', status: statuses.bm25 },
        { id: 'rrf', label: 'RRF', status: statuses.rrf },
        { id: 'rerank', label: '重排', status: statuses.rerank },
        { id: 'answer', label: '回答', status: statuses.answer }
      ]
    },
    chainStatus() {
      if (!this.message) return '提出问题后，这里会显示证据如何汇合'
      if (this.message.status === 'error') return '链路中断，可保留已收到的内容后重试'
      if (this.message.status === 'streaming') return '检索与生成正在进行'
      const decision = this.message.retrievalSummary && this.message.retrievalSummary.decision
      return decision === 'answer' ? '链路完成，证据充足' : (decision ? '链路完成，证据不足' : '链路已完成')
    }
  },
  methods: {
    stageNumber(index) { return index < 9 ? '0' + (index + 1) : String(index + 1) },
    statusLabel(status) {
      return { waiting: '等待', active: '运行中', done: '完成', error: '错误' }[status] || status
    },
    focusSibling(event, index) {
      const buttons = event.currentTarget.closest('ol').querySelectorAll('button')
      if (buttons[index]) buttons[index].focus()
    }
  }
}
</script>

<style scoped>
.signal-rail { padding: 14px 18px 12px; color: #eef5f3; background: var(--signal-dark); border-bottom: 1px solid #344440; }
.rail-heading { margin-bottom: 12px; display: flex; justify-content: space-between; align-items: flex-end; gap: 14px; }
.rail-heading > div { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
.rail-heading strong { font-size: 13px; }
.rail-heading span { color: #9fb3af; font-size: 11px; }
.rail-request { flex: 0 0 auto; color: #7f9691 !important; }
.rail-track { margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(92px, 1fr)); list-style: none; }
.rail-stage { position: relative; border-top: 1px solid #4b605b; }
.rail-stage:not(:last-child)::after { content: ''; position: absolute; z-index: 0; top: -1px; left: 50%; right: -50%; height: 1px; background: #4b605b; }
.rail-stage.done:not(:last-child)::after { background: #50c7b5; }
.rail-stage button { position: relative; z-index: 1; width: 100%; min-height: 58px; padding: 14px 8px 4px 0; display: grid; grid-template-columns: 22px 1fr; grid-template-rows: auto auto; text-align: left; color: #dbe5e2; background: transparent; border: 0; cursor: pointer; }
.stage-probe { position: absolute; top: -5px; left: 0; width: 9px; height: 9px; background: #6f817d; border: 2px solid var(--signal-dark); }
.stage-index { grid-row: 1 / 3; color: #6f8580; font-size: 10px; }
.rail-stage strong { font-size: 12px; }
.rail-stage small { color: #8da19d; font-size: 10px; }
.rail-stage.active .stage-probe { background: #e4a33b; animation: stage-pulse 850ms ease-out infinite alternate; }
.rail-stage.done .stage-probe { background: #50c7b5; }
.rail-stage.error .stage-probe { background: #e06b5d; }
.rail-stage button[aria-current="step"] { background: #24322f; }
@keyframes stage-pulse { to { opacity: .35; } }
@media (max-width: 700px) {
  .signal-rail { padding-left: 14px; padding-right: 14px; overflow-x: auto; }
  .rail-heading { min-width: 560px; }
  .rail-track { min-width: 560px; }
}
</style>
