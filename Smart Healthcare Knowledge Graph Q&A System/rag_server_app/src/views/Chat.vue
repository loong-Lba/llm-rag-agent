<template>
  <div class="chat-page">
    <div class="chat-page__aurora chat-page__aurora--one"></div>
    <div class="chat-page__aurora chat-page__aurora--two"></div>
    <div class="chat-page__grid"></div>

    <div class="chat-shell">
      <aside class="chat-sidebar">
        <div>
          <div class="chat-sidebar__badge">Medical Graph QA</div>
          <h1 class="chat-sidebar__title">智能医疗问答</h1>
          <p class="chat-sidebar__subtitle">
            你好，{{ username }}。当前支持会话历史、上下文追问，以及判断是否需要走医疗图谱查询。
          </p>
        </div>

        <div class="chat-sidebar__actions">
          <el-button type="primary" size="mini" @click="createSession">新建对话</el-button>
        </div>

        <div class="chat-sidebar__sessions">
          <div class="chat-sidebar__sessions-title">历史会话</div>
          <div
            v-for="item in sessionList"
            :key="item.id"
            class="chat-session-item"
            :class="{ 'chat-session-item--active': item.id === sessionId }"
            @click="selectSession(item.id)"
          >
            <div class="chat-session-item__main">
              <div class="chat-session-item__title">{{ item.title || '新对话' }}</div>
              <div class="chat-session-item__preview">{{ item.last_answer_preview || item.last_question || '暂无内容' }}</div>
            </div>
            <el-button type="text" class="chat-session-item__delete" @click.stop="deleteSession(item.id)">删除</el-button>
          </div>
        </div>

        <div class="chat-sidebar__tips">
          <p>示例问题：</p>
          <ul>
            <li @click="fillQuestion('糖尿病有什么症状？')">糖尿病有什么症状？</li>
            <li @click="fillQuestion('高血压用什么药？')">高血压用什么药？</li>
            <li @click="fillQuestion('糖尿病不能吃什么？')">糖尿病不能吃什么？</li>
            <li @click="fillQuestion('那它有什么并发症？')">那它有什么并发症？</li>
          </ul>
        </div>
      </aside>

      <section class="chat-main">
        <div class="chat-main__header">
          <span>问答工作台</span>
          <div class="chat-main__meta">
            <span v-if="currentRoute">路线：{{ currentRoute }}</span>
            <span v-if="retrievalUsed">已使用图谱检索</span>
            <el-button type="text" @click="goLogin">退出</el-button>
          </div>
        </div>

        <div class="chat-messages" ref="messageBox">
          <div
            v-for="(item, index) in messages"
            :key="index"
            class="chat-message"
            :class="item.role === 'user' ? 'chat-message--user' : 'chat-message--assistant'"
          >
            <div class="chat-message__label">{{ item.role === 'user' ? '你' : '智能体' }}</div>
            <div v-if="item.role === 'user'" class="chat-message__bubble">{{ item.content }}</div>
            <div v-else class="chat-message__bubble chat-message__bubble--markdown" v-html="renderMarkdown(item.content)"></div>
          </div>
        </div>

        <div class="chat-input">
          <el-input
            v-model="question"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="请输入你的医疗知识问题"
            @keyup.enter.native="handleEnter"
          ></el-input>
          <div class="chat-input__actions">
            <el-button @click="createSession">新建对话</el-button>
            <el-button type="primary" :loading="loading" @click="sendMessage">发送</el-button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import DOMPurify from 'dompurify'
import marked from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true
})

