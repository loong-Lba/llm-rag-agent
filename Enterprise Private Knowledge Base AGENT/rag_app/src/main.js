// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'

Vue.config.productionTip = false

//引入element-ui
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';
Vue.use(ElementUI);

//引入axios.js
import axios from 'axios'
//配置服务器请求前缀
axios.defaults.baseURL = '';
// 配置cookie,session跨域配置
axios.defaults.withCredentials=true;
// 设置post请求数据格式
axios.defaults.headers.post['Content-Type'] = 'application/json'
// 设置put请求数据格式
axios.defaults.headers.put['Content-Type'] = 'application/json'
// 设置全局 axios 写法
Vue.prototype.$axios = axios

//配置服务器的请求路径公共部分
Vue.prototype.$serverUrlBase = 'http://localhost:8001/';

//markdown解析
import marked from 'marked'
import DOMPurify from 'dompurify'
// marked 基础配置
marked.setOptions({
  breaks: true,    // 支持换行
  gfm: true,       // GitHub 风格
  smartLists: true,
  smartypants: false
})
function normalizeMarkdown(text) {
  return text
    .replace(/(#{1,6} )/g, '\n$1')
    .replace(/- /g, '\n- ')
}
// 全局 markdown 渲染方法
Vue.prototype.$renderMarkdown = function (text) {
  if (!text) return ''
  const rawHtml = marked(normalizeMarkdown(text))
  return DOMPurify.sanitize(rawHtml)
}



// 导航钩子 ---- 未登录拦截
// to：去哪里
// from：从哪里来
// next：放行
router.beforeEach((to, from, next) => {
  // 取出登录用户名
  let username = sessionStorage.getItem('username')
  // 判断是否需要拦截
  if (to.meta.isLogin) {
    // 需要拦截 --- 判断是否登陆了，登陆了则放行，否则拦截
    if (username) {
      next();
    } else {
      // 回到登录页面
      alert('请先登录！');
      next('/');
    }
  }else {
    // 不拦截 ---放行
    next();
    }
});
/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
