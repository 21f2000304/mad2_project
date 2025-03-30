<template>
    <div class="question-create-modal">

      <div class="modal-header">
        <h3>{{ quizTitle }}   ({{ chapterName }}) </h3>
        <h4>Total Questions: {{ questions.length }}</h4>
        <div class="header-actions">

          <button class="add-btn" v-if="!showForm" @click="openForm(null)">
            ➕ Add Question
          </button>

          <button class="close-btn" v-if="!showForm" @click="closeModal">✖️</button>
        </div>
      </div>
  

      <div v-if="!showForm" class="summary-view">
        <div v-if="questions.length === 0">
          No questions available.
        </div>
        <div v-else class="questions-list">
          <div v-for="question in sortedQuestions" :key="question.id" class="question-card">
            <div class="question-info">
              <h4>Q{{ question.q_no }}: {{ question.title }}</h4>
              <p>{{ question.question_statement }}</p>
              <ul class="options-list">
                <template v-if="question.options && question.options.length">
                  <li v-for="(opt, index) in question.options" 
                      :key="index" 
                      :class="{ 'correct-option': question.correct_option === (index + 1) }">
                    {{ index + 1 }}. {{ opt }}
                  </li>
                </template>
                <template v-else>
                  <li :class="{ 'correct-option': question.correct_option === 1 }">
                    1. {{ question.option1 }}
                  </li>
                  <li :class="{ 'correct-option': question.correct_option === 2 }">
                    2. {{ question.option2 }}
                  </li>
                  <li :class="{ 'correct-option': question.correct_option === 3 }">
                    3. {{ question.option3 }}
                  </li>
                  <li :class="{ 'correct-option': question.correct_option === 4 }">
                    4. {{ question.option4 }}
                  </li>
                </template>
              </ul>
            </div>
            <div class="question-actions">
              <button class="edit-btn" @click="openForm(question)" title="Edit Question">
                ✏️
              </button>
              <button class="delete-btn" @click="deleteQuestion(question.id)" title="Delete Question">
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>
  

        <div v-if="showForm" class="form-view card-border">
        <h3>{{ editingQuestion ? "Edit Question" : "Add New Question" }}</h3>
        <form @submit.prevent="dummySubmit">
            <div class="form-grid">
            <div class="form-group">
                <label>Question Title:</label>
                <input type="text" v-model="newQuestion.title" placeholder="Enter question title" required />
            </div>
            <div class="form-group">
                <label>Question Number:</label>
                <input type="number" v-model.number="newQuestion.q_no" placeholder="Enter question number" required />
            </div>
            <div class="form-group full-width">
                <label>Question Statement:</label>
                <textarea v-model="newQuestion.question_statement" placeholder="Enter question statement" required></textarea>
            </div>
            <div class="form-group">
                <label>Option 1:</label>
                <input type="text" v-model="newQuestion.option1" placeholder="Enter option 1" required />
            </div>
            <div class="form-group">
                <label>Option 2:</label>
                <input type="text" v-model="newQuestion.option2" placeholder="Enter option 2" required />
            </div>
            <div class="form-group">
                <label>Option 3:</label>
                <input type="text" v-model="newQuestion.option3" placeholder="Enter option 3" required />
            </div>
            <div class="form-group">
                <label>Option 4:</label>
                <input type="text" v-model="newQuestion.option4" placeholder="Enter option 4" required />
            </div>
            <div class="form-group">
                <label>Correct Option:</label>
                <select v-model.number="newQuestion.correct_option" required>
                <option :value="1">1</option>
                <option :value="2">2</option>
                <option :value="3">3</option>
                <option :value="4">4</option>
                </select>
            </div>
            </div>

            <div class="form-actions">
            <button type="button" @click="submitAndClose">💾 Submit</button>
            <button type="button" @click="saveAndNext">💾 ➕ Next</button>
            <button type="button" @click="cancelForm">❌ Close</button>
            </div>
        </form>
        </div>
    </div>
  </template>
  
  <script>
  export default {
    name: "QuestionCreate",
    props: {
      quizId: {
        type: Number,
        required: true
      },
      quizno: {
        type: Number,
        default: 0
      },
      quizTitle: {
        type: String,
        required: true
      }
    },
    data() {
      return {
        chapterName: "Unknown Chapter",
        questions: [],
        showForm: false,
        editingQuestion: null,
        newQuestion: {
          title: "",
          q_no: "",
          question_statement: "",
          option1: "",
          option2: "",
          option3: "",
          option4: "",
          correct_option: 1,
          quiz_id: this.quizId
        }
      };
    },
    computed: {
      sortedQuestions() {
        return this.questions.slice().sort((a, b) => a.q_no - b.q_no);
      }
    },
    mounted() {
        this.chapterName = this.$route.query.chapterName || "Unknown Chapter";
        console.log("QuestionCreate mounted. quizId:", this.quizId, "quizno:", this.quizno, "quizTitle:", this.quizTitle, "chapterName:", this.chapterName);
        this.fetchQuestions();
        },
    methods: {
      getAuthHeaders() {
        const token = localStorage.getItem("token");
        return token
          ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
          : { "Content-Type": "application/json" };
      },
      async fetchQuestions() {
        try {
          const response = await fetch(`http://localhost:5000/api/question?quiz_id=${this.quizId}`, {
            method: "GET",
            headers: this.getAuthHeaders(),
            credentials: "include"
          });
          if (!response.ok) {
            const errorText = await response.text();
            if (errorText.includes("No questions found for this quiz_id")) {
              this.questions = [];
              return; // Gracefully exit
            }
            throw new Error(errorText);
          }
          this.questions = await response.json();
  
          const existingNumbers = new Set(
            this.questions
            .filter(q => q.quiz_id === this.quizId)
            .map(q => Number(q.q_no))
          );
          let nextQNo = 1;
          while (existingNumbers.has(nextQNo)) {
            nextQNo++;
          }
          this.nextQNo = nextQNo;
        } catch (error) {
          console.error("Error fetching questions:", error);
        }
      },
      openForm(question = null) {
        this.showForm = true;
        if (question) {
          this.editingQuestion = question;
          if (question.options && Array.isArray(question.options)) {
            this.newQuestion = {
              title: question.title,
              q_no: this.nextQNo || 1,
              question_statement: question.question_statement,
              option1: question.options[0],
              option2: question.options[1],
              option3: question.options[2],
              option4: question.options[3],
              correct_option: question.correct_option,
              quiz_id: this.quizId
            };
          } else {
            this.newQuestion = { ...question, quiz_id: this.quizId };
          }
        } else {
          this.editingQuestion = null;
          this.newQuestion = {
            title: "",
            q_no: this.nextQNo,
            question_statement: "",
            option1: "",
            option2: "",
            option3: "",
            option4: "",
            correct_option: 1,
            quiz_id: this.quizId
          };
        }
      },
      cancelForm() {
        this.showForm = false;
        this.editingQuestion = null;
        this.newQuestion = {
          title: "",
          q_no: "",
          question_statement: "",
          option1: "",
          option2: "",
          option3: "",
          option4: "",
          correct_option: 1,
          quiz_id: this.quizId
        };
      },
      async submitQuestion() {
        if (
          !this.newQuestion.title.trim() ||
          this.newQuestion.q_no === "" ||
          !this.newQuestion.question_statement.trim() ||
          !this.newQuestion.option1.trim() ||
          !this.newQuestion.option2.trim() ||
          !this.newQuestion.option3.trim() ||
          !this.newQuestion.option4.trim()
        ) {
          alert("Please fill in all required fields.");
          return false;
        }
        try {
          let url = "http://localhost:5000/api/question";
          let method = "POST";
          if (this.editingQuestion && this.editingQuestion.id) {
            url += `/${this.editingQuestion.id}`;
            method = "PUT";
          }
          const response = await fetch(url, {
            method,
            headers: this.getAuthHeaders(),
            credentials: "include",
            body: JSON.stringify(this.newQuestion)
          });
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
          }
          await this.fetchQuestions();
          this.$emit("quizUpdated");
          return true;
        } catch (error) {
          console.error("Error saving question:", error);
          alert("Error: " + error.message);
          return false;
        }
      },
      async submitAndClose() {
        const success = await this.submitQuestion();
        if (success) {
          alert("Question saved successfully.");
          await this.fetchQuestions();
          if (window.opener) {
            window.opener.postMessage('questions-updated', window.location.origin);
          } else {
            this.$emit("quizUpdated");
          }
          this.cancelForm();
        }
      },
      async saveAndNext() {
        const success = await this.submitQuestion();
        if (success) {
          alert("Question saved successfully. Ready for next entry.");
          await this.fetchQuestions();
          this.openForm();
        }
      },
      async deleteQuestion(questionId) {
        if (!confirm("Are you sure you want to delete this question?")) return;
        try {
          const response = await fetch(`http://localhost:5000/api/question/${questionId}`, {
            method: "DELETE",
            headers: this.getAuthHeaders(),
            credentials: "include"
          });
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(errorText);
          }
          await this.fetchQuestions();
          alert("Question deleted successfully.");
        } catch (error) {
          console.error("Error deleting question:", error);
          alert("Error: " + error.message);
        }
      },
      closeModal() {
        console.log("Close button clicked");
        if (window.opener) {
          window.opener.postMessage('questions-updated', window.location.origin);
          window.close();
        } else {
          this.$emit("close");
          this.$emit("quizUpdated");
        }
        }
    }
  };
  </script>
  
  <style scoped>
  .question-create-modal {
    background: #fff;
    padding: 10px 20px;
    border-radius: 8px;
    width: 800px;
    max-width: 95%;
    margin: 10px auto;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    position: relative;
  }
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #ccc;
    padding-bottom: 10px;
    margin-bottom: 20px;
  }
  .modal-header h3 {
    margin: 0;
    font-size: 1.5rem;
  }
  .header-actions {
    display: flex;
  }
  .add-btn {
  background-color: #28a745;
  color: #fff;
  padding: 2px 8px;      
  border: none;
  border-radius: 10px; 
  cursor: pointer;
  font-size: 0.8rem;  
}

  .add-btn:hover {
    background-color: #218838;
  }
  .close-btn {
    background: transparent;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
  }
  .summary-view {
    max-height: 500px;
    overflow-y: auto;
    padding: 10px;
  }
  .questions-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .question-card {
    border: 1px solid #ddd;
    padding: 15px;
    margin-bottom: 10px;
    border-radius: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .question-info h4 {
    margin: 0 0 5px 0;
  }
  .options-list {
    list-style: none;
    padding: 0;
    margin: 5px 0 0 0;
  }
  .options-list li {
    padding: 5px;
  }
  .correct-option {
    background-color: #d4edda;
    color: #155724;
    font-weight: bold;
  }
  .question-actions button {
    background: transparent;
    border: none;
    cursor: pointer;
    margin-left: 5px;
    font-size: 1.2rem;
  }
  .edit-btn:hover {
    color: #007bff;
  }
  .delete-btn:hover {
    color: #dc3545;
  }
  .form-view {
    border-top: 1px solid #ccc;
    padding-top: 20px;
  }
  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  .form-group {
    display: flex;
    flex-direction: column;
  }
  .form-group.full-width {
    grid-column: 1 / -1;
  }
  .form-group label {
    font-weight: bold;
    margin-bottom: 5px;
  }
  .form-group input,
  .form-group textarea,
  .form-group select {
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }
  .form-actions {
    margin-top: 20px;
    display: flex;
    justify-content: space-between;
  }
  .form-actions button {
    padding: 8px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    background: #28a745;
    color: #fff;
  }
  .form-actions button:hover {
    background: #218838;
  }
  </style>
  