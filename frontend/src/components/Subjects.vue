<template>
  <div class="subjects-container">

    <div v-if="successMessage" class="alert success">{{ successMessage }}</div>
    <div v-if="errorMessage" class="alert error">{{ errorMessage }}</div>


    <div class="add-subject-container">
      <button @click="openAddModal" class="add-btn">➕ Add Subject</button>
    </div>


    <div class="subjects-grid">
      <div v-for="subject in filteredSubjects" :key="subject.id" class="subject-card">

        <div class="subject-header">
          <h3 class="subject-name">{{ subject.name }}</h3>
          <div class="subject-actions">
            <button @click="editSubject(subject)" class="edit-btn" title="Edit Subject">✏️</button>
            <button @click="deleteSubject(subject.id)" class="delete-btn" title="Delete Subject">🗑️</button>
          </div>
        </div>

        <p class="subject-description">{{ subject.description }}</p>

        <Chapter
          :key="'chapter-' + subject.id + '-' + forceRenderKey"
          :chapters="subject.chapters || []"
          :subject-id="subject.id"
          :search-query="searchQuery"
          @add-chapter="handleAddChapter"
          @edit-chapter="handleEditChapter"
          @delete-chapter="handleDeleteChapter"
        />
      </div>
    </div>


    <div v-if="tooltip.visible" :style="tooltip.style" class="tooltip">
      {{ tooltip.text }}
    </div>


    <div v-if="showSubjectModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <button class="close-btn" @click="closeModal">&times;</button>
        <h3 class="modal-title">
          {{ isEditingSubject ? "✏️ Edit Subject" : "➕ Add New Subject" }}
        </h3>
        <div class="form-group">
          <label>Subject Name</label>
          <input v-model="currentSubject.name" class="form-input" required />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="currentSubject.description" class="form-textarea"></textarea>
        </div>
        <div class="button-group">
          <button @click="isEditingSubject ? updateSubject() : addSubject()" class="save-btn">
            {{ isEditingSubject ? "✅ Update" : "✅ Save" }}
          </button>
          <button @click="closeModal" class="cancel-btn">❌ Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from "vue";
import Chapter from "./Chapter.vue";

