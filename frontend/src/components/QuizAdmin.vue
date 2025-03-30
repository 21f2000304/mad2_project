<template>
  <div class="quiz-admin">
    <div class="header">
      <h2 class="title">Manage Quizzes</h2>
      <div class="header-controls">
        <div class="filter-tabs">
          <button 
            @click="filterCategory('all')"
            :class="{ active: currentFilter === 'all' }"
          >
            All
          </button>
          <button 
            @click="filterCategory('upcoming')"
            :class="{ active: currentFilter === 'upcoming' }"
          >
            Upcoming
          </button>
          <button 
            @click="filterCategory('active')"
            :class="{ active: currentFilter === 'active' }"
          >
            Active
          </button>
          <button 
            @click="filterCategory('expired')"
            :class="{ active: currentFilter === 'expired' }"
          >
            Expired
          </button>
        </div>
        <button class="add-btn" @click="openAddForm">➕ Add Quiz</button>
      </div>
    </div>

    <div class="quiz-list">
      <div v-if="quizzes === null">Loading quizzes...</div>
      <div v-else-if="filteredQuizzes.length === 0">No quizzes match the selected filter.</div>
      <div v-else class="quiz-cards">
        <div 
          v-for="quiz in filteredQuizzes" 
          :key="quiz.id" 
          class="quiz-card"
          :class="getQuizStatusClass(quiz)"
        >
          <button class="add-questions-btn" 
                  @click="openQuestionWindow(quiz)"
                  @mouseover="showTooltip('Manage Questions', $event)"
                  @mouseleave="hideTooltip">
            Questions
          </button>
          <h3>{{ quiz?.title || 'Untitled Quiz' }}</h3>
          <p><strong>Subject:</strong> {{ getSubjectNameFromQuiz(quiz) || 'Unknown' }}</p>
          <p><strong>Chapter:</strong> {{ getChapterName(quiz?.chapter_id) || 'Unknown' }}</p>
          <p><strong>Total Questions:</strong> {{ quiz?.num_questions || 0 }}</p>
          <p><strong>Date of Quiz:</strong> {{ formatDate(quiz?.date_of_quiz) }}</p>
          <p><strong>Last Date:</strong> {{ formatDate(quiz?.last_date) }}</p>
          <p><strong>Duration:</strong> {{ quiz?.time_duration || 'N/A' }}</p>
          <p><strong>Remarks:</strong> {{ quiz?.remarks || 'None' }}</p>
          <p><strong>Status:</strong> <span :class="getQuizStatusClass(quiz)">{{ getQuizStatus(quiz) }}</span></p>
          <div class="card-actions">
            <button class="edit-btn" @click="openEditForm(quiz)"
                    @mouseover="showTooltip('Edit Quiz', $event)"
                    @mouseleave="hideTooltip">
              ✏️
            </button>
            <button class="delete-btn" @click="confirmDelete(quiz)"
                    @mouseover="showTooltip('Delete Quiz', $event)"
                    @mouseleave="hideTooltip">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>


    <div v-if="tooltip.visible" :style="tooltip.style" class="tooltip">
      {{ tooltip.text }}
    </div>


    <div v-if="showAddForm" class="modal-overlay">
      <div class="modal">
        <h3>{{ editMode ? '✏️ Edit Quiz' : '➕ Add New Quiz' }}</h3>
        <form @submit.prevent="handleSubmit">
          <div class="form-grid">
            <div class="form-group">
              <label>Title:</label>
              <input type="text" v-model="newQuiz.title" placeholder="Enter Quiz Title" required />
            </div>
            <div class="form-group">
              <label>Date of Quiz:</label>
              <input type="date" v-model="newQuiz.date_of_quiz" required />
            </div>
            <div class="form-group">
              <label>Last Date:</label>
              <input type="date" v-model="newQuiz.last_date" required />
            </div>
            <div class="form-group">
              <label>Subject:</label>
              <select v-model="newQuiz.subject_id" @change="fetchFilteredChapters" required>
                <option value="" disabled>Select Subject</option>
                <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
                  {{ subject.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Duration:</label>
              <input type="time" v-model="newQuiz.time_duration" required />
            </div>
            <div class="form-group">
              <label>Chapter:</label>
              <select v-model="newQuiz.chapter_id" :disabled="filteredChapters.length === 0" required>
                <option value="" disabled>Select Chapter</option>
                <option v-for="chapter in filteredChapters" :key="chapter.id" :value="chapter.id">
                  {{ chapter.name }}
                </option>
              </select>
            </div>
            <div class="form-group full-width">
              <label>Remarks:</label>
              <textarea v-model="newQuiz.remarks" placeholder="Enter remarks"></textarea>
            </div>
          </div>
          <div class="form-actions">
            <button type="submit">{{ editMode ? '✅ Update' : '✅ Save' }}</button>
            <button type="button" @click="closeForm">❌ Cancel</button>
          </div>
        </form>
      </div>
    </div>
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
      quizzes: null,
      subjects: [],
      chapters: [],
      filteredChapters: [],
      showAddForm: false,
      editMode: false,
      newQuiz: { 
        title: "", 
        subject_id: "", 
        chapter_id: "", 
        date_of_quiz: "",
        last_date: "", 
        time_duration: "01:00", 
        remarks: "" 
      },
      editingQuizId: null,
      tooltip: {
        visible: false,
        text: "",
        style: {}
      },
      currentFilter: 'all'
    };
  },
  mounted() {
    this.fetchQuizzes();
    this.fetchSubjects();
    this.fetchAllChapters();
    window.addEventListener('message', this.handleMessage);
  },
  beforeDestroy() {
    window.removeEventListener('message', this.handleMessage);
  },
  computed: {
  filteredQuizzes() {
    if (!this.quizzes) return [];
    
    let filtered = [];
    const parseDate = (dateString) => {
      const datePart = dateString.split('T')[0];
      const [year, month, day] = datePart.split('-').map(Number);
      return new Date(year, month - 1, day);
    };

    const now = new Date();
    
    switch (this.currentFilter) {
      case 'upcoming':
        filtered = this.quizzes.filter(quiz => {
          if (!quiz.date_of_quiz) return false;
          const startDate = parseDate(quiz.date_of_quiz);
          return now < startDate;
        });
        break;
      case 'active':
        filtered = this.quizzes.filter(quiz => {
            if (!quiz.date_of_quiz || !quiz.last_date) return false;
            const startDate = parseDate(quiz.date_of_quiz);
            const endDate = parseDate(quiz.last_date);
            endDate.setHours(23, 59, 59, 999); // End of day
            return now >= startDate && now <= endDate;
        });
        break;
      case 'expired':
        filtered = this.quizzes.filter(quiz => {
            if (!quiz.last_date) return false;
            const endDate = parseDate(quiz.last_date);
            endDate.setHours(23, 59, 59, 999);
            return now > endDate;
          });
          break;
      default:
        filtered = this.quizzes;
        break;
    }

    const searchTerm = this.searchQuery?.toLowerCase().trim();
    if (!searchTerm) return filtered;

    return filtered.filter(quiz => {
      const quizTitle = quiz.title?.toLowerCase() || '';
      const subjectName = this.getSubjectNameFromQuiz(quiz)?.toLowerCase() || '';
      const chapterName = this.getChapterName(quiz.chapter_id)?.toLowerCase() || '';
      const questions = quiz.questions || [];
      const questionTexts = quiz.questions?.map(q => (q.text || '').toLowerCase()) || [];
      const hasMatchingQuestion = questionTexts.some(text => text.includes(searchTerm));
      
      return quizTitle.includes(searchTerm) ||
             subjectName.includes(searchTerm) ||
             chapterName.includes(searchTerm) ||
             hasMatchingQuestion;
    });
  }
},
  methods: {
    getAuthHeaders() {
      const token = localStorage.getItem("token");
      return token
        ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
        : { "Content-Type": "application/json" };
    },
    
    async fetchQuizzes() {
      try {
        const response = await fetch("http://localhost:5000/api/quiz", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        this.quizzes = await response.json();
      } catch (error) {
        console.error("Error fetching quizzes:", error);
        this.quizzes = [];
      }
    },
    openQuestionWindow(quiz) {
      const quizTitle = quiz.title || "Unknown Quiz";
      const chapterName = this.getChapterName(quiz.chapter_id);
      const url = `/admin/question-create/${quiz.id}?quizTitle=${encodeURIComponent(quizTitle)}&chapterName=${encodeURIComponent(chapterName)}`;
      
      const questionWindow = window.open(url, '_blank');
      
      const checkWindowClosed = setInterval(() => {
        if (questionWindow.closed) {
          clearInterval(checkWindowClosed);
          this.fetchQuizzes();
        }
      }, 500);
    },
    handleMessage(event) {
      if (event.origin !== window.location.origin) return;
      if (event.data === 'questions-updated') {
        this.fetchQuizzes();
      }
    },
    
    async fetchSubjects() {
      try {
        const response = await fetch("http://localhost:5000/api/subject", {
          method: "GET",
          headers: this.getAuthHeaders(),
          credentials: "include",
        });
        if (!response.ok) throw new Error("Failed to fetch subjects");
        this.subjects = await response.json();
      } catch (error) {
        console.error("Error fetching subjects:", error);
      }
    },
    
    async fetchAllChapters() {
      try {
        const response = await fetch("http://localhost:5000/api/chapter", {
          method: "GET",
          headers: this.getAuthHeaders(),
          credentials: "include",
        });
        if (!response.ok) throw new Error("Failed to fetch chapters");
        this.chapters = await response.json();
      } catch (error) {
        console.error("Error fetching chapters:", error);
      }
    },
    
    async fetchFilteredChapters() {
      if (!this.newQuiz.subject_id) {
        this.filteredChapters = [];
        return;
      }
      try {
        const response = await fetch(
          `http://localhost:5000/api/chapter?subject_id=${this.newQuiz.subject_id}`,
          {
            method: "GET",
            headers: this.getAuthHeaders(),
            credentials: "include",
          }
        );
        if (!response.ok) throw new Error("Failed to fetch filtered chapters");
        this.filteredChapters = await response.json();
      } catch (error) {
        console.error("Error fetching filtered chapters:", error);
      }
    },
    
    getChapterName(chapter_id) {
      if (!chapter_id) return "Unknown";
      const chapter = this.chapters.find(c => c.id === chapter_id);
      return chapter ? chapter.name : "Unknown";
    },
    
    getSubjectNameFromQuiz(quiz) {
      if (!quiz?.chapter_id) return "Unknown";
      const chapter = this.chapters.find(c => c.id === quiz.chapter_id);
      if (!chapter) return "Unknown";
      const subject = this.subjects.find(s => s.id === chapter.subject_id);
      return subject ? subject.name : "Unknown";
    },
    
    formatDate(dateStr) {
      if (!dateStr) return "N/A";
      try {
        const dateObj = new Date(dateStr);
        return dateObj.toLocaleDateString();
      } catch {
        return "Invalid Date";
      }
    },
    
    openAddForm() {
      this.editMode = false;
      this.editingQuizId = null;
      
      let currentDate = new Date();
      let lastDate = new Date();
      lastDate.setDate(lastDate.getDate() + 7);

      this.newQuiz = { 
        title: `Quiz ${(this.quizzes?.length || 0) + 1}`,
        subject_id: "", 
        chapter_id: "", 
        date_of_quiz: currentDate.toISOString().split('T')[0],
        last_date: lastDate.toISOString().split('T')[0],
        time_duration: "01:00", 
        remarks: "" 
      };
      this.filteredChapters = [];
      this.showAddForm = true;
    },
    
    openEditForm(quiz) {
      if (!quiz) return;
      
      this.editMode = true;
      this.editingQuizId = quiz.id;
      this.newQuiz = { 
        title: quiz.title || "", 
        subject_id: this.getSubjectIdFromQuiz(quiz), 
        chapter_id: quiz.chapter_id || "", 
        date_of_quiz: quiz.date_of_quiz ? quiz.date_of_quiz.split("T")[0] : "", 
        last_date: quiz.last_date ? quiz.last_date.split("T")[0] : "",
        time_duration: quiz.time_duration || "01:00", 
        remarks: quiz.remarks || "" 
      };
      this.fetchFilteredChapters();
      this.showAddForm = true;
    },
    
    getSubjectIdFromQuiz(quiz) {
      if (!quiz?.chapter_id) return "";
      const chapter = this.chapters.find(c => c.id === quiz.chapter_id);
      return chapter ? chapter.subject_id : "";
    },
    
    validateUniqueTitle() {
      const newTitle = this.newQuiz.title.trim();
      if (!newTitle) return false;
      
      if (this.editMode) {
        return !this.quizzes?.some(q => 
          q.id !== this.editingQuizId && 
          q.title?.trim().toLowerCase() === newTitle.toLowerCase()
        );
      }
      return !this.quizzes?.some(q => 
        q.title?.trim().toLowerCase() === newTitle.toLowerCase()
      );
    },
    
    async handleSubmit() {
      try {
        const url = this.editMode 
          ? `http://localhost:5000/api/quiz/${this.editingQuizId}`
          : "http://localhost:5000/api/quiz";
        
        const method = this.editMode ? "PUT" : "POST";
        
        const response = await fetch(url, {
          method,
          headers: this.getAuthHeaders(),
          body: JSON.stringify(this.newQuiz),
          credentials: "include"
        });
        
        if (response.ok) {
          await this.fetchQuizzes();
          this.closeForm();
        }
      } catch (error) {
        console.error("Error saving quiz:", error);
      }
    },
    
    confirmDelete(quiz) {
      if (!quiz?.id) return;
      if (confirm(`Are you sure you want to delete "${quiz.title || 'this quiz'}"?`)) {
        this.deleteQuiz(quiz.id);
      }
    },
    
    async deleteQuiz(quizId) {
      try {
        const response = await fetch(`http://localhost:5000/api/quiz/${quizId}`, {
          method: "DELETE",
          headers: this.getAuthHeaders(),
          credentials: "include",
        });
        
        if (!response.ok) throw new Error("Failed to delete quiz");
        this.fetchQuizzes();
      } catch (error) {
        console.error("Error deleting quiz:", error);
        alert("Failed to delete quiz. Please try again.");
      }
    },
    
    openQuestionWindow(quiz) {
      if (!quiz?.id) return;
      
      const quizTitle = quiz.title || "Unknown Quiz";
      const chapterName = this.getChapterName(quiz.chapter_id);
      const url = `/admin/question-create/${quiz.id}?quizTitle=${encodeURIComponent(quizTitle)}&chapterName=${encodeURIComponent(chapterName)}`;
      window.open(url, '_blank', 'width=900,height=660');
    },
    
    closeForm() {
      this.showAddForm = false;
      this.editMode = false;
      this.editingQuizId = null;
      this.newQuiz = { 
        title: "", 
        subject_id: "", 
        chapter_id: "", 
        date_of_quiz: "", 
        last_date: "",
        time_duration: "01:00", 
        remarks: "" 
      };
      this.filteredChapters = [];
    },
    
    showTooltip(text, event) {
      this.tooltip = {
        text: text,
        visible: true,
        style: {
          top: `${event.clientY + 10}px`,
          left: `${event.clientX + 10}px`
        }
      };
    },
    
    hideTooltip() {
      this.tooltip.visible = false;
    },
    
    getQuizStatus(quiz) {
  if (!quiz || !quiz.date_of_quiz || !quiz.last_date) return 'Unknown';

  const parseDate = (dateString) => {
    const datePart = dateString.split('T')[0];
    const [year, month, day] = datePart.split('-').map(Number); 
    return new Date(year, month - 1, day); 
  };

  const now = new Date();
  const startDate = parseDate(quiz.date_of_quiz);
  const endDate = parseDate(quiz.last_date);

  endDate.setHours(23, 59, 59, 999);

  if (now < startDate) {
    return 'Upcoming';
  } else if (now > endDate) {
    return 'Expired';
  } else {
    return 'Active';
  }
},
    
    getQuizStatusClass(quiz) {
      const status = this.getQuizStatus(quiz).toLowerCase();
      return {
        'upcoming-status': status === 'upcoming',
        'active-status': status === 'active',
        'expired-status': status === 'expired',
        'unknown-status': status === 'unknown'
      };
    },
    
    filterCategory(category) {
      this.currentFilter = category;
    }
  }
};
</script>

