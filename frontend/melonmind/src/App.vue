<template>
  <div id="app">
    <div id="main-wrapper">
      <Header />
      <Sidebar />
      <div class="content-body">
        <div class="container-fluid">
          <router-view />
        </div>
      </div>
      <div class="footer">
        <div class="copyright">
          <p>Copyright &copy; MelonMind 2023</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Header from './components/Header.vue'
import Sidebar from './components/Sidebar.vue'

export default {
  name: 'App',
  components: {
    Header,
    Sidebar
  }
}
</script>

<style>
/* 导入基本样式 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

#main-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-body {
  flex: 1;
  padding: 85px 0 0;
  margin-left: 240px; /* 侧边栏宽度 */
}

.footer {
  background: #fff;
  padding: 15px 30px;
  border-top: 1px solid #eee;
  margin-left: 240px;
}

.copyright {
  text-align: center;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .content-body, .footer {
    margin-left: 0;
  }
}
</style>