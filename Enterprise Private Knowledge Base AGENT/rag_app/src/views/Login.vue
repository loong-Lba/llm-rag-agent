<template>
  <main id="main-content" class="access-page">
    <section class="access-story" aria-labelledby="product-title">
      <div class="brand-mark" aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span>
      </div>
      <h1 id="product-title">可视化 RAG 助手：看见答案如何抵达。</h1>
      <p class="story-copy">进入工作台，沿着检索信号核查每条回答。不是只看结果，而是检查向量召回、关键词匹配、融合、重排与最终证据。</p>

      <ol class="access-signal" aria-label="RAG 证据链">
        <li><span>01</span><strong>向量</strong><small>语义召回</small></li>
        <li><span>02</span><strong>BM25</strong><small>词项匹配</small></li>
        <li><span>03</span><strong>RRF</strong><small>候选融合</small></li>
        <li><span>04</span><strong>重排</strong><small>相关性校准</small></li>
        <li><span>05</span><strong>回答</strong><small>来源可核查</small></li>
      </ol>
      <p class="demo-note"><span aria-hidden="true"></span>当前知识库为机制演示数据，不代表固定业务领域。</p>
    </section>

    <section class="access-console" aria-labelledby="login-title">
      <h2 id="login-title">登录，连接你的工作台</h2>
      <p class="console-intro">登录后可继续历史对话并保存每次检索的证据链。</p>

      <p v-if="loginRequired" class="access-notice" role="status">请先登录，再进入 RAG 工作台。</p>

      <form class="access-form" novalidate @submit.prevent="login">
        <div class="signal-field">
          <label for="username">账号</label>
          <input
            id="username"
            ref="username"
            v-model="user.username"
            class="signal-input"
            type="text"
            autocomplete="username"
            required
            :aria-invalid="Boolean(errors.username)"
            aria-describedby="username-error"
            :disabled="submitting"
            @input="errors.username = ''"
          />
          <p v-if="errors.username" id="username-error" class="signal-error-text">{{ errors.username }}</p>
        </div>

        <div class="signal-field">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="user.password"
            class="signal-input"
            type="password"
            autocomplete="current-password"
            required
            :aria-invalid="Boolean(errors.password)"
            aria-describedby="password-error"
            :disabled="submitting"
            @input="errors.password = ''"
          />
          <p v-if="errors.password" id="password-error" class="signal-error-text">{{ errors.password }}</p>
        </div>

        <p v-if="formMessage" class="form-message" :class="{ error: formMessageType === 'error' }" role="status" aria-live="polite">
          {{ formMessage }}
        </p>

        <button class="signal-button access-submit" type="submit" :disabled="submitting">
          <span v-if="submitting" class="button-pulse" aria-hidden="true"></span>
          {{ submitting ? '正在验证身份' : '登录并进入工作台' }}
        </button>
      </form>

      <div class="access-switch">
        <span>还没有账号？</span>
        <button type="button" :disabled="submitting" @click="goRegister">创建账号</button>
      </div>
      <p class="maker">Made by LBA</p>
    </section>
  </main>
</template>

<script>
export default {
  name: 'Login',
  data() {
    return {
      user: { username: '', password: '' },
      errors: { username: '', password: '' },
      submitting: false,
      formMessage: '',
      formMessageType: '',
      navigationTimer: null
    }
  },
  computed: {
    loginRequired() {
      return this.$route.query.reason === 'login-required'
    }
  },
  methods: {
    validate() {
      this.errors.username = this.user.username.trim() ? '' : '请输入账号。'
      this.errors.password = this.user.password ? '' : '请输入密码。'
      if (this.errors.username && this.$refs.username) this.$refs.username.focus()
      return !this.errors.username && !this.errors.password
    },
    login() {
      if (this.submitting || !this.validate()) return
      this.submitting = true
      this.formMessage = '正在连接身份服务…'
      this.formMessageType = ''

      this.$axios({
        url: this.$serverUrlBase + 'users/login',
        method: 'post',
        data: JSON.stringify({
          username: this.user.username.trim(),
          password: this.user.password
        })
      }).then(res => {
        if (res.data.code !== 200 || res.data.data === undefined || res.data.data === null) {
          this.formMessage = res.data.msg || '登录失败，请检查账号和密码。'
          this.formMessageType = 'error'
          return
        }
        sessionStorage.setItem('userId', res.data.data)
        sessionStorage.setItem('username', this.user.username.trim())
        this.user.password = ''
        this.formMessage = res.data.msg || '登录成功，正在进入工作台。'
        this.navigationTimer = setTimeout(() => this.$router.push('/goChat'), 500)
      }).catch(() => {
        this.formMessage = '无法连接登录服务，请确认后端已启动后重试。'
        this.formMessageType = 'error'
      }).then(() => {
        this.submitting = false
      })
    },
    goRegister() {
      this.$router.push('/register')
    }
  },
  beforeDestroy() {
    if (this.navigationTimer) clearTimeout(this.navigationTimer)
  }
}
</script>

