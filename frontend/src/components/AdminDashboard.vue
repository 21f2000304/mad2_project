<template>
  <div class="dashboard-container">
    <div class="dashboard-content">
      <Subjects :search-query="searchQuery" />
    </div>
  </div>
</template>

<script>
import Subjects from "./Subjects.vue";

export default {
  name: "AdminDashboard",
  components: {
    Subjects,
  },
  props: ['searchQuery'],
  data() {
    return {
      adminName: "Admin",
    };
  },
  mounted() {
    this.getAdminData();
    window.addEventListener("storage", this.getAdminData);
  },
  beforeUnmount() {
    window.removeEventListener("storage", this.getAdminData);
  },
  methods: {
    getAdminData() {
      const user = JSON.parse(localStorage.getItem("user"));
      if (user && user.role === "admin") {
        this.adminName = user.username || user.name || "Admin";
      } else {
        this.$router.push("/admin-login");
      }
    },
  },
};
</script>

<style scoped>

.dashboard-container {
  width: 100%;
  min-height: 100vh;
  padding: 10px;
  background-color: #f8f9fa;
  box-sizing: border-box;
}


.dashboard-content {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 10px;
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  box-sizing: border-box;
}


@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .dashboard-content {
    padding: 15px;
  }
}

@media (max-width: 480px) {
  .dashboard-content {
    padding: 10px;
  }
}
</style>