export default {
  name: 'Chat',
  data() {
    return {
      username: '',
      userId: '',
      sessionId: null,
      sessionList: [],
      question: '',
      loading: false,
      currentRoute: '',
      retrievalUsed: false,
      messages: []
    }
  },
  methods: {
    goLogin() {
      sessionStorage.removeItem('username')
      this.$router.push('/')
    },
    fillQuestion(text) {
      this.question = text
    },
    handleEnter(e) {
      if (!e.shiftKey) {
        e.preventDefault()
        this.sendMessage()
      }
    },
    renderMarkdown(content) {
      const source = String(content || '')
      const html = marked.parse(source)
      return DOMPurify.sanitize(html)
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const box = this.$refs.messageBox
        if (box) {
          box.scrollTop = box.scrollHeight
        }
      })
    },
    async loadSessions() {
      const res = await this.$axios({
        url: 'history/list',
        method: 'get',
        params: {
          userId: this.userId
        }
      })
      this.sessionList = res.data.data || []
      if (!this.sessionId && this.sessionList.length > 0) {
        await this.selectSession(this.sessionList[0].id)
      }
    },
    async createSession() {
      const res = await this.$axios({
        url: 'chat/createNewChat',
        method: 'post',
        data: {
          userId: this.userId
        }
      })
      const data = res.data.data || {}
      this.sessionId = data.sessionId
      this.messages = []
      this.currentRoute = ''
      this.retrievalUsed = false
      await this.loadSessions()
      this.scrollToBottom()
    },
    async selectSession(id) {
      this.sessionId = id
      const res = await this.$axios({
        url: 'history/detail',
        method: 'get',
        params: {
          sessionId: id
        }
      })
      const data = res.data.data || []
      this.messages = data.map(item => ({
        role: item.role,
        content: item.content
      }))
      this.scrollToBottom()
    },
    async deleteSession(id) {
      await this.$axios({
        url: 'history/delete',
        method: 'delete',
        params: {
          sessionId: id
        }
      })
      if (this.sessionId === id) {
        this.sessionId = null
        this.messages = []
      }
      await this.loadSessions()
      if (!this.sessionList.length) {
        await this.createSession()
      }
    },
    async sendMessage() {
      const value = this.question.trim()
      if (!value) {
        this.$message.warning('请输入问题后再发送')
        return
      }
      if (!this.sessionId) {
        await this.createSession()
      }

      this.messages.push({
        role: 'user',
        content: value
      })
      this.messages.push({
        role: 'assistant',
        content: '正在思考，请稍候...'
      })
      this.loading = true
      this.question = ''
      this.scrollToBottom()

      try {
        const res = await this.$axios({
          url: 'chat/send',
          method: 'post',
          data: {
            sessionId: this.sessionId,
            userId: this.userId,
            message: value
          }
        })
        const data = res.data.data || {}
        this.currentRoute = data.route || ''
        this.retrievalUsed = !!data.retrievalUsed
        this.sessionId = data.sessionId || this.sessionId
        this.messages.pop()
        this.messages.push({
          role: 'assistant',
          content: data.answer || '模型没有输出'
        })
        await this.loadSessions()
        this.scrollToBottom()
      } catch (err) {
        const msg = err && err.message ? err.message : '请求失败'
        this.messages.pop()
        this.messages.push({
          role: 'assistant',
          content: `系统异常：${msg}`
        })
        this.scrollToBottom()
      } finally {
        this.loading = false
      }
    }
  },
  async mounted() {
    this.username = sessionStorage.getItem('username') || '用户'
    this.userId = this.username
    await this.loadSessions()
    if (!this.sessionList.length) {
      await this.createSession()
    }
  }
}
</script>

<style scoped>
.chat-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(91, 141, 239, 0.35), transparent 34%),
    radial-gradient(circle at right, rgba(96, 211, 193, 0.18), transparent 30%),
    linear-gradient(135deg, #07111f 0%, #0d1a2b 42%, #111f34 100%);
  padding: 24px;
}

.chat-page__aurora {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.55;
  pointer-events: none;
}

.chat-page__aurora--one {
  top: -110px;
  left: -80px;
  background: radial-gradient(circle, rgba(104, 129, 255, 0.6) 0%, rgba(104, 129, 255, 0) 72%);
}

.chat-page__aurora--two {
  right: -120px;
  bottom: -140px;
  background: radial-gradient(circle, rgba(79, 228, 202, 0.38) 0%, rgba(79, 228, 202, 0) 70%);
}

.chat-page__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 90%);
  opacity: 0.25;
}

.chat-shell {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 48px);
}

.chat-sidebar,
.chat-main {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(16, 24, 40, 0.82), rgba(11, 19, 32, 0.72));
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(18px);
}

.chat-sidebar {
  display: flex;
  flex-direction: column;
  padding: 28px 24px;
  gap: 18px;
}

.chat-sidebar__badge {
  display: inline-flex;
  align-items: center;
  padding: 7px 12px;
  border: 1px solid rgba(115, 142, 255, 0.28);
  border-radius: 999px;
  background: rgba(109, 136, 255, 0.12);
  color: #c8d7ff;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.chat-sidebar__title {
  margin: 20px 0 10px;
  color: #f6f9ff;
  font-size: 30px;
  line-height: 1.2;
  font-weight: 600;
}

.chat-sidebar__subtitle {
  margin: 0;
  color: rgba(221, 230, 248, 0.72);
  font-size: 14px;
  line-height: 1.8;
}

.chat-sidebar__sessions {
  flex: 1;
  overflow-y: auto;
}

