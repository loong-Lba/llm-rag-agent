<template>
  <main id="main-content" class="workbench-shell" @keydown.esc="closeLayers">
    <div v-if="mobileHistoryOpen || (!desktopInspector && evidenceOpen)" class="workspace-scrim" aria-hidden="true" @click="closeLayers"></div>

    <HistoryShelf
      :histories="historyList"
      :active-id="openHistoryId"
      :collapsed="isHistoryCollapsed"
      :mobile-open="mobileHistoryOpen"
      :busy="streaming || conversationBusy"
      :loading="historyLoading"
      :error="historyError"
      @toggle="isHistoryCollapsed = !isHistoryCollapsed"
      @close-mobile="closeHistory"
      @create="createNewChat"
      @select="loadHistoryById"
      @delete="confirmDeleteHistory"
    />

    <section ref="workspace" class="workspace" aria-label="RAG 问答工作台" :aria-hidden="mobileHistoryOpen || (!desktopInspector && evidenceOpen) ? 'true' : null">
      <header class="workspace-head">
        <div class="workspace-identity">
          <button ref="historyTrigger" class="mobile-tool" type="button" aria-label="打开会话历史" @click="openHistory">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h10"/></svg>
          </button>
          <div>
            <h1>可视化 RAG 助手 · {{ currentSessionTitle }}</h1>
          </div>
        </div>
        <div class="workspace-tools">
          <KnowledgeBaseStatus
            v-model="selectedKnowledgeBaseId"
            :knowledge-bases="knowledgeBases"
            :loading="knowledgeBasesLoading"
            :disabled="streaming"
            :error="knowledgeBaseError"
          />
          <button ref="evidenceTrigger" class="evidence-tool" type="button" :aria-expanded="String(evidenceOpen)" @click="openEvidence">
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="10" r="5"/><path d="m14 14 6 6M10 7v6M7 10h6"/></svg>
            检查证据
            <span class="signal-data">{{ evidenceSources.length }}</span>
          </button>
        </div>
      </header>

      <SignalRail :message="latestAssistantMessage" :selected-stage="selectedStage" @select-stage="selectStage" />

      <MessageThread
        ref="thread"
        :messages="messages"
        @open-source="showSource"
        @select-stage="selectStage"
      />

      <QuestionComposer
        ref="composer"
        v-model="question"
        :disabled="composerDisabled"
        :streaming="streaming"
        :has-conversation="Boolean(openHistoryId)"
        :has-knowledge-base="Boolean(selectedKnowledgeBaseId)"
        @submit="chat"
        @cancel="cancelActiveRequest(true)"
      />

      <div class="sr-only" aria-live="polite" aria-atomic="true">{{ liveAnnouncement }}</div>
    </section>

    <EvidenceInspector
      :open="evidenceOpen"
      :desktop="desktopInspector"
      :sources="evidenceSources"
      :selected-source="selectedSource"
      :selected-stage="selectedStage"
      :score-entries="scoreEntries(selectedSource)"
      @close="closeEvidence"
      @select-source="selectSource"
    />
  </main>
</template>

<script>
import SignalRail from '../components/workbench/SignalRail'
import HistoryShelf from '../components/workbench/HistoryShelf'
import KnowledgeBaseStatus from '../components/workbench/KnowledgeBaseStatus'
import MessageThread from '../components/workbench/MessageThread'
import EvidenceInspector from '../components/workbench/EvidenceInspector'
import QuestionComposer from '../components/workbench/QuestionComposer'

