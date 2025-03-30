<template>
  <div class="signup-container">
    <h2>Sign Up</h2>

    <form @submit.prevent="handleSignup">
      <input type="email" placeholder="Email" v-model="email" required />
      <input type="password" placeholder="Password" v-model="password" required />
      <input type="text" placeholder="Full Name" v-model="fullName" required />
      <input type="text" placeholder="Qualification" v-model="qualification" />
      <input type="date" placeholder="Date of Birth" v-model="dob" />

      <label for="reminderTime" class="reminder-label">
        ⏰ Choose Your Preferred Reminder Time:
      </label>
      <input type="time" id="reminderTime" v-model="reminderTime" />

      <button type="submit" :disabled="loading">
        {{ loading ? "Signing up..." : "Sign Up" }}
      </button>
    </form>

    <p>Already have an account? <router-link to="/user-login">Login</router-link></p>
  </div>
</template>

<script>
export default {
  name: "SignUp",
  data() {
    return {
      email: "",
      password: "",
      fullName: "",
      qualification: "",
      dob: "",
      reminderTime: "19:00",
      loading: false,
    };
  },
  methods: {
    async handleSignup() {
      if (!this.email || !this.password || !this.fullName) {
        alert("Email, password, and full name are required!");
        return;
      }

      this.loading = true;

      try {
        const response = await fetch("http://localhost:5000/api/signup", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: this.email,
            password: this.password,
            full_name: this.fullName,
            qualification: this.qualification,
            dob: this.dob,
            reminder_time: this.reminderTime,
          }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Signup failed");

        alert(data.message);
        window.location.href = "/user-login"; 
      } catch (error) {
        alert(error.message);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>

.signup-container {
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

.reminder-label {
  font-size: 1.1rem;
  font-weight: bold;
  color: #ff6b6b;
  margin-top: 10px;
  display: block;
}

button {
  padding: 10px;
  font-size: 1rem;
  color: white;
  background-color: #28a745;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

button:hover {
  background-color: #218838;
}

.already-logged-in {
  color: green;
  font-size: 1.2rem;
  margin-top: 20px;
}

p {
  margin-top: 10px;
}

a {
  color: #007bff;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
