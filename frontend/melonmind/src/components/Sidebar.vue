<template>
  <div class="nk-sidebar">
    <div class="nk-nav-scroll">
      <ul class="metismenu" id="menu">
        <li class="nav-label">Menu</li>
        <li>
          <router-link to="/" class="has-arrow" aria-expanded="false">
            <i class="icon-speedometer menu-icon"></i><span class="nav-text">Dashboard</span>
          </router-link>
        </li>
        <li>
          <router-link to="/pdfloader" class="has-arrow" aria-expanded="false">
            <i class="icon-doc menu-icon"></i><span class="nav-text">PDF Loader</span>
          </router-link>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Sidebar'
}
</script>

<style scoped>
/* 这里会包含从模板中提取的CSS样式 */
.nk-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 999;
  height: 100vh;
  background: #fff;
  width: 240px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  transition: all .2s ease;
}

.nk-nav-scroll {
  height: calc(100% - 80px);
  overflow: auto;
}

.metismenu {
  padding: 20px 0;
}

.nav-label {
  padding: 0 20px;
  color: #8699b2;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: 1.2px;
}

.metismenu li a {
  padding: 12px 15px;
  margin: 0 15px;
  display: flex;
  align-items: center;
  border-radius: 4px;
  transition: all .3s ease;
  color: #333;
  text-decoration: none;
}

.metismenu li a:hover {
  background-color: #f0f5ff;
  color: #6a6c70;
}

.metismenu li a i {
  margin-right: 10px;
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.metismenu li.active > a {
  background-color: #3498DB;
  color: white;
}
</style>