<style scoped>
.quiz-admin {
  padding: 20px 30px; 
  max-width: 1600px;
  margin: 0 auto;
}

.header {
  display: flex;
  flex-direction: column;
  gap: 15px; 
  margin-bottom: 20px;
}

.title {
  font-size: 2rem;
  text-align: center;
  color: #2c3e50;
  margin: 10px 0;
}

.header-controls {
  display: flex;
  justify-content: flex-start; 
  width: 100%;
  gap: 20px;
}

.filter-tabs {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-right: auto;
}

.add-btn {
  background-color: #28a745;
  color: #fff;
  padding: 10px 20px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1rem;
  font-weight: 500;
}

.add-btn:hover {
  background-color: #218838;
  transform: translateY(-1px);
}

.filter-tabs button {
  padding: 10px 20px;
  border: 2px solid #ddd;
  background: #616185;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
  font-size: 0.95rem;
}

.filter-tabs button:hover {
  background: #838bd4;
  transform: translateY(-1px);
}

.filter-tabs button.active {
  background: #3498db;
  border-color: #3498db;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.quiz-list {
  margin-top: 30px;
}

.quiz-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 300px));
  gap: 30px;
  justify-content: center;
}

.quiz-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  width: 300px;
  min-height: 380px;
  box-sizing: border-box;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 6px rgba(0,0,0,0.08);
  display: flex;
  flex-direction: column;
}

