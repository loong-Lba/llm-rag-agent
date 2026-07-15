<template>
  <div class="chat-layout">
    <!-- ==================== 左侧历史记录面板 ==================== -->
    <div class="history-panel" :class="{ collapsed: isHistoryCollapsed }">
      <!-- 面板头部 -->
      <div class="history-header">
        <div class="header-title">
          <span class="icon">📋</span>
          <span v-show="!isHistoryCollapsed" class="title-text">历史对话</span>
        </div>
        <button class="collapse-btn" @click="isHistoryCollapsed = !isHistoryCollapsed">
          {{ isHistoryCollapsed ? '▶' : '◀' }}
        </button>
      </div>

      <!-- 新建对话按钮 -->
      <div class="history-actions" v-show="!isHistoryCollapsed">
        <button class="new-chat-btn" @click="createNewChat">
          <span class="plus-icon">＋</span> 新建对话
        </button>
      </div>

      <!-- 历史记录列表 -->
      <div class="history-list" ref="historyList">
        <!-- 空状态 -->
        <div v-if="historyList.length === 0" class="empty-history">
          <span class="empty-icon">💬</span>
          <span class="empty-text">暂无历史记录</span>
          <span class="empty-hint">点击上方「新建对话」开始聊天</span>
        </div>

        <!-- 历史记录项 -->
        <div
          v-for="item in historyList"
          :key="item.historyId"
          class="history-item"
        >
          <!-- 对话标题 -->
          <div class="history-item-content">
            <span class="item-icon">{{ item.type === 'law' ? '🏍️' : '💬' }}</span>
            <div class="item-info">
              <div class="history-title" @click="loadHistoryById(item.historyId)">{{ item.question || '新对话' }}</div>
              <div class="history-meta">
                <span class="history-time">{{ item.createTime }}</span>
              </div>
            </div>
          </div>
          <!-- 操作按钮（悬停显示） -->
          <div class="item-actions">
            <button class="action-btn delete-btn" @click.stop="deleteHistory(item.historyId)" title="删除">
              <span>✕</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== 右侧聊天区域 ==================== -->
    <div class="chat-container">
      <div class="chat-card">
        <!-- 聊天头部 -->
        <div class="chat-header">
          <div class="header-left">
            <h2>💬 AI 智能助手</h2>
            <span class="current-session" v-if="currentSessionTitle">
              {{ currentSessionTitle }}
            </span>
          </div>
          <div class="header-right">
            <span class="status online">● 在线</span>
          </div>
        </div>

        <!-- 消息区域 -->
        <div class="chat-body" ref="chatBody">
          <div
            v-for="(item, index) in messages"
            :key="index"
            class="message-wrapper"
            :class="item.role === 'user' ? 'user-message' : 'assistant-message'"
          >
            <div class="message-avatar">
              {{ item.role === 'user' ? '👤' : '🤖' }}
            </div>
            <div class="message-content">
              <div class="message-role">
                {{ item.role === 'user' ? '我' : item.role === 'system' ? '系统' : 'AI' }}
              </div>
              <div class="message-text" v-html="$renderMarkdown(item.content)"></div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-footer">
          <input
            type="text"
            placeholder="请输入您的问题..."
            v-model="question"
            class="chat-input"
            @keyup.enter="chat"
          />
          <button type="button" @click="chat" class="chat-btn">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Chat",
  data() {
    return {
      // ========== 聊天相关 ==========
      question: null,   //用户输入的问题
      loading: false,   //是否正在加载ai回复
      messages: [],  //聊天消息列表

      // ========== 历史记录相关 ==========
      isHistoryCollapsed: false,           // 面板是否折叠
      currentSessionId: null,         // 当前会话ID
      currentSessionTitle: '新对话',     // 当前会话标题
      historyList: [],   //历史记录列表
      openHistoryId: 0, // 打开对话记录的时候的historyId
      isNewChat: false,
      userId: null,

    }
  },
  methods: {
    // ========== 滚动到底部 ==========
    scrollToBottom() {
      this.$nextTick(() => {
        const chatBody = this.$refs.chatBody;
        if (chatBody) {
          chatBody.scrollTop = chatBody.scrollHeight;
        }
      });

    },
    //获取历史记录
    history_List(){
      this.$axios({
        url: this.$serverUrlBase + 'history/list',    //请求历史记录列表接口
        method:'get',
        params:{
          userId: this.userId   //传递当前用户ID
        }
      }).then(res => {
        this.historyList = res.data.data;   //将返回的数据复制给历史列表

      })
    },
    loadHistoryById(historyId) {    //通过history_id加载历史
      console.log(historyId)
      this.openHistoryId = historyId;
      this.$axios({
        url: this.$serverUrlBase + 'history/findHistoryById',   //请求加载历史接口
        method:'get',
        params:{
          historyId: historyId    // 传递historyId
        }
      }).then(res =>{
        console.log(res.data)
        this.messages = res.data.data;
        this.scrollToBottom()
      })
    },
    deleteHistory(history_id){    //删除对话
      this.$axios({
      url: this.$serverUrlBase + 'history/deleteHistoryByRootId',   //请求删除对话接口
      method:'delete',    //删除数据使用“delete”
      params:{
        history_id: history_id,
      }
      }).then(res =>{
        console.log('删除成功',res)
        this.historyList = this.historyList.filter(item => item.historyId !== history_id)   //从会话列表中删除指定ID的那条记录
      })
    },
    // 打开对话记录接着对话存储数据
    openHistorySaveData(question, answer){
      this.$axios({
        url:this.$serverUrlBase + 'history/openHistorySaveData',    //请求打开对话记录存储数据接口
        method:'post',
        data: JSON.stringify({    //把对象转换成JSON字符串。 原因：HTTP协议只能传输文本（字符串），不能直接传输JavaScript对象。
          'question':question,
          'answer':answer,
          'parentId':this.openHistoryId,
          'userId':this.userId
        }),
      })

    },
    updateHistoryById(history_id, question, answer) {   //对话后更新历史记录
      this.$axios({
        url: this.$serverUrlBase + 'history/updateHistoryById',     //请求接口
        method: 'put',    //更新数据使用“put”
        params: {       //params表示参数拼接在url上，data表示参数放在请求体中。params可以被缓存，data不行
          history_id: history_id,
          question: question,
          answer: answer
        }
      }).then(res => {
        console.log('更新成功', res)
        this.currentSessionTitle = question     //左侧历史记录相应部分把第一个问题当作标题
        this.history_List()
      }).catch(error => {
        console.error('更新失败详情：', error.response && error.response.data ? error.response.data : error)
        console.log('本次更新参数：', history_id, question, answer)
      })
    },


    // ========== 历史记录相关方法 ==========

    /**
     * 创建新对话
     */
      createNewChat() {
      this.$axios({
        url: this.$serverUrlBase + 'chat/createNewChat',    //请求接口
        method: 'post',
        params: {
          user_id: this.userId
        }
      }).then(res => {
        console.log('新建对话成功', res)
        this.openHistoryId = res.data.data
        this.currentSessionId = res.data.data
        this.currentSessionTitle = '新对话'
        this.messages = [{ role: 'system', content: '我是 qwen3.7-max，有什么可以帮助您的吗 😊' }]
        this.question = null
        this.isNewChat = true
        // 清空消息列表（重置为系统欢迎消息）
        // this.messages = [
        //   {role: 'system', content: '我是 qwen3.7-max，有什么可以帮助您的吗 😊'}
        // ];

        this.history_List()
        this.$message.success('已创建新对话')
        this.scrollToBottom()
      })

    },



    /**
     * 清空所有历史记录
     */
    clearAllHistory() {

    },

    // ========== 聊天方法 ==========
    chat() {
      let _this = this;
      let myQuestion = this.question;   //保存问题、清空问题输入框
      this.question = null;
      myQuestion = myQuestion ? myQuestion.trim() : '';   //去掉空格
      // 判断问题是否有输入
      if (myQuestion === '') {
        this.$message.warning('请输入问题');
        return;
      }
      // 添加用户消息和ai占位符
      this.messages.push({ role: 'user', content: myQuestion });
      this.messages.push({ role: 'assistant', content: '正在思考...' });
      this.loading = true;
      this.scrollToBottom();

      let s = "";   //存储ai返回的答案
      // 构造请求参数
      let params = new URLSearchParams({
        question: myQuestion,
        history_id: this.openHistoryId
      });
      // 构造EventSource对象
      let eventSource = new EventSource(this.$serverUrlBase + 'chat/chatStream?' + params);
      // 监听事件---连接打开时触发
      eventSource.onopen = (event) => {
        console.log('连接打开');
      }
      // 监听事件-----发生错误时出发
      eventSource.onerror = (event) => {
        console.log(event);       //把错误的详细信息打印到浏览器控制台
        console.log('发生错误');
        eventSource.close();        // 主动关闭连接，防止无限重连消耗资源。
      }
      //监听事件----接收到服务器推送的消息时触发
      eventSource.onmessage = (event) => {
        try {
          let oneData = JSON.parse(event.data);   //取出数据并且转为js对象
          if (oneData.content === '[DONE]') {   //判断是否终止内容（后端通常在流式输出结束时发送一个特殊标记 "[DONE]"）
            this.loading = false;
            eventSource.close();    //关闭连接
            if (this.isNewChat) {   // 如果是新会话，调用方法更新历史记录
            _this.updateHistoryById(this.openHistoryId, myQuestion, s)
            this.isNewChat = false  // 标记为已有会话
          } else {    // 如果不是新会话，调用方法保存当前对话到历史记录
            _this.openHistorySaveData(myQuestion, s)
          }
          // 保存数据---打开对话记录之后对话进行结果保存

            // 更新消息数量
            const currentItem = this.historyList.find(item => item.historyId === this.currentSessionId);    // 从会话列表中找到当前正在对话的那条记录
            if (currentItem) {      // 如果找到了当前会话记录
              currentItem.messageCount = this.messages.filter(m => m.role !== 'system').length;   // 更新消息数量：过滤掉 role 为 'system' 的消息（系统消息不计入统计），然后计算剩余消息的条数
              currentItem.time = new Date().toLocaleString();     // 更新最后活跃时间：设置为当前时间的本地字符串格式
            }

            this.scrollToBottom();    // 页面滚动到底部
            return;
          }
          // 显示内容
          s += oneData.content;
          _this.messages[_this.messages.length - 1].content = s;
          // 流式输出时实时滚动到底部
          this.scrollToBottom();
        } catch (e) {
          console.error('解析失败：', e);
        }
      }
      //监听事件----推送结束
      eventSource.onclose = (event) => {
        console.log('推送结束');
        eventSource.close();  // 关闭连接
      }
    }
  },
  mounted() {
    this.scrollToBottom();

    // 设置当前会话标题
    if (this.historyList.length > 0) {      // 设置当前会话标题：如果历史记录列表不为空
      const firstItem = this.historyList[0];    // 取列表中的第一条记录
      this.currentSessionTitle = firstItem.title;   // 把它的标题赋值给当前会话标题
    }
    this.scrollToBottom();    //页面加载时滚动到聊天底部
    this.userId = sessionStorage.getItem('userId');   //// 从浏览器的sessionStorage中读取用户ID，保存到组件的data里
    this.history_List();     //调用方法获取历史记录
  },
}
</script>

