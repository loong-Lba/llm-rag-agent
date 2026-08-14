<template>
  <section class="kb-control" aria-labelledby="kb-label">
    <div class="kb-title-row">
      <label id="kb-label" for="knowledge-base">知识库通道</label>
      <span v-if="selected" :class="['status-flag', selected.status]">{{ statusText(selected.status) }}</span>
    </div>
    <select id="knowledge-base" class="kb-select" :value="value" :disabled="disabled || loading" @change="$emit('input', $event.target.value)">
      <option value="" disabled>{{ loading ? '正在读取知识库…' : '选择知识库' }}</option>
      <option v-for="item in knowledgeBases" :key="item.id" :value="item.id" :disabled="item.status === 'unavailable'">{{ item.name }}</option>
    </select>
    <p v-if="error" class="kb-message error" role="status">{{ error }}</p>
    <p v-else-if="selected" class="kb-message">
      <span class="signal-data">{{ selected.documentCount || 0 }}</span> 文档
      <span aria-hidden="true">/</span>
      <span class="signal-data">{{ selected.chunkCount || 0 }}</span> 片段
      <span v-if="selected.statusMessage"> · {{ selected.statusMessage }}</span>
    </p>
  </section>
</template>

<script>
export default {
  name: 'KnowledgeBaseStatus',
  model: { prop: 'value', event: 'input' },
  props: {
    value: { type: [String, Number], default: '' },
    knowledgeBases: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  computed: {
    selected() {
      const id = this.value
      return this.knowledgeBases.find(item => String(item.id) === String(id)) || null
    }
  },
  methods: {
    statusText(status) {
      return { ready: '可用', degraded: '降级', unavailable: '不可用' }[status] || status || '状态未知'
    }
  }
}
</script>

<style scoped>
.kb-control { min-width: 250px; }
.kb-title-row { margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.kb-title-row label { color: var(--signal-muted); font-size: 11px; font-weight: 700; }
.status-flag { padding: 2px 6px; color: var(--signal-active-strong); background: var(--signal-active-soft); font-size: 10px; font-weight: 700; }
.status-flag.degraded { color: #714200; background: var(--signal-progress-soft); }
.status-flag.unavailable { color: var(--signal-error); background: var(--signal-error-soft); }
.kb-select { width: 100%; min-height: 40px; padding: 8px 34px 8px 10px; color: var(--signal-ink); background: #fff; border: 1px solid var(--signal-line-strong); border-radius: 0; }
.kb-select:focus { border-color: var(--signal-focus); box-shadow: 0 0 0 3px rgba(0,95,204,.16); }
.kb-message { max-width: 42ch; margin: 6px 0 0; color: var(--signal-muted); font-size: 10px; line-height: 1.5; }
.kb-message.error { color: var(--signal-error); }
@media (max-width: 760px) { .kb-control { min-width: 0; width: 100%; } }
</style>
