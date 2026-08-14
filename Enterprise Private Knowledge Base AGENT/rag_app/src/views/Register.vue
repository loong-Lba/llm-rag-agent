<template>
  <main id="main-content" class="access-page access-page--register">
    <section class="access-story" aria-labelledby="product-title">
      <div class="brand-mark" aria-hidden="true"><span></span><span></span><span></span><span></span><span></span></div>
      <h1 id="product-title">可视化 RAG 助手：建立你的证据通道。</h1>
      <p class="story-copy">账号用于保存会话、回答与检索来源。创建后将直接进入工作台，从一条真实问题开始观察证据如何汇合。</p>
      <div class="trace-proof" aria-label="系统将保存的内容">
        <div><span>A</span><strong>对话上下文</strong><small>继续未完成的探索</small></div>
        <div><span>B</span><strong>检索轨迹</strong><small>保留阶段与评分</small></div>
        <div><span>C</span><strong>来源证据</strong><small>回到原始片段核查</small></div>
      </div>
      <p class="demo-note"><span aria-hidden="true"></span>当前法律与 MotoGP/675SR 内容仅用于机制演示。</p>
    </section>

    <section class="access-console" aria-labelledby="register-title">
      <h2 id="register-title">注册并创建账号</h2>
      <p class="console-intro">完成注册后会自动登录，并连接到新的工作台会话。</p>

      <form class="access-form" novalidate @submit.prevent="register">
        <div class="signal-field">
          <label for="username">用户名</label>
          <input id="username" ref="username" v-model="user.username" class="signal-input" type="text" autocomplete="username" required :disabled="submitting" :aria-invalid="Boolean(errors.username)" aria-describedby="username-error" @input="errors.username = ''">
          <p v-if="errors.username" id="username-error" class="signal-error-text">{{ errors.username }}</p>
        </div>
        <div class="signal-field">
          <label for="password">密码</label>
          <input id="password" ref="password" v-model="user.password" class="signal-input" type="password" autocomplete="new-password" required :disabled="submitting" :aria-invalid="Boolean(errors.password)" aria-describedby="password-error" @input="errors.password = ''">
          <p v-if="errors.password" id="password-error" class="signal-error-text">{{ errors.password }}</p>
        </div>
        <div class="signal-field">
          <label for="confirmPassword">确认密码</label>
          <input id="confirmPassword" ref="confirmPassword" v-model="confirmPassword" class="signal-input" type="password" autocomplete="new-password" required :disabled="submitting" :aria-invalid="Boolean(errors.confirmPassword)" aria-describedby="confirm-error" @input="errors.confirmPassword = ''">
          <p v-if="errors.confirmPassword" id="confirm-error" class="signal-error-text">{{ errors.confirmPassword }}</p>
        </div>

        <p v-if="formMessage" class="form-message" :class="{ error: formMessageType === 'error' }" role="status" aria-live="polite">{{ formMessage }}</p>
        <button class="signal-button access-submit" type="submit" :disabled="submitting">
          <span v-if="submitting" class="button-pulse" aria-hidden="true"></span>
          {{ submitting ? '正在创建通道' : '创建账号并进入' }}
        </button>
      </form>

      <div class="access-switch">
        <span>已经有账号？</span>
        <button type="button" :disabled="submitting" @click="goLogin">返回登录</button>
      </div>
      <p class="maker">Made by LBA</p>
    </section>
  </main>
</template>

<script>
export default {
  name: 'Register',
  data() {
    return {
      user: { username: '', password: '' },
      confirmPassword: '',
      errors: { username: '', password: '', confirmPassword: '' },
      submitting: false,
      formMessage: '',
      formMessageType: '',
      navigationTimer: null
    }
  },
  methods: {
    validate() {
      const username = this.user.username.trim()
      const password = this.user.password.trim()
      const confirmation = this.confirmPassword.trim()
      this.errors.username = username ? '' : '请输入用户名。'
      this.errors.password = password ? '' : '请输入密码。'
      this.errors.confirmPassword = !confirmation ? '请再次输入密码。' : (password !== confirmation ? '两次输入的密码不一致。' : '')
      if (this.errors.username) this.$refs.username.focus()
      else if (this.errors.password) this.$refs.password.focus()
      else if (this.errors.confirmPassword) this.$refs.confirmPassword.focus()
      return !this.errors.username && !this.errors.password && !this.errors.confirmPassword
    },
    register() {
      if (this.submitting || !this.validate()) return
      const username = this.user.username.trim()
      const password = this.user.password.trim()
      this.submitting = true
      this.formMessage = '正在创建账号…'
      this.formMessageType = ''

      this.$axios({
        url: this.$serverUrlBase + 'users/register',
        method: 'post',
        data: JSON.stringify({ username: username, password: password })
      }).then(res => {
        if (res.data.code !== 200 || res.data.data === undefined || res.data.data === null) {
          this.formMessage = res.data.msg || '注册失败，请修改信息后重试。'
          this.formMessageType = 'error'
          return
        }
        sessionStorage.setItem('userId', res.data.data)
        sessionStorage.setItem('username', username)
        this.user.password = ''
        this.confirmPassword = ''
        this.formMessage = res.data.msg || '注册成功，正在进入工作台。'
        this.navigationTimer = setTimeout(() => this.$router.push('/goChat'), 500)
      }).catch(() => {
        this.formMessage = '无法连接注册服务，请确认后端已启动后重试。'
        this.formMessageType = 'error'
      }).then(() => {
        this.submitting = false
      })
    },
    goLogin() { this.$router.push('/') }
  },
  beforeDestroy() {
    if (this.navigationTimer) clearTimeout(this.navigationTimer)
  }
}
</script>