export default {
  name: 'Chat',
  components: { SignalRail, HistoryShelf, KnowledgeBaseStatus, MessageThread, EvidenceInspector, QuestionComposer },
  data() {
    return {
      question: '',
      streaming: false,
      conversationBusy: false,
      messages: [],
      isHistoryCollapsed: false,
      mobileHistoryOpen: false,
      currentSessionTitle: '新对话',
      historyList: [],
      historyLoading: false,
      historyError: '',
      openHistoryId: 0,
      userId: null,
      knowledgeBases: [],
      knowledgeBasesLoading: false,
      knowledgeBaseError: '',
      selectedKnowledgeBaseId: '',
      activeEventSource: null,
      activeRequestId: null,
      activeAssistantMessage: null,
      historyLoadToken: 0,
      localMessageSequence: 0,
      selectedStage: 'vector',
      evidenceOpen: false,
      selectedSource: null,
      desktopInspector: true,
      liveAnnouncement: '',
      lastQuestion: ''
    }
  },
  computed: {
    composerDisabled() {
      return this.streaming || this.conversationBusy || !this.openHistoryId || !this.selectedKnowledgeBaseId
    },
    latestAssistantMessage() {
      for (let index = this.messages.length - 1; index >= 0; index -= 1) {
        const role = this.messages[index].role
        if (role === 'assistant' || role === 'AI') return this.messages[index]
      }
      return null
    },
    evidenceSources() {
      return this.latestAssistantMessage && this.latestAssistantMessage.sources ? this.latestAssistantMessage.sources : []
    }
  },
  watch: {
    evidenceSources(sources) {
      if (!sources.length) this.selectedSource = null
      else if (!this.selectedSource || sources.indexOf(this.selectedSource) === -1) this.selectedSource = sources[0]
    }
  },
  methods: {
    nextLocalId() {
      this.localMessageSequence += 1
      return 'message-' + this.localMessageSequence
    },
    createRequestId() {
      if (window.crypto && window.crypto.randomUUID) return window.crypto.randomUUID()
      return 'rag-' + Date.now() + '-' + Math.random().toString(16).slice(2)
    },
    updateViewport() {
      this.desktopInspector = window.innerWidth > 1180
      if (this.desktopInspector) this.evidenceOpen = true
      if (window.innerWidth > 760) this.mobileHistoryOpen = false
    },
    announce(text) { this.liveAnnouncement = ''; this.$nextTick(() => { this.liveAnnouncement = text }) },
    handleUnauthorized(error) {
      const status = error && error.response && error.response.status
      if (status !== 401 && status !== 403) return false
      sessionStorage.removeItem('userId')
      sessionStorage.removeItem('username')
      this.$router.replace({ path: '/', query: { reason: 'login-required' } })
      return true
    },
    loadKnowledgeBases() {
      this.knowledgeBasesLoading = true
      this.knowledgeBaseError = ''
      return this.$axios.get(this.$serverUrlBase + 'chat/knowledgeBases').then(res => {
        this.knowledgeBases = res.data.data || []
        const ready = this.knowledgeBases.find(item => item.status !== 'unavailable')
        if (!this.selectedKnowledgeBaseId && ready) this.selectedKnowledgeBaseId = ready.id
        if (!this.knowledgeBases.length) this.knowledgeBaseError = '没有可用知识库。'
      }).catch(error => {
        if (!this.handleUnauthorized(error)) this.knowledgeBaseError = '知识库状态加载失败，请刷新重试。'
      }).then(() => { this.knowledgeBasesLoading = false })
    },
    historyListLoad() {
      this.historyLoading = true
      this.historyError = ''
      return this.$axios.get(this.$serverUrlBase + 'history/list', { params: { userId: this.userId } }).then(res => {
        this.historyList = res.data.data || []
        const current = this.historyList.find(item => item.historyId === this.openHistoryId)
        if (current) this.currentSessionTitle = current.question || '新对话'
      }).catch(error => {
        if (!this.handleUnauthorized(error)) this.historyError = '会话记录加载失败。'
      }).then(() => { this.historyLoading = false })
    },
    normalizeHistoryMessages(items) {
      return (items || []).map(item => {
        const rag = item.rag || null
        return {
          localId: this.nextLocalId(),
          role: item.role === 'AI' ? 'assistant' : item.role,
          content: item.content || '',
          status: 'done',
          stages: [],
          sources: rag && rag.sources ? rag.sources : [],
          retrievalSummary: rag && rag.retrievalSummary ? rag.retrievalSummary : null,
          knowledgeBase: rag && rag.knowledgeBase ? rag.knowledgeBase : null
        }
      })
    },
    loadHistoryById(historyId) {
      if (this.conversationBusy || (historyId === this.openHistoryId && this.streaming)) return
      this.cancelActiveRequest(true)
      this.mobileHistoryOpen = false
      this.openHistoryId = historyId
      this.historyLoadToken += 1
      const token = this.historyLoadToken
      this.conversationBusy = true
      this.announce('正在读取历史对话。')
      this.$axios.get(this.$serverUrlBase + 'history/findHistoryById', { params: { historyId: historyId } }).then(res => {
        if (token !== this.historyLoadToken) return
        this.messages = this.normalizeHistoryMessages(res.data.data)
        const current = this.historyList.find(item => item.historyId === historyId)
        this.currentSessionTitle = current ? (current.question || '新对话') : '历史对话'
        this.selectedStage = 'answer'
        this.announce('历史对话已载入。')
      }).catch(error => {
        if (token === this.historyLoadToken && !this.handleUnauthorized(error)) {
          this.$message.error('历史对话加载失败')
          this.announce('历史对话加载失败，请重试。')
        }
      }).then(() => { if (token === this.historyLoadToken) this.conversationBusy = false })
    },
    createNewChat() {
      if (this.streaming || this.conversationBusy) return
      this.historyLoadToken += 1
      this.cancelActiveRequest(true)
      this.conversationBusy = true
      this.mobileHistoryOpen = false
      this.$axios.post(this.$serverUrlBase + 'chat/createNewChat', null, { params: { user_id: this.userId } }).then(res => {
        if (res.data.data === undefined || res.data.data === null) throw new Error('missing history id')
        this.openHistoryId = res.data.data
        this.currentSessionTitle = '新对话'
        this.messages = []
        this.question = ''
        this.selectedStage = 'vector'
        this.selectedSource = null
        this.announce('新对话已创建，可以开始提问。')
        return this.historyListLoad()
      }).then(() => {
        this.$nextTick(() => { if (this.$refs.composer) this.$refs.composer.focus() })
      }).catch(error => {
        if (!this.handleUnauthorized(error)) {
          this.$message.error('新建对话失败')
          this.announce('新建对话失败，请重试。')
        }
      }).then(() => { this.conversationBusy = false })
    },
    confirmDeleteHistory(historyId) {
      const item = this.historyList.find(history => history.historyId === historyId)
      const label = item && item.question ? item.question : '这条会话'
      this.$confirm('删除“' + label + '”后无法恢复。', '确认删除会话', {
        confirmButtonText: '删除会话', cancelButtonText: '保留会话', type: 'warning'
      }).then(() => this.deleteHistory(historyId)).catch(() => {})
    },
    deleteHistory(historyId) {
      if (this.streaming || this.conversationBusy) return
      this.historyLoadToken += 1
      if (historyId === this.openHistoryId) this.cancelActiveRequest(true)
      this.conversationBusy = true
      this.$axios.delete(this.$serverUrlBase + 'history/deleteHistoryByRootId', { params: { history_id: historyId } }).then(() => {
        this.historyList = this.historyList.filter(item => item.historyId !== historyId)
        if (historyId === this.openHistoryId) {
          this.openHistoryId = 0
          this.currentSessionTitle = '新对话'
          this.messages = []
          this.selectedSource = null
        }
        this.announce('会话已删除。')
      }).catch(error => {
        if (!this.handleUnauthorized(error)) this.$message.error('删除对话失败')
      }).then(() => { this.conversationBusy = false })
    },
    cancelActiveRequest(markCancelled) {
      const assistant = this.activeAssistantMessage
      if (this.activeEventSource) this.activeEventSource.close()
      if (markCancelled && assistant && assistant.status === 'streaming') {
        assistant.status = 'error'
        assistant.error = '请求已取消'
        assistant.content = assistant.content || '请求已取消。你可以修改问题后重新发送。'
        this.updateStage(assistant, 'error', 'error')
        this.announce('已停止接收回答，已收到的内容仍然保留。')
      }
      this.activeEventSource = null
      this.activeRequestId = null
      this.activeAssistantMessage = null
      this.streaming = false
    },
    stageLabel(type) {
      const labels = { route: '已锁定所选知识库', searching: '向量与 BM25 检索', reranking: 'RRF 融合与重排序', sources: '来源已就绪', answer_start: '正在生成回答', done: '回答与来源已保存', error: '请求失败' }
      return labels[type] || type
    },
    updateStage(message, type, status) {
      const stage = message.stages.find(item => item.type === type)
      if (stage) stage.status = status
      else message.stages.push({ type: type, label: this.stageLabel(type), status: status })
    },
    parseEvent(event, source, message) {
      if (source !== this.activeEventSource) return null
      let payload
      try { payload = JSON.parse(event.data) } catch (error) {
        this.failRequest(source, message, 'SSE 数据解析失败')
        return null
      }
      if (!payload.requestId || payload.requestId !== this.activeRequestId) return null
      message.requestId = payload.requestId
      return payload
    },
    failRequest(source, message, text) {
      if (source !== this.activeEventSource) return
      message.status = 'error'
      message.error = text
      message.content = message.content || text + '。请检查服务状态后重试。'
      this.updateStage(message, 'error', 'error')
      source.close()
      this.activeEventSource = null
      this.activeRequestId = null
      this.activeAssistantMessage = null
      this.streaming = false
      this.announce(text + '，可以重试。')
    },
    chat() {
      const myQuestion = (this.question || '').trim()
      if (!myQuestion) { this.$message.warning('请输入问题'); return }
      if (this.streaming || this.conversationBusy) return
      if (!this.openHistoryId) { this.$message.warning('请先新建或选择对话'); this.openHistory(); return }
      if (!this.selectedKnowledgeBaseId) { this.$message.warning('请选择知识库'); return }

      this.question = ''
      this.lastQuestion = myQuestion
      const userMessage = { localId: this.nextLocalId(), role: 'user', content: myQuestion }
      const assistantMessage = { localId: this.nextLocalId(), role: 'assistant', content: '', status: 'streaming', stages: [], sources: [], retrievalSummary: null, requestId: null, error: null }
      this.messages.push(userMessage, assistantMessage)
      this.streaming = true
      this.activeAssistantMessage = assistantMessage
      this.selectedStage = 'vector'
      this.selectedSource = null
      this.announce('问题已发送，正在启动证据信号链。')

      const requestId = this.createRequestId()
      assistantMessage.requestId = requestId
      this.activeRequestId = requestId
      const params = new URLSearchParams({ question: myQuestion, history_id: String(this.openHistoryId), knowledge_base: this.selectedKnowledgeBaseId, request_id: requestId })
      const source = new EventSource(this.$serverUrlBase + 'chat/chatStream?' + params.toString())
      this.activeEventSource = source
      const eventTypes = ['route', 'searching', 'reranking', 'sources', 'answer_start', 'token', 'done', 'error']
      eventTypes.forEach(type => {
        source.addEventListener(type, event => {
          const payload = this.parseEvent(event, source, assistantMessage)
          if (!payload) return
          const data = payload.data || {}
          if (type === 'token') {
            assistantMessage.content += data.content || ''
          } else if (type === 'sources') {
            assistantMessage.sources = Array.isArray(data.items) ? data.items : []
            assistantMessage.retrievalSummary = data.summary || null
            this.updateStage(assistantMessage, type, 'done')
            if (assistantMessage.sources.length) this.selectedSource = assistantMessage.sources[0]
            this.announce('来源已就绪，共 ' + assistantMessage.sources.length + ' 条。')
          } else if (type === 'done') {
            assistantMessage.status = 'done'
            assistantMessage.stages.forEach(stage => { if (stage.status === 'active') stage.status = 'done' })
            this.updateStage(assistantMessage, type, 'done')
            source.close()
            if (source === this.activeEventSource) {
              this.activeEventSource = null
              this.activeRequestId = null
              this.activeAssistantMessage = null
              this.streaming = false
            }
            if (this.currentSessionTitle === '新对话') this.currentSessionTitle = myQuestion
            this.selectedStage = 'answer'
            const sufficient = assistantMessage.retrievalSummary && assistantMessage.retrievalSummary.decision === 'answer'
            this.announce('回答完成，' + (sufficient ? '证据充足。' : '请检查证据判断。'))
            this.historyListLoad()
          } else if (type === 'error') {
            this.failRequest(source, assistantMessage, data.message || '请求失败')
          } else {
            this.updateStage(assistantMessage, type, type === 'answer_start' ? 'active' : 'done')
            this.announce(this.stageLabel(type))
          }
        })
      })
      source.onerror = () => { if (source === this.activeEventSource) this.failRequest(source, assistantMessage, '连接中断') }
    },
    selectStage(stage) {
      this.selectedStage = stage
      if (!this.desktopInspector) this.evidenceOpen = true
    },
    openHistory() { this.mobileHistoryOpen = true; this.setWorkspaceInert(true) },
    openEvidence() { this.evidenceOpen = true; if (!this.desktopInspector) this.setWorkspaceInert(true) },
    closeHistory() {
      this.mobileHistoryOpen = false
      this.setWorkspaceInert(false)
      this.$nextTick(() => { if (this.$refs.historyTrigger) this.$refs.historyTrigger.focus() })
    },
    setWorkspaceInert(value) {
      if (!this.$refs.workspace) return
      if (value) this.$refs.workspace.setAttribute('inert', '')
      else this.$refs.workspace.removeAttribute('inert')
    },
    closeEvidence() {
      const wasOpen = this.evidenceOpen
      this.evidenceOpen = false
      this.setWorkspaceInert(false)
      if (wasOpen) this.$nextTick(() => { if (this.$refs.evidenceTrigger) this.$refs.evidenceTrigger.focus() })
    },
    closeLayers() {
      const historyWasOpen = this.mobileHistoryOpen
      const evidenceWasOpen = !this.desktopInspector && this.evidenceOpen
      this.mobileHistoryOpen = false
      if (!this.desktopInspector) this.evidenceOpen = false
      this.setWorkspaceInert(false)
      this.$nextTick(() => {
        if (historyWasOpen && this.$refs.historyTrigger) this.$refs.historyTrigger.focus()
        else if (evidenceWasOpen && this.$refs.evidenceTrigger) this.$refs.evidenceTrigger.focus()
      })
    },
    showSource(source) {
      this.selectedSource = source
      this.selectedStage = 'answer'
      this.evidenceOpen = true
    },
    selectSource(source) { this.selectedSource = source },
    formatScore(value) {
      const numeric = Number(value)
      return Number.isFinite(numeric) ? numeric.toFixed(4) : String(value)
    },
    scoreEntries(source) {
      const labels = { vectorDistance: '向量距离', vectorSimilarity: '向量相似度', vectorRank: '向量排名', bm25Score: 'BM25 分数', bm25Rank: 'BM25 排名', rrfScore: 'RRF 分数', rrfRank: 'RRF 排名', rerankScore: '重排分数', rerankRank: '重排排名' }
      const scores = source && source.scores ? source.scores : {}
      return Object.keys(labels).filter(key => scores[key] !== undefined && scores[key] !== null).map(key => ({ key: key, label: labels[key], value: typeof scores[key] === 'number' ? this.formatScore(scores[key]) : scores[key] }))
    }
  },
  mounted() {
    this.userId = sessionStorage.getItem('userId')
    if (!this.userId) { this.$router.replace({ path: '/', query: { reason: 'login-required' } }); return }
    this.updateViewport()
    window.addEventListener('resize', this.updateViewport)
    this.loadKnowledgeBases()
    this.historyListLoad()
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.updateViewport)
    this.cancelActiveRequest(true)
  }
}
</script>

