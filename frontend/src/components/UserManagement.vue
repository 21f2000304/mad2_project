<template>
    <div class="user-management">
        <div style="display: flex; justify-content: center;">
        <h2>User Management</h2>
        </div>

      <div class="tabs">
        <button v-for="tab in tabs" :key="tab" 
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab">
          {{ tab }}
        </button>
      </div>
 
      <div class="actions" v-if="selectedUsers.length > 0">
        <button v-if="activeTab === 'Pending'" @click="bulkUpdate('active')" :disabled="loading">Approve</button>
        <button v-if="activeTab === 'Pending'" @click="bulkUpdate('disabled')" :disabled="loading">Disable</button>
  
        <button v-if="activeTab === 'Active'" @click="bulkUpdate('disabled')" :disabled="loading">Disable</button>
  
        <button v-if="activeTab === 'Disabled'" @click="bulkUpdate('active')" :disabled="loading">Activate</button>
      </div>
  
      <p v-if="message" class="status-message">{{ message }}</p>
  
      <table>
        <thead>
          <tr>
            <th><input type="checkbox" @change="toggleSelectAll" :checked="isAllSelected" /></th>
            <th @click="sortBy('full_name')">Name <span>{{ getSortArrow('full_name') }}</span></th>
            <th @click="sortBy('email')">Email <span>{{ getSortArrow('email') }}</span></th>
            <th @click="sortBy('qualification')">Qualification <span>{{ getSortArrow('qualification') }}</span></th>
            <th @click="sortBy('dob')">DOB <span>{{ getSortArrow('dob') }}</span></th>
            <th @click="sortBy('last_seen')">Last Seen <span>{{ getSortArrow('last_seen') }}</span></th>
            <th @click="sortBy('reminder_time')">Reminder Time <span>{{ getSortArrow('reminder_time') }}</span></th>
            <th @click="sortBy('status')">Status <span>{{ getSortArrow('status') }}</span></th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in sortedAndFilteredUsers" :key="user.id">
            <td><input type="checkbox" v-model="selectedUsers" :value="user.id" /></td>
            <td>{{ user.full_name }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.qualification || 'N/A' }}</td>
            <td>{{ user.dob || 'N/A' }}</td>
            <td>{{ formatDateTime(user.last_seen) }}</td>
            <td>{{ user.reminder_time || 'N/A' }}</td>
            <td>{{ user.status }}</td>
            <td>
              <button v-if="user.status === 'pending'" @click="updateStatus(user.id, 'active')" :disabled="loading">Approve</button>
              <button v-if="user.status === 'pending'" @click="updateStatus(user.id, 'disabled')" :disabled="loading">Disable</button>
              <button v-if="user.status === 'active'" @click="updateStatus(user.id, 'disabled')" :disabled="loading">Disable</button>
              <button v-if="user.status === 'disabled'" @click="updateStatus(user.id, 'active')" :disabled="loading">Activate</button>
            </td>
          </tr>
        </tbody>
      </table>
  
      <p v-if="loading">Loading...</p>
    </div>
  </template>
  
  <script>
  export default {
    props: {
      searchQuery: {
        type: String,
        default: ""
      }
    },
    data() {
      return {
        users: [],
        activeTab: 'Pending',
        selectedUsers: [],
        loading: false,
        tabs: ['Pending', 'Active', 'Disabled'],
        sortKey: '',
        sortOrder: 1,
        message: ''
      };
    },
    computed: {
      filteredUsers() {
        return this.users.filter(user =>
          user.status.toLowerCase() === this.activeTab.toLowerCase() &&
          (user.full_name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
           user.email.toLowerCase().includes(this.searchQuery.toLowerCase()))
        );
      },
      sortedAndFilteredUsers() {
        return [...this.filteredUsers].sort((a, b) => {
          if (!this.sortKey) return 0;
          return this.sortOrder * (a[this.sortKey] > b[this.sortKey] ? 1 : -1);
        });
      },
      isAllSelected() {
        return this.selectedUsers.length > 0 && this.selectedUsers.length === this.filteredUsers.length;
      }
    },
    watch: {
      activeTab() {
        this.selectedUsers = []; 
      }
    },
    methods: {
      async fetchUsers() {
        this.loading = true;
        try {
          const token = localStorage.getItem("token");
          const response = await fetch("http://localhost:5000/api/users", {
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            credentials: "include"
          });
  
          if (response.status === 401) {
            console.error("Unauthorized: Redirecting to login...");
            this.$router.push("/admin-login");
            return;
          }
  
          if (!response.ok) throw new Error("Failed to fetch users");
          this.users = await response.json();
        } catch (error) {
          console.error(error);
        } finally {
          this.loading = false;
        }
      },
      async updateStatus(userId, status) {
        this.loading = true;
        try {
          const token = localStorage.getItem("token");
          await fetch(`http://localhost:5000/api/users/${userId}`, {
            method: 'PATCH',
            headers: { 
              'Content-Type': 'application/json',
              "Authorization": `Bearer ${token}` 
            },
            body: JSON.stringify({ status })
          });
          this.message = "User status updated successfully!";
          setTimeout(() => this.message = "", 2000);
          await this.fetchUsers();
  
          this.selectedUsers = [];
        } catch (error) {
          console.error(error);
        } finally {
          this.loading = false;
        }
      },
      async bulkUpdate(status) {
        this.loading = true;
        try {
          const token = localStorage.getItem("token");
          await fetch("http://localhost:5000/api/users/bulk-update", {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ user_ids: this.selectedUsers, status })
          });
          this.message = "Selected Users status updated successfully!";
          setTimeout(() => this.message = "", 2000);
          await this.fetchUsers();
  
          this.selectedUsers = [];
        } catch (error) {
          console.error(error);
        } finally {
          this.loading = false;
        }
      },
      sortBy(key) {
        if (this.sortKey === key) {
          this.sortOrder *= -1;
        } else {
          this.sortKey = key;
          this.sortOrder = 1;
        }
      },
      getSortArrow(key) {
        return this.sortKey === key ? (this.sortOrder === 1 ? '↑' : '↓') : '';
      },
      formatDateTime(dateTime) {
        return dateTime ? new Date(dateTime).toLocaleString() : 'N/A';
      },
      toggleSelectAll(event) {
        if (event.target.checked) {
          this.selectedUsers = this.filteredUsers.map(user => user.id);
        } else {
          this.selectedUsers = [];
        }
      }
    },
    mounted() {
      this.fetchUsers();
    }
  };
  </script>
  
  <style>
  .status-message {
    color: darkgreen;
    font-weight: bold;
    margin-bottom: 10px;
    text-align: center;
}