<style scoped>
.access-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(380px, .75fr);
  background: var(--signal-canvas);
}
.access-story {
  min-width: 0;
  padding: clamp(38px, 7vw, 108px);
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: var(--signal-dark);
  background-image: repeating-linear-gradient(0deg, transparent 0, transparent 31px, rgba(117, 152, 145, .07) 31px, rgba(117, 152, 145, .07) 32px);
  color: #f4f7f6;
}
.brand-mark { width: 152px; height: 28px; display: flex; align-items: center; gap: 7px; margin-bottom: 54px; }
.brand-mark span { width: 22px; height: 2px; background: #86a39e; }
.brand-mark span:nth-child(2), .brand-mark span:nth-child(3), .brand-mark span:nth-child(4) { height: 8px; background: #50c7b5; }
.brand-mark span:nth-child(3) { height: 20px; }
h1 { max-width: 760px; margin: 0; color: #fff; font-size: clamp(42px, 6vw, 84px); line-height: 1.04; letter-spacing: -.04em; }
.story-copy { max-width: 660px; margin: 30px 0 58px; color: #c1cfcc; font-size: clamp(17px, 1.6vw, 21px); line-height: 1.8; }
.access-signal { max-width: 850px; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(92px, 1fr)); list-style: none; border-top: 1px solid #50635f; }
.access-signal li { position: relative; padding: 22px 14px 16px 0; display: grid; gap: 7px; }
.access-signal li::before { content: ''; position: absolute; top: -5px; left: 0; width: 9px; height: 9px; border: 2px solid var(--signal-dark); background: #50c7b5; }
.access-signal span, .access-signal small { color: #8ca19d; font-family: var(--signal-data-font); font-size: 11px; }
.access-signal strong { font-size: 15px; }
.demo-note { margin: 38px 0 0; display: flex; align-items: center; gap: 10px; color: #91a5a1; font-size: 13px; }
.demo-note span { width: 8px; height: 8px; border: 1px solid #eaa543; background: transparent; }
.access-console { min-width: 0; padding: clamp(32px, 6vw, 82px); display: flex; flex-direction: column; justify-content: center; background: var(--signal-surface); box-shadow: -18px 0 46px rgba(0, 0, 0, .12); }
h2 { margin: 0 0 12px; font-size: clamp(30px, 3vw, 44px); letter-spacing: -.035em; }
.console-intro { max-width: 43ch; margin: 0 0 34px; color: var(--signal-muted); line-height: 1.7; }
.access-notice { margin: 0 0 22px; padding: 12px 14px; color: #704200; background: var(--signal-progress-soft); border: 1px solid #d39a43; font-size: 14px; }
.access-form { display: grid; gap: 22px; }
.form-message { margin: -4px 0 0; color: var(--signal-active-strong); font-size: 14px; line-height: 1.5; }
.form-message.error { color: var(--signal-error); }
.access-submit { width: 100%; margin-top: 8px; display: flex; justify-content: center; align-items: center; gap: 10px; }
.button-pulse { width: 8px; height: 8px; background: #8be3d5; animation: pulse 900ms ease-out infinite alternate; }
.access-switch { margin-top: 28px; padding-top: 22px; display: flex; justify-content: space-between; gap: 14px; color: var(--signal-muted); border-top: 1px solid var(--signal-line); font-size: 14px; }
.access-switch button { border: 0; padding: 0; color: var(--signal-active-strong); background: transparent; font-weight: 700; text-decoration: underline; text-underline-offset: 4px; cursor: pointer; }
.maker { margin: 62px 0 0; color: var(--signal-faint); font-family: var(--signal-data-font); font-size: 11px; letter-spacing: .08em; }
@keyframes pulse { to { opacity: .35; } }
@media (max-width: 900px) {
  .access-page { grid-template-columns: 1fr; }
  .access-story { min-height: auto; padding-bottom: 44px; }
  .brand-mark { margin-bottom: 32px; }
  .story-copy { margin-bottom: 34px; }
  .access-console { box-shadow: 0 -18px 46px rgba(0, 0, 0, .1); }
}
@media (max-width: 620px) {
  .access-page { width: 100vw; max-width: 100vw; overflow-x: hidden; }
  .access-story, .access-console { width: 100vw; min-width: 0; max-width: 100vw; padding: 28px 20px; overflow-x: hidden; }
  .access-story > * { max-width: 100%; }
  .access-story { overflow: hidden; }
  h1 { width: 100%; font-size: clamp(36px, 11vw, 48px); overflow-wrap: anywhere; word-break: break-all; }
  .access-signal { width: 100%; grid-template-columns: repeat(5, minmax(0, 1fr)); padding-bottom: 8px; }
  .access-signal li { min-width: 0; padding-right: 4px; }
  .access-signal strong { font-size: 13px; }
  .access-signal small { font-size: 9px; }
  .story-copy { width: 100%; max-width: 100%; font-size: 16px; overflow-wrap: anywhere; word-break: break-all; }
  .maker { margin-top: 40px; }
}
</style>