<style scoped>
/* ============================================
   整体布局
   ============================================ */
.chat-layout {
  display: flex;
  min-height: 100vh;
  background: #0b0b0b;
  font-family: 'Segoe UI', Roboto, system-ui, -apple-system, sans-serif;
}

/* ============================================
   左侧历史记录面板
   ============================================ */
.history-panel {
  width: 300px;
  min-width: 300px;
  background: #1a1a1a;
  border-right: 1px solid rgba(212, 175, 55, 0.15);
  display: flex;
  flex-direction: column;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
}

/* 折叠状态 */
.history-panel.collapsed {
  width: 56px;
  min-width: 56px;
}

/* ===== 面板头部 ===== */
.history-header {
  padding: 1rem 1.2rem;
  border-bottom: 1px solid rgba(212, 175, 55, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  min-height: 60px;
}

.history-panel.collapsed .history-header {
  padding: 1rem 0.8rem;
  justify-content: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.header-title .icon {
  font-size: 1.2rem;
}

.header-title .title-text {
  color: #f5f0eb;
  font-size: 1rem;
  font-weight: 600;
  white-space: nowrap;
}

.history-panel.collapsed .header-title .title-text {
  display: none;
}

.collapse-btn {
  background: transparent;
  border: none;
  color: #6b6258;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(212, 175, 55, 0.1);
  color: #d4af37;
}

.history-panel.collapsed .collapse-btn {
  font-size: 0.9rem;
}

/* ===== 新建对话按钮 ===== */
.history-actions {
  padding: 0.8rem 1.2rem;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(212, 175, 55, 0.06);
}

.history-panel.collapsed .history-actions {
  display: none;
}

.new-chat-btn {
  width: 100%;
  padding: 0.7rem 1rem;
  background: linear-gradient(145deg, #d4af37, #b8962e);
  color: #0b0b0b;
  font-weight: 600;
  font-size: 0.9rem;
  border: none;
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.new-chat-btn .plus-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.new-chat-btn:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 24px -6px rgba(212, 175, 55, 0.35);
}

.new-chat-btn:active {
  transform: scale(0.97);
}

/* ===== 历史记录列表 ===== */
.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0.6rem;
}

.history-panel.collapsed .history-list {
  display: none;
}

.history-list::-webkit-scrollbar {
  width: 3px;
}

.history-list::-webkit-scrollbar-track {
  background: transparent;
}

.history-list::-webkit-scrollbar-thumb {
  background: rgba(212, 175, 55, 0.3);
  border-radius: 10px;
}

/* ---- 空状态 ---- */
.empty-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #6b6258;
  text-align: center;
  gap: 0.3rem;
}

.empty-history .empty-icon {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
}

.empty-history .empty-text {
  font-size: 0.95rem;
  font-weight: 500;
}

.empty-history .empty-hint {
  font-size: 0.8rem;
  opacity: 0.7;
}

/* ---- 历史记录项 ---- */
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 0.9rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 2px;
  position: relative;
  gap: 0.5rem;
}