.user-management {
  padding: 20px;
  font-family: Arial, sans-serif;
}


.tabs {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.tabs button {
  padding: 10px 20px;
  cursor: pointer;
  border: none;
  border-radius: 5px;
  font-weight: bold;
  transition: background 0.3s ease, opacity 0.3s ease;
  background: #d0e7ff;
  color: #333;
  opacity: 0.8;
}

.tabs button:hover {
  background: #a5cfff;
  opacity: 1;
}

.tabs .active {
  background: #007bff;
  color: white;
  opacity: 1;
}


.actions {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.actions button {
  padding: 8px 12px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.actions button:disabled {
  background: #ccc;
  cursor: not-allowed;
}


table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background: #f8f9fa;
  font-weight: bold;
  cursor: pointer;
}

th span {
  margin-left: 5px;
  font-size: 12px;
  color: #555;
}

td input[type="checkbox"] {
  cursor: pointer;
}

td button {
  padding: 6px 10px;
  margin: 3px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s ease;
}

td button:first-child {
  margin-right: 8px;
}

td button.approve {
  background: #28a745;
  color: white;
}

td button.disable {
  background: #dc3545;
  color: white;
}

td button:disabled {
  background: #ccc;
  cursor: not-allowed;
}


p {
  font-style: italic;
  color: #666;
}


.search-bar {
  margin-bottom: 15px;
}

.search-bar input {
  padding: 8px;
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 5px;
}
</style>