export default {
  components: { Chapter },
  props: {
    searchQuery: { type: String, default: "" }
  },
  setup(props) {
    const subjects = ref([]);
    const showSubjectModal = ref(false);
    const isEditingSubject = ref(false);
    const currentSubject = ref({ id: null, name: "", description: "" });
    const forceRenderKey = ref(0);
    const successMessage = ref("");
    const errorMessage = ref("");
    const isModalOpen = ref(false);
    const tooltip = ref({ text: "", visible: false, style: {} });

    const filteredSubjects = computed(() => {
      const term = props.searchQuery.toLowerCase().trim();
      if (!term) return subjects.value;
      return subjects.value.filter(subject => {
        const subjectMatch =
          subject.name.toLowerCase().includes(term) ||
          (subject.description && subject.description.toLowerCase().includes(term));
        const chapterMatch = (subject.chapters || []).some(chapter =>
          chapter.name.toLowerCase().includes(term)
        );
        return subjectMatch || chapterMatch;
      });
    });

    const showMessage = (message, isError = false) => {
      if (isError) errorMessage.value = message;
      else successMessage.value = message;
      setTimeout(() => {
        successMessage.value = "";
        errorMessage.value = "";
      }, 3000);
    };

    const showTooltip = (text, event) => {
      tooltip.value = {
        text,
        visible: true,
        style: { top: `${event.clientY + 10}px`, left: `${event.clientX + 10}px` }
      };
    };

    const hideTooltip = () => { tooltip.value.visible = false; };

    const fetchSubjects = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:5000/api/subject", {
          headers: { Authorization: `Bearer ${token}` }
        });
        subjects.value = await response.json();
      } catch (error) {
        showMessage("Failed to fetch subjects", true);
      }
    };

    const openAddModal = () => {
      isEditingSubject.value = false;
      currentSubject.value = { id: null, name: "", description: "" };
      showSubjectModal.value = true;
      isModalOpen.value = true;
    };

    const closeModal = () => {
      showSubjectModal.value = false;
      isModalOpen.value = false;
    };

    watch(isModalOpen, (newVal) => {
      if (newVal) document.body.classList.add("modal-open");
      else document.body.classList.remove("modal-open");
    });

    const addSubject = async () => {
      const newSub = currentSubject.value;
      if (!newSub.name.trim()) {
        showMessage("Subject name is required!", true);
        return;
      }
      const exists = subjects.value.some(
        s => s.name.toLowerCase() === newSub.name.trim().toLowerCase()
      );
      if (exists) {
        showMessage(`Subject "${newSub.name}" already exists!`, true);
        return;
      }
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:5000/api/subject", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(newSub)
        });
        const data = await response.json();
        if (response.ok) {
          subjects.value.push({ ...data.subject, chapters: [] });
          forceRenderKey.value++;
          showMessage(`Subject "${newSub.name}" added successfully!`);
          closeModal();
        } else {
          showMessage(data.error || "Failed to add subject", true);
        }
      } catch (error) {
        showMessage("Failed to add subject", true);
      }
    };

    const editSubject = (subject) => {
      isEditingSubject.value = true;
      currentSubject.value = { ...subject };
      showSubjectModal.value = true;
      isModalOpen.value = true;
    };

    const updateSubject = async () => {
      const updatedSub = currentSubject.value;
      if (!updatedSub.name.trim()) {
        showMessage("Subject name is required!", true);
        return;
      }
      const exists = subjects.value.some(
        s => s.id !== updatedSub.id && s.name.toLowerCase() === updatedSub.name.trim().toLowerCase()
      );
      if (exists) {
        showMessage(`Subject "${updatedSub.name}" already exists!`, true);
        return;
      }
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost:5000/api/subject/${updatedSub.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(updatedSub)
        });
        const data = await response.json();
        if (response.ok) {
          subjects.value = subjects.value.map(subject => {
            if (subject.id === data.subject.id) {
              return { ...data.subject, chapters: subject.chapters || [] };
            }
            return subject;
          });
          forceRenderKey.value++;
          showMessage(`Subject "${updatedSub.name}" updated successfully!`);
          closeModal();
        } else {
          showMessage(data.error || "Failed to update subject", true);
        }
      } catch (error) {
        showMessage("Failed to update subject", true);
      }
    };

    const deleteSubject = async (id) => {
      const sub = subjects.value.find(s => s.id === id);
      if (!sub || !confirm(`Delete subject "${sub.name}"?`)) return;
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost:5000/api/subject/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          subjects.value = subjects.value.filter(s => s.id !== id);
          forceRenderKey.value++;
          showMessage(`Subject "${sub.name}" deleted successfully!`);
        } else {
          const errData = await response.json();
          showMessage(errData.error || "Failed to delete subject", true);
        }
      } catch (error) {
        showMessage("Failed to delete subject", true);
      }
    };


    const handleAddChapter = async (chapterData) => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:5000/api/chapter", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(chapterData)
        });
        const data = await response.json();
        if (response.ok) {
          const subjectIndex = subjects.value.findIndex(s => s.id === chapterData.subject_id);
          if (subjectIndex !== -1) {
            subjects.value[subjectIndex].chapters = [
              ...subjects.value[subjectIndex].chapters,
              data.chapter
            ];
          }
          showMessage(`Chapter "${data.chapter.name}" added successfully!`);
        } else {
          showMessage(data.error || "Failed to add chapter", true);
        }
      } catch (error) {
        showMessage("Failed to add chapter", true);
      }
    };

    const handleEditChapter = async (chapterData) => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost:5000/api/chapter/${chapterData.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            name: chapterData.name,
            subject_id: chapterData.subject_id,
            description: chapterData.description
          })
        });
        const data = await response.json();
        if (response.ok) {
          await fetchSubjects(); 
          forceRenderKey.value++;

          showMessage(`Chapter "${data.chapter.name}" updated successfully!`);
        } else {
          showMessage(data.error || "Failed to update chapter", true);
        }
      } catch (error) {
        showMessage("Failed to update chapter", true);
      }
    };

    const handleDeleteChapter = async (chapterId) => {
      if (!confirm("Are you sure you want to delete this chapter?")) return;
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(`http://localhost:5000/api/chapter/${chapterId}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          subjects.value.forEach(subject => {
            subject.chapters = subject.chapters.filter(ch => ch.id !== chapterId);
          });
          showMessage("Chapter deleted successfully!");
        } else {
          const errData = await response.json();
          showMessage(errData.error || "Failed to delete chapter", true);
        }
      } catch (error) {
        showMessage("Failed to delete chapter", true);
      }
    };

    onMounted(fetchSubjects);

    return {
      subjects,
      showSubjectModal,
      isEditingSubject,
      currentSubject,
      forceRenderKey,
      successMessage,
      errorMessage,
      openAddModal,
      addSubject,
      editSubject,
      updateSubject,
      deleteSubject,
      tooltip,
      showTooltip,
      hideTooltip,
      filteredSubjects,
      closeModal,
      handleAddChapter,
      handleEditChapter,
      handleDeleteChapter
    };
  }
};
</script>

<style scoped>

*,
*::before,
*::after {
  box-sizing: border-box;
}


body, html {
  width: 100%;
  max-width: 100%;
  overflow-x: hidden;
}


.subjects-container {
  max-width: 100%;
  overflow-x: hidden;
  padding: 20px;
}


.add-subject-container {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 5px;
}

.add-btn {
  background-color: #28a745;
  color: white;
  padding: 10px 15px;
  border-radius: 5px;
  border: none;
  cursor: pointer;
  font-weight: bold;
  transition: background 0.3s ease;
}

.add-btn:hover {
  background-color: #218838;
}

.subjects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  width: 100%;
  padding: 10px;
  margin: 0 auto;
}


.subject-card {
  position: relative;
  text-align: center;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
  overflow: hidden;
  width: 100%;
  max-width: 100%;
}


.subject-card:hover {
  transform: translateY(-5px);
}


.subject-header {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  margin-bottom: 0.5rem;
}
.subject-name {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
  font-weight: bold;
}


.subject-description {
  margin: 4px 0 12px 0;
  color: #666;
  font-size: 0.9rem;
  line-height: 1.4;
  padding: 0 20px;
}


.subject-actions {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  gap: 8px;
}
.edit-btn,
.delete-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 5px;
  transition: color 0.3s ease;
}
.edit-btn:hover {
  color: #007bff;
}
.delete-btn:hover {
  color: #dc3545;
}


.tooltip {
  position: fixed;
  background-color: rgba(0, 0, 0, 0.75);
  color: white;
  padding: 5px 10px;
  border-radius: 5px;
  font-size: 14px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 1000;
}


.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 15px; 
}


.modal {
  background: white;
  padding: 20px 25px;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  z-index: 1001;
  width: 400px;
  max-width: 90%;
}
.modal-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 15px;
  text-align: center;
}


.form-group {
  margin-bottom: 15px;
  text-align: left;
}
.form-group label {
  font-size: 0.9rem;
  font-weight: bold;
  color: #555;
  display: block;
  margin-bottom: 5px;
}
.form-input,
.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s ease;
  box-sizing: border-box;
}
.form-input:focus,
.form-textarea:focus {
  border-color: #007bff;
}
.form-textarea {
  min-height: 80px;
  resize: vertical;
}


.button-group {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
}
.save-btn,
.cancel-btn {
  flex: 1;
  padding: 10px;
  font-size: 1rem;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s ease;
}
.save-btn {
  background: #28a745;
  color: white;
  margin-right: 10px;
}
.save-btn:hover {
  background: #218838;
}
.cancel-btn {
  background: #dc3545;
  color: white;
}
.cancel-btn:hover {
  background: #c82333;
}

.alert {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  max-width: 400px;
  padding: 15px 25px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  text-align: center;
}
.success {
  background: #4CAF50;
  color: white;
}
.error {
  background: #f44336;
  color: white;
}

body.modal-open {
  overflow: hidden;
}

.subject-card .chapter-container {
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
}
</style>
