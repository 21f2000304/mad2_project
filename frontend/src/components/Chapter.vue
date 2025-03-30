<template>
  <div class="chapter-container">
    <div v-if="successMessage" class="alert success">{{ successMessage }}</div>
    <div v-if="errorMessage" class="alert error">{{ errorMessage }}</div>

    <div class="table-wrapper">
      <table class="chapter-table">
      <thead>
        <tr>
          <th class="wide-column">Name</th>
          <th>Total Questions</th>
          <th>No. of Quizzes</th>
          <th class="actions-column">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="chapter in filteredChapters" :key="chapter.id">
          <td v-html="highlightMatch(chapter.name, searchQuery)"></td>
          <td>{{ chapter.n_questions || 0 }}</td>
          <td>{{ chapter.n_quizzes || 0 }}</td>
          <td class="actions-cell">
            <button @click="editChapter(chapter)" class="edit-btn" title="Edit Chapter">✏️</button>
            <button @click="deleteChapter(chapter.id)" class="delete-btn" title="Delete Chapter">🗑️</button>
          </td>
        </tr>
      </tbody>
    </table>
    </div>

    <div class="add-chapter-container">
      <button @click="openAddChapterModal" class="add-chapter-btn" title="Add New Chapter">
        ➕ Add Chapter
      </button>
    </div>
  </div>

  <teleport to="body">
    <div v-if="showChapterModal" class="modal" @click.self="closeChapterModal">
      <div class="modal-content">
        <h3 class="modal-title">
          {{ isEditingChapter ? "✏️ Edit Chapter" : "➕ Add New Chapter" }}
        </h3>
        <div class="form-group">
          <label>Chapter Name</label>
          <input
            v-model="currentChapter.name"
            class="form-input"
            placeholder="Enter Chapter Name"
            required
          />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea
            v-model="currentChapter.description"
            class="form-textarea"
            placeholder="Enter Chapter Description"
          ></textarea>
        </div>
        <div class="button-group">
          <button @click="isEditingChapter ? updateChapter() : addChapter()" class="save-btn">
            {{ isEditingChapter ? "✅ Update" : "✅ Save" }}
          </button>
          <button @click="closeChapterModal" class="cancel-btn">❌ Cancel</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script>
import { ref, computed } from "vue";

export default {
  props: {
    chapters: { type: Array, required: true },
    subjectId: { type: Number, required: true },
    searchQuery: { type: String, default: "" }
  },
  emits: ["add-chapter", "edit-chapter", "delete-chapter"],
  setup(props, { emit }) {
    const showChapterModal = ref(false);
    const isEditingChapter = ref(false);
    const currentChapter = ref({ id: null, name: "", description: "", subject_id: props.subjectId });
    const successMessage = ref("");
    const errorMessage = ref("");

    const filteredChapters = computed(() => {
      return props.chapters.filter(chapter =>
        chapter.name.toLowerCase().includes(props.searchQuery.toLowerCase())
      );
    });

    const highlightMatch = (text, query) => {
      if (!text || !query) return text;
      const cleanQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const regex = new RegExp(`(${cleanQuery})`, "gi");
      return text.replace(regex, "<mark>$1</mark>");
    };

    const showMessage = (message, isError = false) => {
      if (isError) errorMessage.value = message;
      else successMessage.value = message;
      setTimeout(() => {
        successMessage.value = "";
        errorMessage.value = "";
      }, 3000);
    };

    const openAddChapterModal = () => {
      isEditingChapter.value = false;
      currentChapter.value = { id: null, name: "", description: "", subject_id: props.subjectId };
      showChapterModal.value = true;
    };

    const closeChapterModal = () => {
      showChapterModal.value = false;
    };

    const addChapter = () => {
      if (!currentChapter.value.name.trim()) {
        showMessage("Chapter name is required!", true);
        return;
      }
      const exists = props.chapters.some(
        ch => ch.name.toLowerCase() === currentChapter.value.name.trim().toLowerCase()
      );
      if (exists) {
        showMessage(`Chapter "${currentChapter.value.name}" already exists!`, true);
        return;
      }
      emit("add-chapter", { ...currentChapter.value });
      closeChapterModal();
    };

    const editChapter = (chapter) => {
      isEditingChapter.value = true;
      currentChapter.value = { ...chapter, description: chapter.description || "" };
      showChapterModal.value = true;
    };

    const updateChapter = () => {
      if (!currentChapter.value.name.trim()) {
        showMessage("Chapter name is required!", true);
        return;
      }
      const exists = props.chapters.some(
        ch => ch.id !== currentChapter.value.id &&
        ch.name.toLowerCase() === currentChapter.value.name.trim().toLowerCase()
      );
      if (exists) {
        showMessage(`Chapter "${currentChapter.value.name}" already exists!`, true);
        return;
      }
      emit("edit-chapter", { ...currentChapter.value });
      closeChapterModal();
    };

    const deleteChapter = (chapterId) => {
      emit("delete-chapter", chapterId);
    };

    return {
      showChapterModal,
      isEditingChapter,
      currentChapter,
      successMessage,
      errorMessage,
      filteredChapters,
      highlightMatch,
      openAddChapterModal,
      closeChapterModal,
      addChapter,
      editChapter,
      updateChapter,
      deleteChapter,
      showMessage
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

.chapter-container {
  width: 100%;
  margin: 0;
  padding: 0;
  border: none;
}


.table-wrapper {
  overflow-x: auto;
}

.chapter-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

@media (max-width: 800px) {
  .chapter-table {
    min-width: 600px;
  }
}

.chapter-table th,
.chapter-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
  font-size: 0.92rem;
}

.chapter-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

mark {
  background-color: #ffeb3b;
  color: #000;
  padding: 0 2px;
  border-radius: 3px;
}

.actions-cell {
  text-align: center;
}

.edit-btn,
.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  margin: 0 5px;
  font-size: 1.1rem;
}

.edit-btn:hover {
  color: #007bff;
}

.delete-btn:hover {
  color: #dc3545;
}

.add-chapter-container {
  margin-top: 15px;
  text-align: center;
}

.add-chapter-btn {
  background-color: #d2d44a;
  color: white;
  padding: 5px 10px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.add-chapter-btn:hover {
  background-color: #5d8305;
}


.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 15px;
}

.modal-content {
  background: white;
  padding: 20px 25px;
  border-radius: 8px;
  width: 400px;
  max-width: 90%;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
  z-index: 1001;
}

.modal-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 15px;
  text-align: center;
}


.form-group {
  margin-bottom: 15px;
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
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.save-btn {
  background-color: #28a745;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn {
  background-color: #dc3545;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}


.alert {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 15px 25px;
  border-radius: 8px;
  z-index: 1000;
  font-weight: 500;
}

.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}


@media (max-width: 600px) {
  .chapter-table th,
  .chapter-table td {
    font-size: 0.8rem;
  }
}
</style>
