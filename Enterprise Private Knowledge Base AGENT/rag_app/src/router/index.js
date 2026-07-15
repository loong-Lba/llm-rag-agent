import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  //设置路由模式为history
  mode:'history',
  routes: [
    //Login.vue 路由
    {
      //访问路由 ---需要拼接在客户端的协议、IP、端口号后面构成完整请求路径
      path: '/',
      meta:{
        isLogin: false, //不拦截
      },
      // 通过path属性的路径访问到的页面
      component: () => import('@/views/Login.vue')
    },
    //goChat路由
    {
      path: '/register',
      meta: {
        isLogin: false,
      },
      component: () => import('@/views/Register.vue')
    },

    //chat.vue路由
    {
      path:'/goChat',
      //设置这个路由访问需要拦截
      meta:{
        isLogin:true, //登录拦截
      },
      component:() =>import('@/views/Chat.vue')
    },
  ]
})