<style scoped>
.workbench-shell { height: 100vh; min-height: 620px; display: flex; overflow: hidden; background: var(--signal-canvas); }
.workspace-scrim { position: fixed; z-index: 50; inset: 0; background: rgba(12, 20, 18, .55); }
.workspace { min-width: 0; min-height: 0; flex: 1; display: flex; flex-direction: column; background: var(--signal-surface); }
.workspace-head { min-height: 76px; padding: 12px 18px; display: flex; align-items: center; justify-content: space-between; gap: 24px; background: #fff; border-bottom: 1px solid var(--signal-line); }
.workspace-identity { min-width: 0; display: flex; align-items: center; gap: 12px; }
h1 { max-width: 38ch; margin: 0; overflow: hidden; color: var(--signal-ink); font-size: 19px; text-overflow: ellipsis; white-space: nowrap; }
.workspace-tools { display: flex; align-items: center; gap: 12px; }
.mobile-tool, .evidence-tool { min-height: 42px; color: var(--signal-ink); background: transparent; border: 1px solid var(--signal-line-strong); cursor: pointer; }
.mobile-tool { width: 42px; display: none; place-items: center; }
.mobile-tool svg, .evidence-tool svg { width: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: square; }
.evidence-tool { padding: 9px 11px; display: none; align-items: center; gap: 7px; font-size: 11px; font-weight: 700; }
.evidence-tool span { min-width: 20px; padding: 2px 4px; color: #fff; background: var(--signal-active-strong); text-align: center; }
@media (max-width: 1180px) { .evidence-tool { display: flex; } }
@media (max-width: 760px) {
  .workbench-shell { min-height: 100dvh; height: 100dvh; }
  .workspace-head { padding: 10px 12px; align-items: flex-start; flex-direction: column; gap: 10px; }
  .workspace-identity, .workspace-tools { width: 100%; }
  .workspace-tools { align-items: flex-end; }
  .workspace-tools > :first-child { flex: 1; }
  .mobile-tool { display: grid; }
  .evidence-tool { flex: 0 0 auto; }
  h1 { max-width: 65vw; }
}
@media (max-width: 480px) {
  .workspace-tools { align-items: stretch; flex-direction: column; }
  .evidence-tool { justify-content: center; }
}
</style>
