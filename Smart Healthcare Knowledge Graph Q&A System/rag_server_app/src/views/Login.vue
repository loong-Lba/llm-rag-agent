<template>
  <div class="login-page">
    <div class="login-page__aurora login-page__aurora--one"></div>
    <div class="login-page__aurora login-page__aurora--two"></div>
    <div class="login-page__grid"></div>

    <div class="login-card">
      <div class="login-card__badge">RAG Assistant</div>
      <h1 class="login-card__title">欢迎登录</h1>
      <p class="login-card__subtitle">邮箱验证码登录，快速进入智能对话工作台。</p>

      <form class="login-form">
        <div class="login-form__group">
          <label class="login-form__label">用户名</label>
          <el-input
            v-model="username"
            placeholder="请输入用户名"
            :disabled="isSend"
            class="login-input"
          ></el-input>
        </div>

        <transition name="fade-slide">
          <div v-show="isSend" class="login-form__group">
            <div class="login-form__row">
              <label class="login-form__label">验证码</label>
              <button
                type="button"
                class="login-form__ghost"
                @click="sendEmail"
                :disabled="countdown > 0"
              >
                {{ countdown > 0 ? `${countdown}s 后可重发` : '重新发送' }}
              </button>
            </div>
            <el-input
              v-model="code"
              placeholder="请输入验证码"
              class="login-input"
            ></el-input>
            <p class="login-form__hint">验证码已发送，请前往邮箱查收并在 60 秒内完成验证。</p>
          </div>
        </transition>

        <el-button
          v-show="!isSend"
          type="primary"
          class="login-button login-button--primary"
          @click="sendEmail"
        >
          发送验证码
        </el-button>

        <el-button
          v-show="isSend"
          type="primary"
          class="login-button login-button--primary"
          @click="verifyCode"
        >
          验证验证码
        </el-button>
      </form>
    </div>
  </div>
</template>

<script>
export default {
  name: "Login",
  data() {
    return {
      username: 'cc', //用户名
      receiver: '', //收件方邮箱号
      code: '', //验证码
      isSend: false, // 是否发送验证码---用于控制师傅显示验证码框，是否禁用发送按钮，禁用用户名输入
      countdown: 0,
      timer: null,
    }
  },
  methods: {
    startCountdown() {
      this.clearCountdown();
      this.countdown = 60;
      this.timer = setInterval(() => {
        if (this.countdown > 0) {
          this.countdown -= 1;
          return;
        }
        this.clearCountdown();
      }, 1000);
    },
    clearCountdown() {
      if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
      }
    },
    sendEmail(){ //发送验证码
      this.$axios({
        url: 'users/sendEmail', //请求地址---fastapi接口
        method:'get', // 请求方式
        params:{ //请求参数、key必须和fastapi接口函数的参数一致
          username: this.username,
        }
      }).then(res =>{//接收服务器返回的数据，res是形参、res.data是返回的数据
        let code = String(res.data.code);
        let data = res.data.data;
        let msg = res.data.msg;
        if (code === '200'){
          this.isSend = true;
          this.startCountdown();
          this.$message.success(msg || '发送成功！');
          this.receiver = data || this.receiver;
        }else {
          this.isSend = false;
          this.clearCountdown();
          this.$message.error(msg || '发送失败！');
        }
      }).catch(() => {
        this.isSend = false;
        this.clearCountdown();
        this.$message.error('发送失败！');
      })
    },
    verifyCode(){ //验证验证码
      this.$axios({
        url: 'users/verifyCode',
        params:{
          receiver: this.receiver, //接收方邮箱号
          code: this.code //验证码
        }
      }).then(res =>{
        if (String(res.data.code) === '200') {
          this.$message.success(res.data.msg || '登录成功！');
          sessionStorage.setItem('username', this.username)
          setTimeout(() =>{
            this.$router.push('/chat');
          },1500);
        }else {
          this.$message.error(res.data.msg || '登录失败！');
        }
      }).catch(() => {
        this.$message.error('登录失败！');
      })

    },

  },
  mounted() {

  },
  beforeDestroy() {
    this.clearCountdown();
  },
}
</script>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(91, 141, 239, 0.35), transparent 34%),
    radial-gradient(circle at right, rgba(96, 211, 193, 0.18), transparent 30%),
    linear-gradient(135deg, #07111f 0%, #0d1a2b 42%, #111f34 100%);
  padding: 24px;
}

