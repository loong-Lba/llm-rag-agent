<template>
  <footer class="question-composer">
    <label class="sr-only" for="rag-question">输入要向当前知识库提出的问题</label>
    <textarea
      id="rag-question"
      ref="question"
      class="composer-input"
      rows="1"
      :value="value"
      :disabled="disabled"
      :placeholder="placeholder"
      @input="$emit('input', $event.target.value)"
      @keydown.enter.exact.prevent="submit"
    ></textarea>
    <div class="composer-actions">
      <span class="composer-hint">Enter 发送 · Shift + Enter 换行</span>
      <button v-if="streaming" class="cancel-button" type="button" @click="$emit('cancel')">
        <span aria-hidden="true"></span>停止接收
      </button>
      <button v-else class="signal-button send-button" type="button" :disabled="disabled || !value.trim()" @click="submit">
        发送问题
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 14-7-4 14-3-6-7-1Z"/></svg>
      </button>
    </div>
  </footer>
</template>

<script>
export default {
  name: 'QuestionComposer',
  model: { prop: 'value', event: 'input' },
  props: {
    value: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    streaming: { type: Boolean, default: false },
    hasConversation: { type: Boolean, default: false },
    hasKnowledgeBase: { type: Boolean, default: false }
  },
  computed: {
    placeholder() {
      if (!this.hasConversation) return '先新建或选择一条会话'
      if (!this.hasKnowledgeBase) return '先选择可用知识库'
      return '输入问题，追踪证据如何形成…'
    }
  },
  methods: {
    submit() { if (!this.disabled && this.value.trim()) this.$emit('submit') },
    focus() { if (this.$refs.question) this.$refs.question.focus() }
  }
}
</script>

<style scoped>
.question-composer { padding: 12px 16px 14px; display: grid; grid-template-columns: minmax(0,1fr) auto; align-items: end; gap: 12px; background: #fff; border-top: 1px solid var(--signal-line); }
.composer-input { width: 100%; min-height: 48px; max-height: 144px; resize: vertical; padding: 12px 13px; color: var(--signal-ink); background: #f7f9f8; border: 1px solid var(--signal-line-strong); border-radius: 0; line-height: 1.5; }
.composer-input::placeholder { color: #697572; }
.composer-input:focus { border-color: var(--signal-focus); box-shadow: 0 0 0 3px rgba(0,95,204,.16); }
.composer-actions { display: grid; grid-template-columns: auto; gap: 6px; justify-items: end; }
.composer-hint { color: var(--signal-faint); font-size: 9px; }
.send-button, .cancel-button { min-height: 44px; display: flex; align-items: center; justify-content: center; gap: 9px; }
.send-button svg { width: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; }
.cancel-button { padding: 9px 15px; color: var(--signal-error); background: var(--signal-error-soft); border: 1px solid #d88b81; font-weight: 700; cursor: pointer; }
.cancel-button span { width: 9px; height: 9px; background: var(--signal-error); }
@media (max-width: 620px) {
  .question-composer { grid-template-columns: 1fr; padding: 10px 12px; }
  .composer-actions { grid-template-columns: 1fr auto; align-items: center; justify-items: stretch; }
  .composer-hint { min-width: 0; }
}
</style>
