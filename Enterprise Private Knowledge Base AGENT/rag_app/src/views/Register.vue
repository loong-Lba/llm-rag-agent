<template>
  <div class="register-container">
    <div class="register-card">
      <h2 class="register-title">欢迎注册</h2>

      <form class="register-form" @submit.prevent="register">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            type="text"
            placeholder="请输入用户名"
            v-model="user.username"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            type="password"
            placeholder="请输入密码"
            v-model="user.password"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            v-model="confirmPassword"
            class="form-input"
          />
        </div>

        <button type="button" @click="register" class="register-submit-btn">确 认 注 册</button>
      </form>

      <div class="back-login-entry">
        <button type="button" class="back-login-btn" @click="goLogin">返回登录</button>
      </div>

      <p class="register-footer">Made by LBA</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "Register",
  data() {
    return {
      $serverUrlBase: this.$serverUrlBase,
      user: {
        username: '',
        password: '',
      },
      confirmPassword: '',
    }
  },
  methods: {
    register() {
      let username = this.user.username ? this.user.username.trim() : '';
      let password = this.user.password ? this.user.password.trim() : '';
      let confirmPassword = this.confirmPassword ? this.confirmPassword.trim() : '';

      if (!username) {
        this.$message.warning('请输入用户名');
        return;
      }

      if (!password) {
        this.$message.warning('请输入密码');
        return;
      }

      if (!confirmPassword) {
        this.$message.warning('请输入确认密码');
        return;
      }

      if (password !== confirmPassword) {
        this.$message.warning('两次输入的密码不一致');
        return;
      }

      this.$axios({
        url: this.$serverUrlBase + 'users/register',
        method: 'post',
        data: JSON.stringify({
          username: username,
          password: password,
        }),
      }).then(res => {
        if (res.data.code === 200) {
          this.$message.success(res.data.msg);
          sessionStorage.setItem('userId', res.data.data);
          sessionStorage.setItem('username', username);
          setTimeout(() => {
            this.$router.push('/goChat');
          }, 1000);
        } else {
          this.$message.error(res.data.msg);
        }
      })
    },

    goLogin() {
      this.$router.push('/');
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #0b0b0b;
  font-family: 'Segoe UI', Roboto, system-ui, -apple-system, sans-serif;
  padding: 1rem;
  box-sizing: border-box;
  background-image: radial-gradient(circle at 20% 30%, rgba(212, 175, 55, 0.04) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(212, 175, 55, 0.03) 0%, transparent 50%);
}

.register-card {
  background: #1a1a1a;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-radius: 40px;
  padding: 2.8rem 2.8rem 2.2rem;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8),
              0 0 0 1px rgba(212, 175, 55, 0.25),
              inset 0 0 0 1px rgba(212, 175, 55, 0.08);
  transition: transform 0.25s ease, box-shadow 0.3s ease;
  border: 1px solid rgba(212, 175, 55, 0.15);
}

.register-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 40px 70px -18px #000000cc,
              0 0 0 1.5px rgba(212, 175, 55, 0.35),
              inset 0 0 0 1px rgba(212, 175, 55, 0.12);
}

.register-title {
  text-align: center;
  font-weight: 700;
  font-size: 3.2rem;
  letter-spacing: 1.5px;
  color: #f5f0eb;
  margin-top: 0.2rem;
  margin-bottom: 2.4rem;
  display: block;
  width: 100%;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
  background: linear-gradient(135deg, #f5f0eb 0%, #d4af37 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 1.7rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #c0b7a8;
  letter-spacing: 0.8px;
  margin-left: 6px;
  text-transform: uppercase;
  font-size: 0.75rem;
  opacity: 0.9;
}

.form-input {
  padding: 0.9rem 1.2rem;
  border: 1.5px solid #3a3a3a;
  border-radius: 60px;
  font-size: 1rem;
  transition: all 0.25s ease;
  background: #0f0f0f;
  color: #f0ece6;
  outline: none;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6);
}

.form-input:focus {
  border-color: #d4af37;
  box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.15), inset 0 2px 6px rgba(0, 0, 0, 0.6);
  background: #141414;
}

.form-input::placeholder {
  color: #6b6258;
  font-weight: 300;
  font-size: 0.95rem;
  letter-spacing: 0.3px;
}

.register-submit-btn {
  margin-top: 0.8rem;
  padding: 1rem 1rem;
  background: linear-gradient(145deg, #d4af37, #b8962e);
  color: #0b0b0b;
  font-weight: 700;
  font-size: 1.1rem;
  border: none;
  border-radius: 60px;
  cursor: pointer;
  transition: all 0.25s ease;
  letter-spacing: 2px;
  box-shadow: 0 8px 24px -6px rgba(212, 175, 55, 0.25), inset 0 1px 0 rgba(255, 215, 100, 0.6);
  text-transform: uppercase;
}

.register-submit-btn:hover {
  background: linear-gradient(145deg, #e0c04a, #c8a132);
  transform: scale(1.01);
  box-shadow: 0 12px 32px -8px rgba(212, 175, 55, 0.45), inset 0 1px 0 rgba(255, 225, 120, 0.7);
}

.back-login-entry {
  display: flex;
  justify-content: flex-end;
  margin-top: 1rem;
}

.back-login-btn {
  background: transparent;
  border: none;
  color: #d4af37;
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0.3rem 0.5rem;
  transition: all 0.2s ease;
}

.back-login-btn:hover {
  color: #f5f0eb;
  text-decoration: underline;
}

.register-footer {
  text-align: center;
  margin-top: 2.2rem;
  font-size: 0.75rem;
  color: #6b6258;
  letter-spacing: 1.5px;
  opacity: 0.7;
  border-top: 1px solid rgba(212, 175, 55, 0.08);
  padding-top: 1.2rem;
}

@media (max-width: 480px) {
  .register-card {
    padding: 2rem 1.5rem 1.8rem;
  }
  .register-title {
    font-size: 2.4rem;
  }
  .form-input {
    padding: 0.8rem 1rem;
  }
  .register-submit-btn {
    padding: 0.9rem 0.8rem;
    font-size: 1rem;
  }
}
</style>