.history-item:hover {
  background: rgba(212, 175, 55, 0.06);
}

.history-item.active {
  background: rgba(212, 175, 55, 0.12);
  border-left: 3px solid #d4af37;
}

.history-item.active:hover {
  background: rgba(212, 175, 55, 0.16);
}

/* 历史项内容 */
.history-item-content {
  display: flex;
  align-items: flex-start;
  gap: 0.7rem;
  flex: 1;
  min-width: 0;
}

.history-item-content .item-icon {
  font-size: 1rem;
  margin-top: 1px;
  flex-shrink: 0;
}

.item-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  color: #f0ece6;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 2px;
}

.history-time {
  color: #6b6258;
  font-size: 0.65rem;
}

.history-messages {
  color: #4a4440;
  font-size: 0.6rem;
  background: rgba(212, 175, 55, 0.08);
  padding: 1px 8px;
  border-radius: 10px;
}

/* 操作按钮（悬停显示） */
.item-actions {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-item:hover .item-actions {
  opacity: 1;
}

.action-btn {
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #6b6258;
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(212, 175, 55, 0.1);
  color: #d4af37;
}

.action-btn.delete-btn:hover {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
}

/* ===== 面板底部 ===== */
.history-footer {
  padding: 0.7rem 1.2rem;
  border-top: 1px solid rgba(212, 175, 55, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.history-panel.collapsed .history-footer {
  display: none;
}

.footer-info {
  color: #6b6258;
  font-size: 0.75rem;
}

.clear-all-btn {
  background: transparent;
  border: none;
  color: #6b6258;
  font-size: 0.7rem;
  cursor: pointer;
  padding: 4px 10px;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.clear-all-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

/* ============================================
   右侧聊天区域（原有样式，微调）
   ============================================ */
.chat-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 1rem;
  box-sizing: border-box;
  background-image: radial-gradient(circle at 20% 30%, rgba(212, 175, 55, 0.04) 0%, transparent 50%),
  radial-gradient(circle at 80% 70%, rgba(212, 175, 55, 0.03) 0%, transparent 50%);
}

.chat-card {
  background: #1a1a1a;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  border-radius: 40px;
  width: 100%;
  max-width: 800px;
  height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 30px 60px -15px rgba(0, 0, 0, 0.8),
  0 0 0 1px rgba(212, 175, 55, 0.25),
  inset 0 0 0 1px rgba(212, 175, 55, 0.08);
  border: 1px solid rgba(212, 175, 55, 0.15);
  overflow: hidden;
  transition: transform 0.25s ease, box-shadow 0.3s ease;
}

.chat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 40px 70px -18px #000000cc,
  0 0 0 1.5px rgba(212, 175, 55, 0.35),
  inset 0 0 0 1px rgba(212, 175, 55, 0.12);
}

/* 头部 */
.chat-header {
  padding: 1.2rem 2rem;
  border-bottom: 1px solid rgba(212, 175, 55, 0.15);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h2 {
  color: #f5f0eb;
  font-weight: 600;
  font-size: 1.3rem;
  margin: 0;
  background: linear-gradient(135deg, #f5f0eb 0%, #d4af37 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.current-session {
  color: #6b6258;
  font-size: 0.75rem;
  background: rgba(212, 175, 55, 0.08);
  padding: 2px 12px;
  border-radius: 12px;
  border: 1px solid rgba(212, 175, 55, 0.08);
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.status {
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  color: #6b6258;
}

.status.online {
  color: #4caf50;
}

/* 消息区域 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  scroll-behavior: smooth;
}

.chat-body::-webkit-scrollbar {
  width: 4px;
}

.chat-body::-webkit-scrollbar-track {
  background: transparent;
}

.chat-body::-webkit-scrollbar-thumb {
  background: #d4af37;
  border-radius: 10px;
}

/* 消息 */
.message-wrapper {
  display: flex;
  gap: 0.8rem;
  align-items: flex-start;
  max-width: 85%;
  animation: fadeIn 0.3s ease;
}

.message-wrapper.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant-message {
  align-self: flex-start;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #2a2a2a;
  border: 1px solid rgba(212, 175, 55, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: linear-gradient(135deg, #d4af37, #b8962e);
  border-color: #d4af37;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.message-role {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #6b6258;
  font-weight: 500;
}

.message-text {
  background: #2a2a2a;
  padding: 0.6rem 1rem;
  border-radius: 16px;
  border-top-left-radius: 4px;
  color: #f0ece6;
  font-size: 0.95rem;
  line-height: 1.6;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.user-message .message-text {
  background: linear-gradient(135deg, #d4af37, #b8962e);
  color: #0b0b0b;
  border-top-left-radius: 16px;
  border-top-right-radius: 4px;
}

/* 打字动画 */
.typing span {
  display: inline-block;
  animation: typing 1.4s infinite both;
  font-size: 1.2rem;
  margin: 0 1px;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.2; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 输入区域 */
.chat-footer {
  padding: 1rem 2rem 1.5rem;
  border-top: 1px solid rgba(212, 175, 55, 0.08);
  display: flex;
  gap: 0.8rem;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  padding: 0.8rem 1.2rem;
  border: 1.5px solid #3a3a3a;
  border-radius: 60px;
  font-size: 1rem;
  background: #0f0f0f;
  color: #f0ece6;
  outline: none;
  transition: all 0.25s ease;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.6);
}

.chat-input:focus {
  border-color: #d4af37;
  box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.15), inset 0 2px 6px rgba(0, 0, 0, 0.6);
  background: #141414;
}

.chat-input::placeholder {
  color: #6b6258;
  font-weight: 300;
}

.chat-btn {
  padding: 0.8rem 2rem;
  background: linear-gradient(145deg, #d4af37, #b8962e);
  color: #0b0b0b;
  font-weight: 700;
  font-size: 0.95rem;
  border: none;
  border-radius: 60px;
  cursor: pointer;
  transition: all 0.25s ease;
  letter-spacing: 1px;
  text-transform: uppercase;
  box-shadow: 0 8px 24px -6px rgba(212, 175, 55, 0.25);
  flex-shrink: 0;
}

.chat-btn:hover {
  background: linear-gradient(145deg, #e0c04a, #c8a132);
  transform: scale(1.02);
  box-shadow: 0 12px 32px -8px rgba(212, 175, 55, 0.45);
}

.chat-btn:active {
  transform: scale(0.97);
}

/* ============================================
   响应式
   ============================================ */
@media (max-width: 768px) {
  .history-panel {
    width: 240px;
    min-width: 240px;
  }
  .history-panel.collapsed {
    width: 48px;
    min-width: 48px;
  }
  .chat-card {
    height: 92vh;
    border-radius: 24px;
  }
  .chat-header {
    padding: 0.8rem 1.2rem;
  }
  .chat-body {
    padding: 1rem 1.2rem;
  }
  .chat-footer {
    padding: 0.8rem 1.2rem 1rem;
  }
  .message-wrapper {
    max-width: 95%;
  }
  .header-left h2 {
    font-size: 1rem;
  }
  .current-session {
    max-width: 100px;
    font-size: 0.65rem;
  }
}

@media (max-width: 480px) {
  .history-panel {
    width: 0;
    min-width: 0;
    border-right: none;
    position: absolute;
    z-index: 100;
    height: 100vh;
    box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
  }
  .history-panel.collapsed {
    width: 0;
    min-width: 0;
  }
  .history-panel:not(.collapsed) {
    width: 280px;
    min-width: 280px;
  }
  .chat-card {
    border-radius: 16px;
  }
  .chat-container {
    padding: 0.5rem;
  }
}
</style>
