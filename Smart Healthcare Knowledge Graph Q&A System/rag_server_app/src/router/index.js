import Vue from 'vue'
import Router from 'vue-router'


Vue.use(Router)

export default new Router({
  mode: 'history', // 配置路由的模式
  routes: [
    // Login.vue
    {
      path: '/',
      component: () => import('@/views/Login.vue')
    },
    // Chat.vue
    {
      path: '/chat',
      component: () => import('@/views/Chat.vue')
    }
  ]
})
