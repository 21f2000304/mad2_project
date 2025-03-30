<template>
  <div class="quiz-container">
    <div v-if="accessDenied" class="access-denied">
      <h2>Action Denied</h2>
      <p>You have already taken this Quiz. Try other quizzes.</p>
    </div>

    <div v-if="!accessDenied && showConfirmation" class="confirmation-dialog">
      <div class="dialog-content">
        <h3>Start Quiz?</h3>
        <p>You have {{ formatTime(timeDuration) }} mins to complete the quiz.</p>
        <div class="dialog-buttons">
          <button @click="startQuiz">Start Quiz</button>
          <button @click="showConfirmation = false">Cancel</button>
        </div>
      </div>
    </div>


    <div v-if="!accessDenied && quizActive && !showConfirmation && questions.length > 0" class="quiz-interface">

      <div class="quiz-timer">
        Time Remaining: {{ formatTime(timeRemaining) }}
      </div>

      <div class="quiz-layout">
        <div class="question-sidebar">
          <div 
            v-for="(question, index) in questions"
            :key="question.id"
            class="question-number"
            :class="{
              'current': currentQuestionIndex === index,
              'answered': questionStates[index] && questionStates[index].answered,
              'unanswered': questionStates[index] && questionStates[index].visited && !questionStates[index].answered,
              'marked': questionStates[index] && questionStates[index].marked
            }"
            @click="jumpToQuestion(index)"
          >
            {{ index + 1 }}
          </div>
        </div>

        <div class="question-main">
          <div v-if="currentQuestion" class="question-card">
            <h3>Question {{ currentQuestionIndex + 1 }}: {{ currentQuestion.title }}</h3>
            <p class="question-text">{{ currentQuestion.question_statement }}</p>
            
            <div class="options-container">
              <label
                v-for="(option, index) in currentQuestion.options"
                :key="index"
                :class="{ selected: selectedOption === index }"
              >
                <input
                  type="radio"
                  :name="'question' + currentQuestion.id"
                  :value="index"
                  v-model="selectedOption"
                  @change="saveAnswer"
                >
                <span class="option-letter">{{ String.fromCharCode(65 + index) }}.</span>
                {{ option }}
              </label>
            </div>

            <div class="action-buttons">
              <button 
                @click="prevQuestion" 
                v-if="currentQuestionIndex > 0"
                class="nav-btn prev-btn"
              >
                ← Previous
              </button>
              
              <div class="middle-buttons">
                <button 
                  @click="resetAnswer" 
                  :disabled="selectedOption === null"
                  class="reset-btn"
                >
                  Reset Answer
                </button>
                <button 
                  @click="markForLater"
                  class="mark-btn"
                >
                  Mark for Later
                </button>
              </div>

              <button 
                @click="nextQuestion" 
                v-if="currentQuestionIndex < questions.length - 1"
                class="nav-btn next-btn"
              >
                Next →
              </button>
              
              <button 
                v-if="currentQuestionIndex === questions.length - 1"
                @click="submitQuiz"
                class="submit-btn"
              >
                Submit Quiz
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      quizId: null,
      accessDenied: false,
      showConfirmation: false,
      quizActive: false,
      quizDetails: null,
      questions: [],
      currentQuestionIndex: 0,
      selectedOption: null,
      questionStates: [],
      timeDuration: 0,
      timeRemaining: 0,
      timerInterval: null,
      loading: true
    }
  },
  computed: {
    currentQuestion() {
      return this.questions[this.currentQuestionIndex];
    }
  },
  async mounted() {
    this.quizId = this.$route.params.quizId;
    await this.verifyQuizAccess();
    if (!this.accessDenied && this.quizActive) {
      setTimeout(() => {
        this.showConfirmation = true;
      }, 500);
      await this.fetchQuestions();
      this.initializeQuestionStates();
    } else if (this.accessDenied) {
      alert("You have already taken this Quiz. Try other quizzes.");
    }
    this.loading = false;
  },
  beforeDestroy() {
    clearInterval(this.timerInterval);
  },
  methods: {
    async verifyQuizAccess() {
      try {
        const response = await fetch(`http://localhost:5000/api/quiz/${this.quizId}`, {
          headers: this.getAuthHeaders()
        });
        if (!response.ok) {
          this.accessDenied = true;
          return;
        }
        const quiz = await response.json();

        const submissionResponse = await fetch(`http://localhost:5000/api/submit-quiz?quiz_id=${this.quizId}`, {
          headers: this.getAuthHeaders()
        });
        const submissionData = await submissionResponse.json();
        
        if (submissionData && submissionData.length > 0) {
          this.accessDenied = true;
          this.quizDetails = quiz;
          this.quizDetails.submission = submissionData[0]; 
        } else {
          const now = new Date();
          const start = new Date(quiz.date_of_quiz);
          const end = new Date(quiz.last_date);
          end.setHours(23, 59, 59, 999);
          if (now >= start && now <= end) {
            this.quizActive = true;
            this.quizDetails = quiz;
            this.timeDuration = this.parseTimeDuration(quiz.time_duration);
            this.timeRemaining = this.timeDuration;
          } else {
            this.accessDenied = true;
          }
        }
      } catch (error) {
        console.error("Quiz access verification failed:", error);
        this.accessDenied = true;
      }
    },
    async fetchQuestions() {
      try {
        const response = await fetch(`http://localhost:5000/api/question?quiz_id=${this.quizId}`, {
          headers: this.getAuthHeaders()
        });
        this.questions = await response.json();
        this.questions.sort((a, b) => a.q_no - b.q_no);
        this.initializeQuestionStates();
      } catch (error) {
        console.error("Error fetching questions:", error);
      }
    },
    initializeQuestionStates() {
      this.questionStates = this.questions.map(() => ({
        visited: false,
        answered: false,
        marked: false
      }));
      if (this.questionStates.length > 0) {
        this.questionStates[0].visited = true;
      }
    },
    startQuiz() {
      this.showConfirmation = false;
      this.startTimer();
    },
    startTimer() {
      this.timerInterval = setInterval(() => {
        if (this.timeRemaining > 0) {
          this.timeRemaining--;
        } else {
          this.submitQuiz();
        }
      }, 1000);
    },
    parseTimeDuration(timeString) {
      const [hours, minutes] = timeString.split(':').map(Number);
      return (hours * 3600) + (minutes * 60);
    },
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60);
      const secs = seconds % 60;
      return `${mins}:${secs.toString().padStart(2, "0")}`;
    },
    jumpToQuestion(index) {
      if (index >= 0 && index < this.questions.length) {
        this.currentQuestionIndex = index;
        if (this.questionStates[index]) {
          this.questionStates[index].visited = true;
        }
        this.selectedOption = this.questions[index].userAnswer;
      }
    },
    saveAnswer() {
      this.questionStates[this.currentQuestionIndex].answered = true;
      this.questions[this.currentQuestionIndex].userAnswer = this.selectedOption;
    },
    resetAnswer() {
      this.selectedOption = null;
      this.questionStates[this.currentQuestionIndex].answered = false;
      delete this.questions[this.currentQuestionIndex].userAnswer;
    },
    markForLater() {
      this.questionStates[this.currentQuestionIndex].marked =
        !this.questionStates[this.currentQuestionIndex].marked;
    },
    nextQuestion() {
      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
        this.questionStates[this.currentQuestionIndex].visited = true;
        this.selectedOption = this.questions[this.currentQuestionIndex].userAnswer;
      }
    },
    prevQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--;
        this.selectedOption = this.questions[this.currentQuestionIndex].userAnswer;
      }
    },
    async submitQuiz() {
      try {
        const answers = this.questions
          .filter(q => q.userAnswer !== undefined)
          .map(q => ({
            question_id: q.id,
            selected_option: q.userAnswer
          }));
        const response = await fetch('http://localhost:5000/api/submit-quiz', {
          method: "POST",
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            quizId: this.quizId,
            answers: answers
          })
        });
        const result = await response.json();
        if (!response.ok) {
          const errorMessage =
            result.error ||
            (result.message !== "Quiz submitted successfully" ? result.message : null) ||
            "Submission failed";
          throw new Error(errorMessage);
        }
        if (window.opener) {
          console.log("Sending postMessage:", {
            type: "quiz-submitted",
            score: result.score,
            total: result.total
          });
          window.opener.postMessage(
            {
              type: "quiz-submitted",
              score: result.score,
              total: result.total
            },
            "*"
          );
          window.close();
        } else {
          console.warn("No opener found, using router navigation instead.");
          this.$router.push({
            path: "/results",
            query: {
              score: result.score,
              total: result.total
            }
          });
        }
      } catch (error) {
        console.error("Submission error:", error);
        alert(`Submission failed: ${error.message}`);
        if (this.timerInterval) clearInterval(this.timerInterval);
      }
    },
    getAuthHeaders() {
      const token = localStorage.getItem("token");
      return {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      };
    }
  }
};
</script>