<style scoped>
.access-page { min-height: 100vh; display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(410px, .85fr); background: var(--signal-canvas); }
.access-story { min-width: 0; padding: clamp(38px, 7vw, 108px); display: flex; flex-direction: column; justify-content: center; color: #f4f7f6; background-color: #15201e; background-image: repeating-linear-gradient(0deg, transparent 0, transparent 31px, rgba(117,152,145,.07) 31px, rgba(117,152,145,.07) 32px); }
.brand-mark { width: 152px; height: 28px; margin-bottom: 54px; display: flex; align-items: center; gap: 7px; }
.brand-mark span { width: 22px; height: 2px; background: #86a39e; }
.brand-mark span:nth-child(2), .brand-mark span:nth-child(3), .brand-mark span:nth-child(4) { height: 8px; background: #50c7b5; }
.brand-mark span:nth-child(3) { height: 20px; }
h1 { max-width: 780px; margin: 0; color: #fff; font-size: clamp(40px, 5.6vw, 76px); line-height: 1.05; letter-spacing: -.04em; }
.story-copy { max-width: 650px; margin: 30px 0 50px; color: #c1cfcc; font-size: clamp(17px, 1.5vw, 20px); line-height: 1.8; }
.trace-proof { max-width: 760px; display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid #50635f; border-bottom: 1px solid #50635f; }
.trace-proof div { padding: 22px 20px 22px 0; display: grid; gap: 7px; }
.trace-proof span, .trace-proof small { color: #91a5a1; font-family: var(--signal-data-font); font-size: 11px; }
.trace-proof strong { font-size: 15px; }
.demo-note { margin: 34px 0 0; display: flex; align-items: center; gap: 10px; color: #91a5a1; font-size: 13px; }
.demo-note span { width: 8px; height: 8px; border: 1px solid #eaa543; }
.access-console { min-width: 0; padding: clamp(32px, 5.6vw, 76px); display: flex; flex-direction: column; justify-content: center; background: var(--signal-surface); box-shadow: -18px 0 46px rgba(0,0,0,.12); }
h2 { margin: 0 0 12px; font-size: clamp(30px, 3vw, 44px); letter-spacing: -.035em; }
.console-intro { max-width: 43ch; margin: 0 0 30px; color: var(--signal-muted); line-height: 1.7; }
.access-form { display: grid; gap: 17px; }
.form-message { margin: -2px 0 0; color: var(--signal-active-strong); font-size: 14px; line-height: 1.5; }
.form-message.error { color: var(--signal-error); }
.access-submit { width: 100%; margin-top: 6px; display: flex; justify-content: center; align-items: center; gap: 10px; }
.button-pulse { width: 8px; height: 8px; background: #8be3d5; animation: pulse 900ms ease-out infinite alternate; }
.access-switch { margin-top: 24px; padding-top: 20px; display: flex; justify-content: space-between; gap: 14px; color: var(--signal-muted); border-top: 1px solid var(--signal-line); font-size: 14px; }
.access-switch button { border: 0; padding: 0; color: var(--signal-active-strong); background: transparent; font-weight: 700; text-decoration: underline; text-underline-offset: 4px; cursor: pointer; }
.maker { margin: 42px 0 0; color: var(--signal-faint); font-family: var(--signal-data-font); font-size: 11px; letter-spacing: .08em; }
@keyframes pulse { to { opacity: .35; } }
@media (max-width: 900px) { .access-page { grid-template-columns: 1fr; } .access-story { padding-bottom: 44px; } .brand-mark { margin-bottom: 32px; } .access-console { box-shadow: 0 -18px 46px rgba(0,0,0,.1); } }
@media (max-width: 620px) { .access-story, .access-console { padding: 28px 20px; } .trace-proof { grid-template-columns: 1fr; } .trace-proof div { grid-template-columns: 28px 1fr; padding: 14px 0; } .trace-proof small { grid-column: 2; } .story-copy { font-size: 16px; } .console-status { margin-bottom: 26px; } }
</style>