.chat-sidebar__sessions-title {
  margin-bottom: 12px;
  color: #eef4ff;
  font-size: 14px;
  font-weight: 600;
}

.chat-session-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 14px;
  margin-bottom: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.04);
  cursor: pointer;
}

.chat-session-item--active {
  border-color: rgba(118, 149, 255, 0.8);
  box-shadow: 0 0 0 3px rgba(96, 126, 255, 0.12);
}

.chat-session-item__main {
  min-width: 0;
}

.chat-session-item__title {
  color: #f5f8ff;
  font-size: 14px;
  font-weight: 600;
}

.chat-session-item__preview {
  margin-top: 6px;
  color: rgba(214, 224, 245, 0.68);
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.chat-session-item__delete {
  padding: 0;
}

.chat-sidebar__tips {
  color: #dfe8fb;
  font-size: 14px;
}

.chat-sidebar__tips p {
  margin-bottom: 12px;
}

.chat-sidebar__tips ul {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 10px;
}

.chat-sidebar__tips li {
  cursor: pointer;
  color: #a9c2ff;
}

.chat-sidebar__tips li:hover {
  color: #d4e1ff;
}

.chat-main {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chat-main__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  color: #f6f9ff;
  font-size: 16px;
  font-weight: 600;
}

.chat-main__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: rgba(214, 224, 245, 0.72);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-message {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-message--user {
  align-items: flex-end;
}

.chat-message__label {
  color: rgba(214, 224, 245, 0.68);
  font-size: 12px;
}

.chat-message__bubble {
  max-width: 78%;
  padding: 14px 16px;
  border-radius: 18px;
  color: #f5f8ff;
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-message--user .chat-message__bubble {
  background: linear-gradient(135deg, #6e8cff 0%, #7f71ff 45%, #4fd9c4 100%);
  box-shadow: 0 16px 30px rgba(87, 112, 255, 0.25);
}

.chat-message--assistant .chat-message__bubble {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.chat-message__bubble--markdown {
  white-space: normal;
}

.chat-message__bubble--markdown /deep/ p {
  margin: 0 0 12px;
}

.chat-message__bubble--markdown /deep/ p:last-child {
  margin-bottom: 0;
}

.chat-message__bubble--markdown /deep/ h1,
.chat-message__bubble--markdown /deep/ h2,
.chat-message__bubble--markdown /deep/ h3,
.chat-message__bubble--markdown /deep/ h4,
.chat-message__bubble--markdown /deep/ h5,
.chat-message__bubble--markdown /deep/ h6 {
  margin: 0 0 12px;
  color: #ffffff;
  line-height: 1.5;
}

.chat-message__bubble--markdown /deep/ ul,
.chat-message__bubble--markdown /deep/ ol {
  margin: 0 0 12px;
  padding-left: 22px;
}

.chat-message__bubble--markdown /deep/ li + li {
  margin-top: 6px;
}

.chat-message__bubble--markdown /deep/ code {
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.78);
  color: #8de7ff;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 13px;
}

.chat-message__bubble--markdown /deep/ pre {
  margin: 0 0 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(8, 15, 28, 0.92);
  overflow-x: auto;
}

.chat-message__bubble--markdown /deep/ pre code {
  display: block;
  padding: 0;
  background: transparent;
  color: #dff7ff;
  line-height: 1.7;
}

.chat-message__bubble--markdown /deep/ a {
  color: #9fcbff;
  text-decoration: underline;
}

.chat-message__bubble--markdown /deep/ blockquote {
  margin: 0 0 12px;
  padding-left: 12px;
  border-left: 3px solid rgba(159, 203, 255, 0.55);
  color: rgba(235, 243, 255, 0.82);
}

.chat-input {
  padding: 20px 24px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.chat-input /deep/ .el-textarea__inner {
  min-height: 92px !important;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  color: #f6f9ff;
}

.chat-input /deep/ .el-textarea__inner::placeholder {
  color: rgba(205, 216, 236, 0.42);
}

.chat-input /deep/ .el-textarea__inner:focus {
  border-color: rgba(118, 149, 255, 0.8);
  box-shadow: 0 0 0 4px rgba(96, 126, 255, 0.15);
}

.chat-input__actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 14px;
}

@media (max-width: 1024px) {
  .chat-shell {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .chat-page {
    padding: 16px;
  }

  .chat-sidebar,
  .chat-main {
    border-radius: 22px;
  }

  .chat-message__bubble {
    max-width: 100%;
  }
}
</style>
