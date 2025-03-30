<template>
  <div id="app">
    <nav v-if="$route.meta.defaultnavbar" class="navbar">
      <button class="hamburger" @click="toggleMobileMenu">☰</button>
      <div class="logo">
        <a href="#" @click.prevent="redirectToDashboard">Quiz App</a>
      </div>

      <div class="search-container">
        <input 
          v-model="globalSearchQuery"
          placeholder="Search..."
          class="search-input"
        >
      </div>
      <div class="nav-links" :class="{ 'mobile-active': mobileMenuOpen }">
        <template v-if="!user.role">
          <router-link to="/user-login">User Login</router-link>
          <router-link to="/admin-login">Admin Login</router-link>
        </template>
        <template v-else-if="user.role === 'admin'">
          <router-link to="/admin-dashboard">Home</router-link>
          <router-link to="/admin/manage-quizzes">Manage Quizzes</router-link>
          <router-link to="/admin/manage-users">Manage Users</router-link>
          <router-link to="/reports">Reports</router-link>
        </template>
        <template v-else>
          <router-link to="/user-dashboard">Dashboard</router-link>
          <router-link to="/reports">Reports</router-link>
        </template>
      </div>
      <div v-if="user.role" class="user-info">
        <span class="username" @click.stop="toggleMenu">
          Welcome, {{ user.username }} ▼
        </span>
        <div class="dropdown-menu" :class="{ active: menuOpen }">
          <ul>
            <li @click="openEditProfile">Edit Profile</li>
            <li @click="logout">Logout</li>
          </ul>
        </div>
      </div>
    </nav>
    <router-view :search-query="globalSearchQuery" />
  </div>
</template>

<script>
import { ref, reactive, watch, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";

export default {
  setup() {
    const router = useRouter();
    const menuOpen = ref(false);
    const globalSearchQuery = ref('');
    const mobileMenuOpen = ref(false);
    
    const user = reactive({
      role: null,
      username: "User",
    });
    const toggleMobileMenu = () => {
      mobileMenuOpen.value = !mobileMenuOpen.value;
    };
    const loadUserData = () => {
      const userData = JSON.parse(localStorage.getItem("user"));
      if (userData?.role) {
        user.role = userData.role.toLowerCase();
        user.username = userData.username;
      } else {
        user.role = null;
        user.username = "User";
      }
    };
    const syncUserData = () => {
      console.log("User data updated, re-rendering navbar.");
      loadUserData();
    };
    watch(() => router.currentRoute.value, (newRoute) => {
      console.log("Route changed to:", newRoute.path);
      if (newRoute.path === "/") {
        if (user.role) {
          if (user.role === "user") {
            router.push("/user-dashboard");
          } else if (user.role === "admin") {
            router.push("/admin-dashboard");
          }
        }
      }
    });


    onMounted(() => {
      loadUserData();
      window.addEventListener("storage", syncUserData);
      document.addEventListener("click", closeMenuOnOutsideClick);
      document.addEventListener('click', closeMobileMenu);
    });

    onBeforeUnmount(() => {
      window.removeEventListener("storage", syncUserData);
      document.removeEventListener("click", closeMenuOnOutsideClick);
      document.removeEventListener('click', closeMobileMenu);
    });

    const logout = () => {
      console.log("Logging out user...");
      localStorage.removeItem("user");
      user.role = null;
      user.username = "User";
      router.push("/");
    };

    const toggleMenu = (event) => {
      if (event) event.stopPropagation();
      menuOpen.value = !menuOpen.value;
    };
    const closeMobileMenu = (event) => {
      if (!event.target.closest('.nav-links') && 
          !event.target.closest('.hamburger')) {
        mobileMenuOpen.value = false;
      }
    };

    const closeMenuOnOutsideClick = (event) => {
      const userInfo = event.target.closest('.user-info');
      if (!userInfo) {
        menuOpen.value = false;
      }
    };

    
  const openEditProfile = () => {
      const userDataString = localStorage.getItem("user");
      if (!userDataString) return;

      try {
        const userData = JSON.parse(userDataString);
        const tokenPayload = JSON.parse(atob(userData.token.split(".")[1]));
        const subData = JSON.parse(tokenPayload.sub);
        const userId = subData.id;

        if (!userId) return;

        const url = `/edit-profile?id=${encodeURIComponent(userId)}&role=${encodeURIComponent(userData.role)}`;
        window.open(url, "_blank", "width=600,height=600,noopener,noreferrer");
      } catch (error) {
      }
    };

    const navigateTo = (path) => {
      router.push(path);
    };

    return {
      user,
      menuOpen,
      logout,
      navigateTo,
      toggleMenu,
      openEditProfile,
      globalSearchQuery,  
      mobileMenuOpen,
      toggleMobileMenu
    };
  },
};
</script>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.6;
  background-color: #f8f9fa;
}

#app {
  min-height: 100vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background: #23272b;
  color: white;
  gap: 1rem;
  flex-wrap: wrap;
  position: relative;
  z-index: 1000;
}

.logo a {
  font-size: 1.5rem;
  font-weight: 600;
  color: white;
  text-decoration: none;
  transition: opacity 0.2s ease;
  white-space: nowrap;
}

.logo a:hover {
  opacity: 0.9;
}

.nav-links {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin: 0;
  padding: 0;
}

.nav-links a {
  text-decoration: none;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: all 0.2s ease;
  font-weight: 500;
  white-space: nowrap;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: #007bff;
  transform: translateY(-1px);
}

.search-container {
  flex: 1 1 300px;
  max-width: 400px;
  margin: 0 1rem;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 0.6rem 1.2rem;
  border: 2px solid #4a4f55;
  border-radius: 2rem;
  background: #2d3238;
  color: white;
  font-size: 0.95rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-input:focus {
  outline: none;
  border-color: #646cff;
  box-shadow: 0 0 0 3px rgba(100, 108, 255, 0.15);
  background: #363b42;
}

.user-info {
  position: relative;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 5px;
  transition: background 0.2s ease;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 8px;
  width: 180px;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.2s ease;
}

.dropdown-menu.active {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-menu ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.dropdown-menu li {
  padding: 0.75rem 1rem;
  color: #2d3748;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  cursor: pointer;
}

.dropdown-menu li:hover {
  background: #f8f9fa;
  color: #007bff;
  padding-left: 1.25rem;
}


.hamburger {
  display: none;
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
  order: 1;
  z-index: 1001;
}

@media (max-width: 768px) {
  .navbar {
    padding: 0.75rem 1rem;
    gap: 0.75rem;
  }

  .nav-links {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    width: 100%;
    background: #2d3238;
    flex-direction: column;
    padding: 1rem;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    z-index: 999;
  }

  .nav-links.mobile-active {
    display: flex;
    animation: slideDown 0.3s ease;
  }

  .nav-links a {
    width: 100%;
    justify-content: center;
    padding: 0.75rem;
  }

  .logo {
    order: 2;
    flex: 1;
    text-align: center;
  }

  .search-container {
    order: 3;
    flex: 1 1 100%;
    margin: 0.5rem 0 0 0;
  }

  .user-info {
    order: 4;
    margin-left: auto;
  }

  .hamburger {
    display: block;
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 480px) {
  .logo a {
    font-size: 1.2rem;
  }

  .search-input {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }

  .user-info {
    font-size: 0.9rem;
  }

  .dropdown-menu {
    width: 160px;
  }
}


.hidden {
  display: none !important;
}

.visible {
  display: flex !important;
}
</style>
