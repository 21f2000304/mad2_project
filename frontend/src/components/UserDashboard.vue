<template>
  <div class="quiz-user">
    <div class="header">
      <h2 class="title">Take Your Quiz</h2>
      <div class="header-controls">
        <div class="filter-tabs">
          <button 
            @click="filterCategory('all')"
            :class="{ active: currentFilter === 'all' }"
          >All</button>
          <button 
            @click="filterCategory('active')"
            :class="{ active: currentFilter === 'active' }"
          >Active</button>
          <button 
            @click="filterCategory('upcoming')"
            :class="{ active: currentFilter === 'upcoming' }"
          >Upcoming</button>
          <button 
            @click="filterCategory('expired')"
            :class="{ active: currentFilter === 'expired' }"
          >Expired</button>
        </div>
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
          :class="[getQuizStatusClass(quiz), { 'quiz-taken': quiz.submission }]"
        >
          <h3>{{ quiz?.title || 'Untitled Quiz' }}</h3>
          <p><strong>Subject:</strong> {{ getSubjectNameFromQuiz(quiz) || 'Unknown' }}</p>
          <p><strong>Chapter:</strong> {{ getChapterName(quiz?.chapter_id) || 'Unknown' }}</p>
          <p><strong>Total Questions:</strong> {{ quiz?.num_questions || 0 }}</p>
          <p><strong>Date of Quiz:</strong> {{ formatDate(quiz?.date_of_quiz) }}</p>
          <p><strong>Last Date:</strong> {{ formatDate(quiz?.last_date) }}</p>
          <p><strong>Duration:</strong> {{ quiz?.time_duration || 'N/A' }}</p>
          <p>
            <strong>Status:</strong> 
            <span :class="getQuizStatusClass(quiz)">{{ getQuizStatus(quiz) }}</span>
          </p>
          <div class="card-actions">
            <button 
              v-if="getQuizStatus(quiz) === 'Active' && !quiz.submission" 
              class="take-quiz-btn"
              @click="startQuiz(quiz)"
            >Take Quiz</button>
            <button 
              v-if="quiz.submission" 
              class="check-result-btn"
              @click="openCheckResult(quiz)"
            >Check Result</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-if="showScorePopup" class="modal-overlay">
    <div class="modal">
      <h2>Quiz Submitted</h2>
      <p>Your Score: {{ scorePopup.score }} / {{ scorePopup.total }}</p>
      <button @click="closeScorePopup">Close</button>
    </div>
  </div>
  <div v-if="showResultModal" class="modal-overlay">
    <div class="modal">
      <h2>Quiz Result: {{ currentQuiz.title }}</h2>
      <p>Score: {{ currentSubmission.score }} / {{ currentSubmission.total_questions }}</p>
      <div class="result-list">
        <div 
          v-for="(item, index) in currentSubmission.answers" 
          :key="item.question_id" 
          class="result-item"
        >
          <p><strong>Question {{ index + 1 }}:</strong> {{ getQuestionText(item.question_id) }}</p>
          <p>
            <strong>Your Answer:</strong>
            <span 
              :class="{
                'correct': item.selected_option === getQuestionCorrectOption(item.question_id),
                'incorrect': item.selected_option !== getQuestionCorrectOption(item.question_id)
              }"
            >
              {{ getOptionLabel(item.selected_option, item.question_id) }}
            </span>
          </p>
          <p v-if="item.selected_option !== getQuestionCorrectOption(item.question_id)">
            <strong>Correct Answer:</strong> {{ getOptionLabel(getQuestionCorrectOption(item.question_id), item.question_id) }}
          </p>
        </div>
      </div>
      <button @click="showResultModal = false">Close</button>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    searchQuery: { type: String, default: "" }
  },
  data() {
    return {
      quizzes: null,
      subjects: [],
      chapters: [],
      currentFilter: "active",
      showResultModal: false,
      currentSubmission: null,
      currentQuiz: null,
      showScorePopup: false,
      scorePopup: { score: 0, total: 0 }
    };
  },
  computed: {
    filteredQuizzes() {
      if (!this.quizzes) return [];
      let filtered = [];
      const parseDate = (dateString) => {
        const datePart = dateString.split("T")[0];
        const [year, month, day] = datePart.split("-").map(Number);
        return new Date(year, month - 1, day);
      };
      const now = new Date();
      switch (this.currentFilter) {
        case "upcoming":
          filtered = this.quizzes.filter(quiz => {
            if (!quiz.date_of_quiz) return false;
            const startDate = parseDate(quiz.date_of_quiz);
            return now < startDate;
          });
          break;
        case "active":
          filtered = this.quizzes.filter(quiz => {
            if (!quiz.date_of_quiz || !quiz.last_date) return false;
            const startDate = parseDate(quiz.date_of_quiz);
            const endDate = parseDate(quiz.last_date);
            endDate.setHours(23, 59, 59, 999);
            return now >= startDate && now <= endDate;
          });
          break;
        case "expired":
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
      if (searchTerm) {
        filtered = filtered.filter(quiz => {
          const quizTitle = quiz.title?.toLowerCase() || "";
          const subjectName = this.getSubjectNameFromQuiz(quiz)?.toLowerCase() || "";
          const chapterName = this.getChapterName(quiz.chapter_id)?.toLowerCase() || "";
          const questionTexts = quiz.questions?.map(q => (q.question_statement || "").toLowerCase()) || [];
          const hasMatchingQuestion = questionTexts.some(text => text.includes(searchTerm));
          return (
            quizTitle.includes(searchTerm) ||
            subjectName.includes(searchTerm) ||
            chapterName.includes(searchTerm) ||
            hasMatchingQuestion
          );
        });
      }
      return filtered;
    }
  },
  methods: {
    async fetchQuizzes() {
      try {
        const response = await fetch("http://localhost:5000/api/quiz", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        let quizzes = await response.json();
        await Promise.all(
          quizzes.map(async quiz => {
            const submissionResponse = await fetch(`http://localhost:5000/api/submit-quiz?quiz_id=${quiz.id}`, {
              headers: this.getAuthHeaders()
            });
            const submissionData = await submissionResponse.json();
            quiz.submission = (submissionData && submissionData.length > 0) ? submissionData[0] : null;
            if (quiz.submission) {
              const questionsResponse = await fetch(`http://localhost:5000/api/quiz-questions?quiz_id=${quiz.id}`, {
                headers: this.getAuthHeaders()
              });
              const questionData = await questionsResponse.json();
              quiz.questions = questionData;
            } else {
              quiz.questions = [];
            }
            console.log(`Quiz ${quiz.id} submission:`, quiz.submission);
          })
        );
        this.quizzes = quizzes;
      } catch (error) {
        console.error("Error fetching quizzes:", error);
        this.quizzes = [];
      }
    },
    async fetchSubjects() {
      try {
        const response = await fetch("http://localhost:5000/api/subject", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        this.subjects = await response.json();
      } catch (error) {
        console.error("Error fetching subjects:", error);
      }
    },
    async fetchAllChapters() {
      try {
        const response = await fetch("http://localhost:5000/api/chapter", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        this.chapters = await response.json();
      } catch (error) {
        console.error("Error fetching chapters:", error);
      }
    },
    getAuthHeaders() {
      const token = localStorage.getItem("token");
      return { 
        Authorization: `Bearer ${token}`, 
        "Content-Type": "application/json" 
      };
    },
    getChapterName(chapter_id) {
      const chapter = this.chapters.find(c => c.id === chapter_id);
      return chapter?.name || "Unknown";
    },
    getSubjectNameFromQuiz(quiz) {
      const chapter = this.chapters.find(c => c.id === quiz.chapter_id);
      const subject = this.subjects.find(s => s.id === chapter?.subject_id);
      return subject?.name || "Unknown";
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString();
    },
    getQuizStatus(quiz) {
      const now = new Date();
      const start = new Date(quiz.date_of_quiz);
      const end = new Date(quiz.last_date);
      end.setHours(23, 59, 59, 999);
      if (now < start) return "Upcoming";
      if (now > end) return "Expired";
      return "Active";
    },
    getQuizStatusClass(quiz) {
      const status = this.getQuizStatus(quiz).toLowerCase();
      return {
        "upcoming-status": status === "upcoming",
        "active-status": status === "active",
        "expired-status": status === "expired"
      };
    },
    startQuiz(quiz) {
      const url = `/quiz-attempt/${quiz.id}`;
      const quizWindow = window.open(url, "_blank", "width=1000,height=800");
      const checkWindow = setInterval(() => {
        if (quizWindow.closed) {
          clearInterval(checkWindow);
          this.fetchQuizzes(); 
        }
      }, 1000);
    },
    filterCategory(category) {
      this.currentFilter = category;
    },
    openCheckResult(quiz) {
      this.currentQuiz = quiz;
      this.currentSubmission = quiz.submission;
      this.showResultModal = true;
    },
    getQuestionText(question_id) {
      if (!this.currentQuiz || !this.currentQuiz.questions) return "";
      const question = this.currentQuiz.questions.find(q => q.id === question_id);
      return question ? question.question_statement : "";
    },

    getOptionLabel(optionIndex, question_id) {
      if (!this.currentQuiz || !this.currentQuiz.questions) return "";
      const question = this.currentQuiz.questions.find(q => q.id === question_id);
      if (question && question.options && question.options.length > optionIndex) {
        return String.fromCharCode(65 + optionIndex) + ". " + question.options[optionIndex];
      }
      return "";
    },

    getQuestionCorrectOption(question_id) {
      if (!this.currentQuiz || !this.currentQuiz.questions) return null;
      const question = this.currentQuiz.questions.find(q => q.id === question_id);
      return question ? question.correct_option - 1 : null;
    },

    handleQuizSubmitted(e) {
      if (e.data && e.data.type === "quiz-submitted") {
        this.scorePopup.score = e.data.score;
        this.scorePopup.total = e.data.total;
        this.showScorePopup = true;
        this.fetchQuizzes();
      }
    },
    closeScorePopup() {
      this.showScorePopup = false;
    }
  },
  mounted() {
    this.fetchQuizzes();
    this.fetchSubjects();
    this.fetchAllChapters();
    window.addEventListener("message", this.handleQuizSubmitted);
  },
  beforeDestroy() {
    window.removeEventListener("message", this.handleQuizSubmitted);
  }
};
</script>



<style scoped>
.vue-notification {
  padding: 15px;
  margin: 10px;
  color: white;
  background: #44A4FC;
  border-left: 5px solid #187FE7;
}
.vue-notification.error {
  background: #E54D42;
  border-left-color: #B82E24;
}
.vue-notification.success {
  background: #68CD86;
  border-left-color: #42A85F;
}
.quiz-user {
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
.quiz-card.quiz-taken {
  background-color: #6a8cfd3f;
}

.header-controls {
  display: flex;
  justify-content: flex-start; 
  width: 100%;
  gap: 20px;
}
.title {
  font-size: 2rem;
  text-align: center;
  color: #2c3e50;
  margin: 10px 0; 
}
.filter-tabs {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  margin-right: auto; 
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
.card-actions {
  margin-top: auto;
  display: flex;
  gap: 15px;
  padding-top: 20px;
  justify-content: flex-end;
}
.take-quiz-btn, .check-result-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s ease;
}
.take-quiz-btn {
  background-color: #4CAF50;
  color: white;
}
.take-quiz-btn:hover {
  background-color: #45a049;
  transform: translateY(-1px);
}
.check-result-btn {
  background-color: #3498db;
  color: white;
}
.check-result-btn:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  text-align: center;
  width: 90%;
  max-width: 600px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.result-list {
  margin-top: 15px;
  max-height: 400px;
  overflow-y: auto;
}
.result-item {
  margin-bottom: 15px;
  border-bottom: 1px solid #ccc;
  padding-bottom: 10px;
}
.correct {
  color: green;
  font-weight: bold;
}
.incorrect {
  color: red;
  font-weight: bold;
}
button {
  margin-top: 10px;
  padding: 5px 10px;
  border: none;
  background: #4CAF50;
  color: white;
  cursor: pointer;
}
button:hover {
  background: #45a049;
}
.upcoming-status { color: #f39c12; }
.active-status { color: #2ecc71; }
.expired-status { color: #e74c3c; }
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
  }
}
</style>
