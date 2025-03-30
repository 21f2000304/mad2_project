<template>
    <div class="login-container">
      <h2>Admin Login</h2>
      
      <form @submit.prevent="handleLogin">
        <input type="email" placeholder="Email" v-model="email" required @input="clearError" />
        <input type="password" placeholder="Password" v-model="password" required @input="clearError" />
        <button type="submit" :disabled="loading">{{ loading ? "Logging in..." : "Login" }}</button>
      </form>
  
      <p v-if="error" class="error-message">{{ error }}</p>
    </div>
  </template>
  
  <script>
  export default {
    name: "AdminLogin",
    data() {
      return {
        email: "",
        password: "",
        loading: false,
        error: "",
      };
    },
    methods: {
      async handleLogin() {
        if (!this.email || !this.password) {
          this.error = "Email and password are required!";
          return;
        }
        
        this.loading = true;
        this.error = "";
  
        try {
          const response = await fetch("http://localhost:5000/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: this.email, password: this.password }),
          });
  
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || "Login failed");
  
          if (data.role !== "admin") {
            throw new Error("Access Denied: Only admins can log in here!");
          }
  
          localStorage.removeItem("user");
          localStorage.removeItem("token");
  
          localStorage.setItem("user", JSON.stringify({
            id: data.id,
            role: data.role,
            username: data.username,
            token: data.token,
            exp: Date.now() + 60 * 60 * 1000, 
          }));
  
          localStorage.setItem("token", data.token);
  
          window.dispatchEvent(new Event("storage"));
  
          this.$router.push("/admin-dashboard");
        } catch (error) {
          this.error = error.message;
        } finally {
          this.loading = false;
        }
      },
      
      clearError() {
        this.error = "";
      }
    },
  };
  </script>
  
  
  <style scoped>
  .login-container {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    text-align: center;
  }
  
  h2 {
    font-size: 2rem;
    margin-bottom: 20px;
  }
  
  form {
    display: flex;
    flex-direction: column;
    gap: 15px;
    width: 300px;
  }
  
  input {
    padding: 10px;
    font-size: 1rem;
    border: 1px solid #ccc;
    border-radius: 5px;
  }
  
  button {
    padding: 10px;
    font-size: 1rem;
    color: white;
    background-color: #007bff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
  }
  
  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .error-message {
    color: red;
    margin-top: 10px;
  }
  </style>
  