.quiz-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0,0,0,0.12);
}

.quiz-card h3 {
  margin: 15px 0 20px;
  font-size: 1.3rem;
  color: #2c3e50;
  line-height: 1.4;
  font-weight: 600;
}

.quiz-card p {
  margin: 8px 0;
  font-size: 1rem;
  color: #444;
  line-height: 1.5;
}

.quiz-card p strong {
  color: #333;
  font-weight: 500;
}

.quiz-card.upcoming {
  border-left: 6px solid #f39c12;
}

.quiz-card.active {
  border-left: 6px solid #2ecc71;
}

.quiz-card.expired {
  border-left: 6px solid #e74c3c;
}

.add-questions-btn {
  background-color: #007bff;
  color: #fff;
  padding: 8px 15px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  position: absolute;
  top: 15px;
  right: 15px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-questions-btn:hover {
  background-color: #0056b3;
  transform: scale(1.05);
}

.card-actions {
  margin-top: auto;
  display: flex;
  gap: 15px;
  padding-top: 20px;
  justify-content: flex-start;
}

.edit-btn, .delete-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.5rem;
  transition: all 0.3s ease;
  padding: 6px;
  border-radius: 50%;
}

.edit-btn:hover {
  color: #007bff;
  transform: scale(1.1);
}

.delete-btn:hover {
  color: #dc3545;
  transform: scale(1.1);
}

