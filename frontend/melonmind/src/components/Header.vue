<template>
  <div class="header">
    <div class="header-content clearfix">
      <div class="nav-control">
        <div class="hamburger">
          <span class="toggle-icon"><i class="icon-menu"></i></span>
        </div>
      </div>
      <div class="header-right">
        <ul class="clearfix">
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Header'
}
</script>

<style scoped>
.header {
  height: 70px;
  position: relative;
  z-index: 999;
  background: #fff;
  padding: 0 30px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.nav-control {
  margin-right: 15px;
}

.hamburger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  cursor: pointer;
}

.toggle-icon {
  font-size: 20px;
}
</style>