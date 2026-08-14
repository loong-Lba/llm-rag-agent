<template>
  <aside ref="drawer" :class="['history-shelf', { collapsed: collapsed, open: mobileOpen }]" aria-label="会话历史" :role="mobileOpen ? 'dialog' : null" :aria-modal="mobileOpen ? 'true' : null" @keydown.tab="trapFocus">
    <div class="shelf-head">
      <div v-show="!collapsed || mobileOpen">
        <h2>会话记录</h2>
      </div>
      <button class="shelf-icon" type="button" :aria-label="mobileOpen ? '关闭会话历史' : (collapsed ? '展开会话历史' : '折叠会话历史')" :aria-expanded="String(!collapsed || mobileOpen)" @click="$emit(mobileOpen ? 'close-mobile' : 'toggle')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>
      </button>
    </div>

    <div v-show="!collapsed || mobileOpen" class="shelf-body">
      <button class="signal-button new-chat" type="button" :disabled="busy" @click="$emit('create')">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>
        新建对话
      </button>
      <div class="history-caption">
        <span>历史信号</span>
        <span class="signal-data">{{ histories.length }}</span>
      </div>
      <p v-if="loading" class="history-state" role="status">正在读取会话记录…</p>
      <p v-else-if="error" class="history-state error" role="status">{{ error }}</p>
      <p v-else-if="!histories.length" class="history-state">还没有会话。新建一条通道开始提问。</p>
      <ul v-else class="history-list">
        <li v-for="item in histories" :key="item.historyId" :class="{ active: item.historyId === activeId }">
          <button class="history-select" type="button" :aria-current="item.historyId === activeId ? 'page' : null" :disabled="busy" @click="$emit('select', item.historyId)">
            <strong>{{ item.question || '新对话' }}</strong>
            <span class="signal-data">{{ item.createTime || '时间未记录' }}</span>
          </button>
          <button class="history-delete" type="button" :disabled="busy" :aria-label="'删除会话：' + (item.question || '新对话')" @click="$emit('delete', item.historyId)">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 7h12M9 7V4h6v3m-8 0 1 13h8l1-13M10 11v5m4-5v5"/></svg>
          </button>
        </li>
      </ul>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'HistoryShelf',
  props: {
    histories: { type: Array, default: () => [] },
    activeId: { type: [Number, String], default: 0 },
    collapsed: { type: Boolean, default: false },
    mobileOpen: { type: Boolean, default: false },
    busy: { type: Boolean, default: false },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' }
  },
  watch: {
    mobileOpen(open) {
      if (open) this.$nextTick(() => {
        const first = this.$refs.drawer && this.$refs.drawer.querySelector('button')
        if (first) first.focus()
      })
    }
  },
  methods: {
    trapFocus(event) {
      if (!this.mobileOpen || !this.$refs.drawer) return
      const controls = Array.from(this.$refs.drawer.querySelectorAll('button:not(:disabled), select:not(:disabled), input:not(:disabled)'))
      if (!controls.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
  }
}
</script>

<style scoped>
.history-shelf { width: 278px; min-width: 278px; min-height: 0; display: flex; flex-direction: column; color: #eef5f3; background: #16201e; border-right: 1px solid #3c4c48; transition: transform 180ms ease-out; }
.history-shelf.collapsed { width: 58px; min-width: 58px; }
.shelf-head { min-height: 76px; padding: 17px 16px; display: flex; align-items: center; justify-content: space-between; gap: 12px; border-bottom: 1px solid #33433f; }
h2 { margin: 0; font-size: 20px; }
.shelf-icon { width: 40px; height: 40px; flex: 0 0 40px; display: grid; place-items: center; color: #c3d0cd; background: transparent; border: 1px solid #4e615c; cursor: pointer; }
.shelf-icon svg, .new-chat svg, .history-delete svg { width: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: square; }
.shelf-body { min-height: 0; flex: 1; padding: 15px 12px; display: flex; flex-direction: column; }
.new-chat { width: 100%; display: flex; align-items: center; justify-content: center; gap: 9px; color: #0c2924; background: #61d3c0; border-color: #61d3c0; }
.new-chat:hover:not(:disabled) { color: #fff; }
.history-caption { margin: 25px 4px 9px; display: flex; justify-content: space-between; color: #90a49f; font-size: 11px; }
.history-state { margin: 0; padding: 22px 10px; color: #9fb1ad; font-size: 13px; line-height: 1.7; }
.history-state.error { color: #ffb5aa; }
.history-list { min-height: 0; margin: 0; padding: 0 3px 20px; overflow-y: auto; list-style: none; }
.history-list li { position: relative; display: flex; align-items: stretch; border-top: 1px solid #344440; }
.history-list li:last-child { border-bottom: 1px solid #344440; }
.history-list li.active { background: #24322f; }
.history-list li.active::before { content: ''; position: absolute; top: 11px; left: -3px; width: 5px; height: 5px; background: #61d3c0; }
.history-select { min-width: 0; flex: 1; padding: 13px 7px; display: grid; gap: 7px; text-align: left; color: #e2ebe8; background: transparent; border: 0; cursor: pointer; }
.history-select strong { overflow: hidden; font-size: 13px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.history-select span { color: #7f938e; font-size: 9px; }
.history-delete { width: 38px; display: grid; place-items: center; color: #869995; background: transparent; border: 0; cursor: pointer; }
.history-delete:hover:not(:disabled) { color: #ffb5aa; background: #3a2926; }
.history-select:disabled, .history-delete:disabled { opacity: .5; cursor: not-allowed; }
@media (max-width: 1050px) { .history-shelf { width: 230px; min-width: 230px; } }
@media (max-width: 760px) {
  .history-shelf, .history-shelf.collapsed { position: fixed; z-index: 60; inset: 0 auto 0 0; width: min(88vw, 340px); min-width: min(88vw, 340px); box-shadow: 18px 0 46px rgba(0,0,0,.28); transform: translateX(-105%); transition: transform 180ms ease-out; }
  .history-shelf.open { transform: translateX(0); }
  .history-shelf:not(.open) { visibility: hidden; }
}
</style>