<style scoped>
.quiz-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px;
}

.access-denied {
  text-align: center;
  padding: 3rem;
  color: #dc3545;
  font-size: 1.2rem;
}

.confirmation-dialog {
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

.dialog-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  text-align: center;
}

.dialog-buttons button {
  margin: 10px;
  padding: 8px 16px;
}


.quiz-timer {
  position: fixed;
  top: 25px;
  right: 25px;
  background: #2c3e50;
  color: white;
  padding: 12px 25px;
  border-radius: 8px;
  font-size: 1.1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.quiz-layout {
  display: flex;
  gap: 20px;
  margin-top: 30px;
}

.question-sidebar {
  width: 80px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.question-number {
  width: 50px;
  height: 50px;
  border: 3px solid #e0e0e0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 1.1rem;
}

.question-number.current {
  border-color: #2196F3;
  background-color: #e3f2fd;
  transform: scale(1.1);
}

.question-number.answered {
  background-color: #4CAF50;
  color: white;
  border-color: #45a049;
}

.question-number.unanswered {
  background-color: #f44336;
  color: white;
  border-color: #e53935;
}

.question-number.marked {
  background-color: #ffeb3b;
  border-color: #fdd835;
  animation: pulse 1.5s infinite;
}

.question-main {
  flex: 1;
  max-width: 1000px;
}

.question-card {
  background: white;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  margin-bottom: 2rem;
}

.question-text {
  font-size: 1.2rem;
  margin: 1.5rem 0;
  line-height: 1.6;
  color: #2c3e50;
}

.options-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin: 2rem 0;
}

.options-container label {
  display: flex;
  align-items: center;
  padding: 1.2rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.options-container label:hover {
  border-color: #2196F3;
  background: #f0f8ff;
}

.options-container label.selected {
  border-color: #2196F3;
  background-color: #e3f2fd;
  transform: translateX(10px);
}

.option-letter {
  font-weight: 600;
  margin-right: 15px;
  font-size: 1.1rem;
  min-width: 30px;
  color: #2196F3;
}

input[type="radio"] {
  width: 20px;
  height: 20px;
  margin-right: 15px;
  accent-color: #2196F3;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 2.5rem;
  gap: 15px;
  flex-wrap: wrap;
}

.middle-buttons {
  display: flex;
  gap: 15px;
  order: 2;
}

button {
  padding: 12px 25px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  border: 2px solid transparent;
}

.nav-btn {
  background: white;
  color: #2196F3;
  border: 2px solid #2196F3;
  order: 1;
}

.nav-btn:hover {
  background: #2196F3;
  color: white;
  box-shadow: 0 4px 12px rgba(33,150,243,0.3);
}

.mark-btn {
  background: #ff4444;
  color: white;
  border-color: #ff4444;
}

.mark-btn:hover {
  background: #cc0000;
  border-color: #cc0000;
  box-shadow: 0 4px 12px rgba(255,68,68,0.3);
}

.submit-btn {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
  order: 3;
  padding: 15px 35px;
  font-weight: 600;
}

.submit-btn:hover {
  background: #45a049;
  border-color: #45a049;
  box-shadow: 0 4px 12px rgba(76,175,80,0.3);
}

.reset-btn {
  background: #757575;
  color: white;
  border-color: #757575;
}

.reset-btn:hover {
  background: #616161;
  border-color: #616161;
}

@media (max-width: 768px) {
  .quiz-container {
    padding: 15px;
  }

  .quiz-layout {
    flex-direction: column;
    margin-top: 30px;
    gap: 20px;
  }

  .question-sidebar {
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }

  .question-card {
    padding: 1.5rem;
  }

  .action-buttons {
    flex-direction: column;
  }

  button {
    width: 100%;
    justify-content: center;
  }

  .nav-btn {
    order: initial;
  }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>