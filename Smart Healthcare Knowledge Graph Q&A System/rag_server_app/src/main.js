// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import App from './App'
import router from './router'

//element-ui配置
import ElementUI from 'element-ui';
import 'element-ui/lib/theme-chalk/index.css';

Vue.use(ElementUI);

Vue.config.productionTip = false

//引入axios.js
import axios from 'axios'
//配置服务器请求前缀
axios.defaults.baseURL = 'http://127.0.0.1:8000';
// 设置post请求数据格式
axios.defaults.headers.post['Content-Type'] = 'application/json'
// 设置put请求数据格式
axios.defaults.headers.put['Content-Type'] = 'application/json'
// 设置全局 axios 写法
Vue.prototype.$axios = axios

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  components: { App },
  template: '<App/>'
})