/* Status text classes */
.upcoming-status {
  color: #f39c12;
  font-weight: 600;
}

.active-status {
  color: #2ecc71;
  font-weight: 600;
}

.expired-status {
  color: #e74c3c;
  font-weight: 600;
}

.unknown-status {
  color: #95a5a6;
  font-weight: 600;
}


@media (min-width: 1200px) {
  .quiz-cards {
    grid-template-columns: repeat(4, 300px);
  }
}

@media (max-width: 1199px) and (min-width: 992px) {
  .quiz-cards {
    grid-template-columns: repeat(3, 300px);
  }
}

@media (max-width: 991px) and (min-width: 768px) {
  .quiz-cards {
    grid-template-columns: repeat(2, 300px);
  }
}

@media (max-width: 767px) {
  .quiz-cards {
    grid-template-columns: 1fr;
  }
  .quiz-card {
    width: 100%;
    min-height: auto;
  }
  .title {
    font-size: 1.6rem;
  }
  .header-controls {
    flex-direction: column;
  }
}


.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 25px;
  border-radius: 12px;
  max-width: 650px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-group {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
}

.form-group.full-width {
  grid-column: span 2;
}

.form-group label {
  font-weight: 500;
  margin-bottom: 8px;
  color: #444;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 6px;
  box-sizing: border-box;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #3498db;
  outline: none;
}

.form-actions {
  margin-top: 25px;
  display: flex;
  justify-content: flex-end;
  gap: 15px;
}

.form-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
  font-weight: 500;
}

.form-actions button[type="submit"] {
  background: #28a745;
  color: #fff;
}

.form-actions button[type="submit"]:hover {
  background: #218838;
  transform: translateY(-1px);
}

.form-actions button[type="button"] {
  background: #dc3545;
  color: #fff;
}

.form-actions button[type="button"]:hover {
  background: #c82333;
  transform: translateY(-1px);
}


.tooltip {
  position: fixed;
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 8px 15px;
  border-radius: 6px;
  font-size: 0.9rem;
  z-index: 1000;
  pointer-events: none;
  white-space: nowrap;
  transition: opacity 0.2s ease;
}
</style>