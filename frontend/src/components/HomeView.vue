<template>
  <div class="home-container">
    <h1>Welcome to Quiz App</h1>
    

    <div class="button-group">
      <router-link to="/user-login" class="btn">User</router-link>
      <router-link to="/admin-login" class="btn">Admin</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: "HomeView",
  data() {
    return {
      isLoggedIn: false, 
    };
  },
  mounted() {
    const user = localStorage.getItem("user");
    if (user) {
      this.isLoggedIn = true;
    }
  },
};
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
}

h1 {
  font-size: 2.5rem;
  margin-bottom: 20px;
}

.button-group {
  display: flex;
  gap: 20px;
}

.btn {
  text-decoration: none;
  font-size: 1.2rem;
  padding: 10px 20px;
  border-radius: 8px;
  background-color: #007bff;
  color: white;
  transition: background 0.3s;
}

.btn:hover {
  background-color: #0056b3;
}
</style>