.login-page__aurora {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.55;
  pointer-events: none;
}

.login-page__aurora--one {
  top: -110px;
  left: -80px;
  background: radial-gradient(circle, rgba(104, 129, 255, 0.6) 0%, rgba(104, 129, 255, 0) 72%);
}

.login-page__aurora--two {
  right: -120px;
  bottom: -140px;
  background: radial-gradient(circle, rgba(79, 228, 202, 0.38) 0%, rgba(79, 228, 202, 0) 70%);
}

.login-page__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.55), transparent 90%);
  opacity: 0.25;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 460px;
  padding: 36px 32px 30px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(16, 24, 40, 0.82), rgba(11, 19, 32, 0.72));
  box-shadow:
    0 30px 80px rgba(0, 0, 0, 0.38),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(18px);
}

.login-card__badge {
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

.login-card__title {
  margin: 20px 0 10px;
  color: #f6f9ff;
  font-size: 32px;
  line-height: 1.15;
  font-weight: 600;
}

.login-card__subtitle {
  margin: 0 0 30px;
  color: rgba(221, 230, 248, 0.72);
  font-size: 14px;
  line-height: 1.7;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.login-form__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.login-form__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.login-form__label {
  color: #eef4ff;
  font-size: 14px;
  font-weight: 500;
}

.login-form__ghost {
  padding: 0;
  border: 0;
  background: transparent;
  color: #8fb4ff;
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s ease, opacity 0.2s ease;
}

.login-form__ghost:hover {
  color: #b9d2ff;
}

.login-form__ghost:disabled {
  cursor: not-allowed;
  color: rgba(194, 208, 233, 0.45);
}

.login-form__hint {
  margin: 2px 0 0;
  color: rgba(207, 218, 239, 0.62);
  font-size: 12px;
  line-height: 1.6;
}

.login-input /deep/ .el-input__inner {
  height: 50px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  color: #f6f9ff;
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.03);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.login-input /deep/ .el-input__inner::placeholder {
  color: rgba(205, 216, 236, 0.42);
}

.login-input /deep/ .el-input__inner:focus {
  border-color: rgba(118, 149, 255, 0.8);
  background: rgba(255, 255, 255, 0.09);
  box-shadow:
    0 0 0 4px rgba(96, 126, 255, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.05);
}

.login-input /deep/ .el-input.is-disabled .el-input__inner {
  color: rgba(239, 244, 255, 0.7);
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.08);
}

.login-button {
  width: 100%;
  height: 52px;
  margin: 6px 0 0;
  border: 0;
  border-radius: 16px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.login-button--primary {
  background: linear-gradient(135deg, #6e8cff 0%, #7f71ff 45%, #4fd9c4 100%);
  box-shadow: 0 16px 30px rgba(87, 112, 255, 0.35);
}

.login-button--primary:hover,
.login-button--primary:focus {
  background: linear-gradient(135deg, #7d98ff 0%, #8d7fff 42%, #61e0cc 100%);
  box-shadow: 0 20px 34px rgba(87, 112, 255, 0.42);
  transform: translateY(-1px);
}

.login-button--primary:active {
  transform: translateY(0);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-slide-enter,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 640px) {
  .login-page {
    padding: 16px;
  }

  .login-card {
    padding: 28px 20px 24px;
    border-radius: 24px;
  }

  .login-card__title {
    font-size: 28px;
  }

  .login-form__row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
