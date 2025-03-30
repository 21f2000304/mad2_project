<template>
  <div class="edit-profile-container">
    <h2>Edit Profile</h2>
    <form @submit.prevent="validateAndUpdateProfile">
      <label>Email:</label>
      <input v-model="userProfile.email" type="email" required />
      <p v-if="errors.email" class="error-message">{{ errors.email }}</p>

      <template v-if="userProfile.role === 'user'">
        <label>Full Name:</label>
        <input v-model="userProfile.full_name" type="text" required />
        <p v-if="errors.full_name" class="error-message">{{ errors.full_name }}</p>

        <label>Qualification:</label>
        <input v-model="userProfile.qualification" type="text" />

        <label>Date of Birth:</label>
        <input v-model="userProfile.dob" type="date" />
        <p v-if="errors.dob" class="error-message">{{ errors.dob }}</p>

        <label>Reminder Time:</label>
        <input v-model="userProfile.reminder_time" type="time" />
        <p v-if="errors.reminder_time" class="error-message">{{ errors.reminder_time }}</p>
      </template>


      <template v-if="userProfile.role === 'admin'">
        <label>Name:</label>
        <input v-model="userProfile.name" type="text" required />
        <p v-if="errors.name" class="error-message">{{ errors.name }}</p>
      </template>


      <label>New Password (optional):</label>
      <input v-model="userProfile.password" type="password" />
      <p v-if="errors.password" class="error-message">{{ errors.password }}</p>


      <p v-if="successMessage" class="success-message">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>


      <div class="button-group">
        <button type="submit" class="update-btn">Update Details</button>
        <button type="button" @click="closeWindow" class="cancel-btn">Cancel</button>
      </div>
    </form>
  </div>
</template>

<script>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";

export default {
  setup() {
    const userProfile = ref({
      email: "",
      role: "",
      password: "",
      full_name: "",
      qualification: "",
      dob: "",
      reminder_time: "",
      name: "",
    });

    const successMessage = ref("");
    const errorMessage = ref("");
    const errors = ref({}); 

    const route = useRoute();
    const userId = ref(route.query.id || null);
    const token = localStorage.getItem("token");


    const getUserDetails = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/users/${userId.value}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (!response.ok) throw new Error("Failed to fetch user details");
        userProfile.value = await response.json();
      } catch (error) {
        console.error("Error fetching user details:", error);
        errorMessage.value = "Failed to fetch user details.";
      }
    };


    const validateForm = () => {
      errors.value = {}; 
      if (!userProfile.value.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(userProfile.value.email)) {
        errors.value.email = "Invalid email format.";
      }
      if (userProfile.value.role === "user" && !userProfile.value.full_name) {
        errors.value.full_name = "Full name is required.";
      }
      if (userProfile.value.role === "admin" && !userProfile.value.name) {
        errors.value.name = "Name is required.";
      }
      if (userProfile.value.password && (userProfile.value.password.length < 6 || userProfile.value.password.length > 128)) {
        errors.value.password = "Password must be between 6 and 128 characters.";
      }
      if (userProfile.value.dob && isNaN(Date.parse(userProfile.value.dob))) {
        errors.value.dob = "Invalid date format.";
      }
      if (userProfile.value.reminder_time && !/^\d{2}:\d{2}$/.test(userProfile.value.reminder_time)) {
        errors.value.reminder_time = "Invalid time format (HH:MM).";
      }

      return Object.keys(errors.value).length === 0;
    };


    const validateAndUpdateProfile = async () => {
      if (!validateForm()) return;

      try {
        const updatedData = {
          email: userProfile.value.email,
        };

        if (userProfile.value.role === "user") {
          updatedData.full_name = userProfile.value.full_name;
          updatedData.qualification = userProfile.value.qualification;
          updatedData.dob = userProfile.value.dob;
          updatedData.reminder_time = userProfile.value.reminder_time ? userProfile.value.reminder_time.slice(0, 5) : null;
        } else if (userProfile.value.role === "admin") {
          updatedData.name = userProfile.value.name;
        }

        if (userProfile.value.password) {
          updatedData.password = userProfile.value.password;
        }

        const response = await fetch(`http://localhost:5000/api/users/${userId.value}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(updatedData),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.error || "Failed to update profile");

        successMessage.value = "Profile updated successfully!";
        errorMessage.value = "";


        const storedUser = JSON.parse(localStorage.getItem("user")) || {};
        storedUser.username = userProfile.value.full_name || userProfile.value.name;
        localStorage.setItem("user", JSON.stringify(storedUser));


        setTimeout(() => {
          window.opener?.postMessage({ type: "profileUpdated", userData: storedUser }, "*");
          window.close();
        }, 1500);
      } catch (error) {
        console.error("Error updating profile:", error);
        errorMessage.value = error.message || "Failed to update profile.";
      }
    };


    const closeWindow = () => {
      window.close();
    };

    onMounted(getUserDetails);

    return { userProfile, validateAndUpdateProfile, closeWindow, successMessage, errorMessage, errors };
  },
};
</script>

<style>
.edit-profile-container {
  width: 90%;
  max-width: 400px;
  margin: auto;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  background: #fff;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  max-height: 90vh;
  overflow-y: auto;
}

form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

label {
  font-weight: bold;
  text-align: left;
  display: block;
  margin-bottom: 4px;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 14px;
}

button {
  background-color: #4caf50;
  color: white;
  border: none;
  padding: 10px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 16px;
  transition: background 0.3s;
}

button:hover {
  background-color: #45a049;
}

.button-group {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.success-message, .error-message {
  font-weight: bold;
  margin-top: 10px;
  text-align: center;
}

.success-message {
  color: green;
}

.error-message {
  color: red;
}
</style>
