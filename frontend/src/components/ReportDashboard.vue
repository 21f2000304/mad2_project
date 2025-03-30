<template>  
  <div class="report-dashboard">
    <h1>Quiz Report Dashboard</h1>

    <div class="tabs">

      <template v-if="!isAdmin">
        <button :class="{ active: activeTab === 'user' }" @click="activeTab = 'user'">
          My Reports
        </button>
        <button :class="{ active: activeTab === 'reports' }" @click="activeTab = 'reports'">
          Quiz Reports
        </button>
      </template>

      <template v-else>
        <button :class="{ active: adminActiveTab === 'details' }" @click="adminActiveTab = 'details'">
          User Details
        </button>
        <button :class="{ active: adminActiveTab === 'charts' }" @click="adminActiveTab = 'charts'">
          Admin Charts
        </button>
      </template>
    </div>


    <template v-if="!isAdmin">

      <div v-if="activeTab === 'user'">
        <h2>Quiz List</h2>
        <div class="export-buttons">
          <button @click="exportReport('csv')">Export CSV</button>
          <button @click="exportReport('excel')">Export Excel</button>
          <button @click="exportReport('pdf')">Export PDF</button>
        </div>
        <table v-if="filteredQuizList.length">
          <thead>
            <tr>
              <th>Quiz Title</th>
              <th>Subject</th>
              <th>Chapter</th>
              <th>Submitted At</th>
              <th>Score</th>
              <th>Average Score (Subject)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="quiz in filteredQuizList" :key="quiz.submission_id">
              <td>{{ quiz.quiz_title }}</td>
              <td>{{ quiz.subject_name }}</td>
              <td>{{ quiz.chapter_name }}</td>
              <td>{{ formatDate(quiz.submitted_at) }}</td>
              <td>{{ quiz.score }}</td>
              <td>{{ averageScoresBySubject[quiz.subject_name] || '-' }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>No quizzes found.</p>
      </div>


      <div v-if="activeTab === 'reports'">
        <h2>Quiz Reports</h2>
        <div class="charts-wrapper">
          <div class="left-charts">

            <div class="chart-container bar-chart-container small-chart">
              <h3>Stacked Bar Chart: Quiz Scores per Subject</h3>
              <base-chart
                v-if="barChartData"
                :chart-data="barChartData"
                :chart-options="barChartOptions"
                chart-type="bar"
              />
            </div>

            <div class="chart-container small-chart">
              <h3>Score Trend per Subject (by Quiz Order)</h3>
              <base-chart
                v-if="userLineChartData"
                :chart-data="userLineChartData"
                :chart-options="chartOptions"
                chart-type="line"
              />
            </div>
          </div>
          <div class="right-charts">

            <div class="chart-container pie-chart-container small-chart">
              <h3>Taken Quizzes Distribution per Subject</h3>
              <p class="total-number">Total Taken: {{ takenTotal }}</p>
              <base-chart
                v-if="pieTakenChartData"
                :chart-data="pieTakenChartData"
                :chart-options="chartOptions"
                chart-type="pie"
              />
            </div>
          </div>
        </div>
      </div>
    </template>


    <template v-else>

      <div v-if="adminActiveTab === 'details'">
        <h2>User Details</h2>
        <div class="export-buttons">
          <button @click="exportReport('csv')">Export CSV</button>
          <button @click="exportReport('excel')">Export Excel</button>
          <button @click="exportReport('pdf')">Export PDF</button>
        </div>
        <table v-if="filteredAdminUserDetails.length">
          <thead>
            <tr>
              <th>User Name</th>
              <th>Email</th>
              <th>Quiz Title</th>
              <th>Subject</th>
              <th>Score</th>
              <th>Avg Score (Subject)</th>
              <th>Avg Score (Overall)</th>
              <th>Submitted At</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="detail in filteredAdminUserDetails" :key="detail.id">
              <td>{{ detail.user_name }}</td>
              <td>{{ detail.email }}</td>
              <td>{{ detail.quiz_title }}</td>
              <td>{{ detail.subject_name }}</td>
              <td>{{ detail.score }}</td>
              <td>{{ detail.avg_score_subject }}</td>
              <td>{{ detail.avg_score_all }}</td>
              <td>{{ formatDate(detail.submitted_at) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>No user details found.</p>
      </div>

      <div v-if="adminActiveTab === 'charts'">
        <h2>Admin Charts</h2>
        <div class="charts-wrapper">
          <div class="left-charts">

            <div class="chart-container small-chart">
              <h3>Stacked Bar Chart: Avg Scores by Quiz (by Subject)</h3>
              <base-chart
                v-if="adminBarChartData"
                :chart-data="adminBarChartData"
                :chart-options="barChartOptions"
                chart-type="bar"
              />
            </div>

            <div class="chart-container small-chart">
              <h3>Trend: Avg Score on Each Quiz (by Subject)</h3>
              <base-chart
                v-if="adminLineChartData"
                :chart-data="adminLineChartData"
                :chart-options="chartOptions"
                chart-type="line"
              />
            </div>
          </div>
          <div class="right-charts">

            <div class="chart-container pie-chart-container small-chart">
              <h3>Pie Chart: Total Quizzes Taken per Subject</h3>
              <p class="total-number">Total Taken: {{ adminTakenTotal }}</p>
              <base-chart
                v-if="adminPieTakenChartData"
                :chart-data="adminPieTakenChartData"
                :chart-options="chartOptions"
                chart-type="pie"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import BaseChart from "@/components/BaseChart.vue";
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { saveAs } from 'file-saver';

export default {
  name: "ReportDashboard",
  components: { BaseChart },
  props: {
    searchQuery: {
      type: String,
      default: ""
    }
  },
  data() {
    return {
      activeTab: "user", 
      adminActiveTab: "details",
      isAdmin: false,
      quizList: [],
      adminUserDetails: [],
      adminChartData: null,
      pieTakenChartData: null,
      barChartData: null,
      lineChartData: null,
      takenTotal: 0,
      adminTakenTotal: 0,
      averageScoresBySubject: {},
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false
      },
      barChartOptions: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { 
            stacked: true,
            ticks: {
              autoSkip: true,
              maxTicksLimit: 5,
              font: { size: 10 }
            }
          },
          y: { 
            stacked: true, 
            beginAtZero: true 
          }
        }
      }
    };
  },
  computed: {
    filteredQuizList() {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) return this.quizList;
      return this.quizList.filter(quiz => {
        return (
          quiz.quiz_title.toLowerCase().includes(query) ||
          quiz.subject_name.toLowerCase().includes(query) ||
          quiz.chapter_name.toLowerCase().includes(query)
        );
      });
    },
    filteredAdminUserDetails() {
      const query = this.searchQuery.trim().toLowerCase();
      if (!query) return this.adminUserDetails;
      return this.adminUserDetails.filter(detail => {
        return (
          detail.user_name.toLowerCase().includes(query) ||
          detail.email.toLowerCase().includes(query) ||
          detail.quiz_title.toLowerCase().includes(query) ||
          detail.subject_name.toLowerCase().includes(query)
        );
      });
    },
    userLineChartData() {
      if (!this.quizList.length) return { labels: [], datasets: [] };
      const subjectsSet = new Set(this.quizList.map(sub => sub.subject_name || "Unknown"));
      const subjects = Array.from(subjectsSet);
      const subjectDatasets = subjects.map(subject => {
        const subjectItems = this.quizList
          .filter(sub => (sub.subject_name || "Unknown") === subject)
          .sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at));
        const averages = [];
        subjectItems.forEach(item => {
          averages.push(item.score);
        });
        return {
          subject,
          data: averages
        };
      });
      const maxQuizCount = Math.max(...subjectDatasets.map(ds => ds.data.length));
      const xAxisLabels = Array.from({ length: maxQuizCount }, (v, i) => `Quiz #${i + 1}`);
      const datasets = subjectDatasets.map(ds => {
        const paddedData = [...ds.data];
        while (paddedData.length < maxQuizCount) {
          paddedData.push(null);
        }
        return {
          label: ds.subject,
          data: paddedData,
          borderColor: this.getRandomColor(),
          backgroundColor: "transparent",
          fill: false,
          spanGaps: true
        };
      });
      return {
        labels: xAxisLabels,
        datasets
      };
    }
  },
  methods: {
    async fetchQuizList() {
      try {
        const response = await fetch("http://localhost:5000/api/my-reports", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        const data = await response.json();
        this.quizList = data;
        this.computeAverageScores();
      } catch (error) {
        console.error("Error fetching quiz list:", error);
      }
    },
    async fetchAvailableQuizzes() {
      try {
        const response = await fetch("http://localhost:5000/api/quiz", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        const data = await response.json();
        const now = new Date();
        return data.filter(quiz => new Date(quiz.date_of_quiz) <= now);
      } catch (error) {
        console.error("Error fetching available quizzes:", error);
        return [];
      }
    },
    async fetchUserCharts() {
      try {
        if (!this.quizList || this.quizList.length === 0) {
          console.warn("No quiz submissions available to compute chart data.");
          return;
        }
        const availableQuizzes = await this.fetchAvailableQuizzes();
        const subjectsSet = new Set(this.quizList.map(sub => sub.subject_name || "Unknown"));
        const subjects = Array.from(subjectsSet);
        const takenCounts = {};
        subjects.forEach(subject => { takenCounts[subject] = 0; });
        this.quizList.forEach(sub => {
          const subject = sub.subject_name || "Unknown";
          takenCounts[subject] = (takenCounts[subject] || 0) + 1;
        });
        this.takenTotal = Object.values(takenCounts).reduce((sum, val) => sum + val, 0);
        this.pieTakenChartData = {
          labels: subjects,
          datasets: [{
            label: "Taken Quizzes",
            data: subjects.map(subject => takenCounts[subject]),
            backgroundColor: subjects.map(() => this.getRandomColor())
          }]
        };
        const quizTitlesSet = new Set(this.quizList.map(sub => sub.quiz_title || "Unknown"));
        const quizTitles = Array.from(quizTitlesSet);
        const barDatasets = quizTitles.map(quizTitle => {
          const data = subjects.map(subject => {
            const subs = this.quizList.filter(sub =>
              sub.quiz_title === quizTitle && (sub.subject_name || "Unknown") === subject
            );
            return subs.reduce((sum, sub) => sum + sub.score, 0);
          });
          return {
            label: quizTitle,
            data: data,
            backgroundColor: this.getRandomColor()
          };
        });
        this.barChartData = {
          labels: subjects,
          datasets: barDatasets
        };
        const quizTitlesSetLine = new Set(this.quizList.map(sub => sub.quiz_title || "Unknown"));
        const quizTitlesArr = Array.from(quizTitlesSetLine).sort();
        const lineDatasets = subjects.map(subject => {
          const data = quizTitlesArr.map(quizTitle => {
            const subs = this.quizList.filter(sub =>
              sub.subject_name === subject && sub.quiz_title === quizTitle
            );
            if (subs.length === 0) return null;
            const total = subs.reduce((sum, sub) => sum + sub.score, 0);
            return (total / subs.length).toFixed(2);
          });
          return {
            label: subject,
            data: data,
            borderColor: this.getRandomColor(),
            backgroundColor: "transparent",
            fill: false,
            spanGaps: true
          };
        });
        this.lineChartData = {
          labels: quizTitlesArr,
          datasets: lineDatasets
        };
      } catch (error) {
        console.error("Error in fetchUserCharts:", error);
      }
    },
    async fetchAdminUserDetails() {
      try {
        const response = await fetch("http://localhost:5000/api/admin-user-details", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        const data = await response.json();
        const grouped = {};
        data.forEach(item => {
          if (!grouped[item.id]) {
            grouped[item.id] = {
              user_name: item.user_name,
              email: item.email,
              details: []
            };
          }
          grouped[item.id].details.push(item);
        });
        const userDetails = [];
        Object.values(grouped).forEach(user => {
          const overallTotal = user.details.reduce((sum, detail) => sum + detail.score, 0);
          const overallAvg = (overallTotal / user.details.length).toFixed(2);
          user.details.forEach(detail => {
            const subjectDetails = user.details.filter(d => d.subject_name === detail.subject_name);
            const subjectTotal = subjectDetails.reduce((sum, d) => sum + d.score, 0);
            const subjectAvg = (subjectTotal / subjectDetails.length).toFixed(2);
            userDetails.push({
              id: detail.id,
              user_name: user.user_name,
              email: user.email,
              quiz_title: detail.quiz_title,
              subject_name: detail.subject_name,
              score: detail.score,
              avg_score_subject: subjectAvg,
              avg_score_all: overallAvg,
              submitted_at: detail.submitted_at
            });
          });
        });
        this.adminUserDetails = userDetails;
      } catch (error) {
        console.error("Error fetching admin user details:", error);
      }
    },
    async fetchAdminCharts() {
      try {
        const response = await fetch("http://localhost:5000/api/admin-quiz-data", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        const allData = await response.json();
        
        const subjectsSet = new Set(allData.map(item => item.subject_name || "Unknown"));
        const subjects = Array.from(subjectsSet);
        
        const takenSets = {};
        subjects.forEach(subject => {
          takenSets[subject] = new Set();
        });
        allData.forEach(item => {
          const subject = item.subject_name || "Unknown";
          takenSets[subject].add(item.quiz_id);
        });
        
        const quizResponse = await fetch("http://localhost:5000/api/quiz", {
          headers: this.getAuthHeaders(),
          credentials: "include"
        });
        const quizData = await quizResponse.json();
        const now = new Date();
        const availableQuizzes = quizData.filter(quiz => new Date(quiz.date_of_quiz) <= now);
        
        const availableSets = {};
        subjects.forEach(subject => {
          availableSets[subject] = new Set();
        });
        availableQuizzes.forEach(quiz => {
          const subject = quiz.subject_name || "Unknown";
          if (!availableSets[subject]) {
            availableSets[subject] = new Set();
          }
          availableSets[subject].add(quiz.id);
        });
        
        const takenCounts = {};
        subjects.forEach(subject => {
          takenCounts[subject] = takenSets[subject].size;
        });
        
        this.adminTakenTotal = subjects.reduce((sum, subject) => sum + takenCounts[subject], 0);
        
        this.adminPieTakenChartData = {
          labels: subjects,
          datasets: [{
            label: "Taken Quizzes",
            data: subjects.map(subject => takenCounts[subject]),
            backgroundColor: subjects.map(() => this.getRandomColor())
          }]
        };
        const quizTitlesSet = new Set(allData.map(item => item.quiz_title || "Unknown"));
        const quizTitles = Array.from(quizTitlesSet);
        const barDatasets = quizTitles.map(quizTitle => {
          const data = subjects.map(subject => {
            const items = allData.filter(item =>
              item.quiz_title === quizTitle && (item.subject_name || "Unknown") === subject
            );
            if (items.length === 0) return 0;
            const total = items.reduce((sum, item) => sum + item.score, 0);
            return (total / items.length).toFixed(2);
          });
          return {
            label: quizTitle,
            data: data,
            backgroundColor: this.getRandomColor()
          };
        });
        this.adminBarChartData = {
          labels: subjects,
          datasets: barDatasets
        };
        const subjectDatasets = subjects.map(subject => {
          const subjectItems = allData.filter(item => (item.subject_name || "Unknown") === subject);
          const groups = {};
          subjectItems.forEach(item => {
            if (!groups[item.quiz_id]) {
              groups[item.quiz_id] = [];
            }
            groups[item.quiz_id].push(item);
          });
          const quizDataArray = Object.keys(groups).map(quizId => {
            const groupItems = groups[quizId];
            const avgScore = groupItems.reduce((sum, item) => sum + item.score, 0) / groupItems.length;
            const earliest = groupItems.reduce(
              (min, item) =>
                new Date(item.submitted_at) < new Date(min) ? item.submitted_at : min,
              groupItems[0].submitted_at
            );
            return { quizId, avgScore: parseFloat(avgScore.toFixed(2)), earliest };
          });
          quizDataArray.sort((a, b) => new Date(a.earliest) - new Date(b.earliest));
          return {
            subject,
            data: quizDataArray.map(q => q.avgScore)
          };
        });
        
        const maxQuizCount = Math.max(...subjectDatasets.map(ds => ds.data.length));
        const xAxisLabels = Array.from({ length: maxQuizCount }, (v, i) => `Quiz #${i + 1}`);
        const lineDatasets = subjectDatasets.map(ds => {
          const paddedData = [...ds.data];
          while (paddedData.length < maxQuizCount) {
            paddedData.push(null);
          }
          return {
            label: ds.subject,
            data: paddedData,
            borderColor: this.getRandomColor(),
            backgroundColor: "transparent",
            fill: false,
            spanGaps: true
          };
        });
        this.adminLineChartData = {
          labels: xAxisLabels,
          datasets: lineDatasets
        };
      } catch (error) {
        console.error("Error fetching admin charts:", error);
      }
    },
    async exportReport(type) {
      try {
        let exportData, headers, filenamePrefix;

        if (this.isAdmin) {
          if (!this.filteredAdminUserDetails?.length) {
            alert('No data available for export');
            return;
          }
          exportData = this.filteredAdminUserDetails.map(item => ({
            ...item,
            submitted_at: this.formatDate(item.submitted_at)
          }));
          headers = [
            { label: 'User Name', key: 'user_name' },
            { label: 'Email', key: 'email' },
            { label: 'Quiz Title', key: 'quiz_title' },
            { label: 'Subject', key: 'subject_name' },
            { label: 'Score', key: 'score' },
            { label: 'Subject Average', key: 'avg_score_subject' },
            { label: 'Overall Average', key: 'avg_score_all' },
            { label: 'Submission Date', key: 'submitted_at' },
          ];
          filenamePrefix = 'admin_report';
        } else {
          if (this.activeTab !== 'user') {
            alert('Export only available for quiz list view');
            return;
          }
          if (!this.filteredQuizList?.length) {
            alert('No data available for export');
            return;
          }
          exportData = this.filteredQuizList.map(quiz => ({
            quiz_title: quiz.quiz_title,
            subject_name: quiz.subject_name,
            chapter_name: quiz.chapter_name,
            submitted_at: this.formatDate(quiz.submitted_at),
            score: quiz.score,
            average_score_subject: this.averageScoresBySubject[quiz.subject_name] || '-'
          }));
          headers = [
            { label: 'Quiz Title', key: 'quiz_title' },
            { label: 'Subject', key: 'subject_name' },
            { label: 'Chapter', key: 'chapter_name' },
            { label: 'Submitted At', key: 'submitted_at' },
            { label: 'Score', key: 'score' },
            { label: 'Subject Average', key: 'average_score_subject' },
          ];
          filenamePrefix = 'user_report';
        }

        const filename = `${filenamePrefix}_${new Date().toISOString().slice(0, 10)}`;

        switch(type) {
          case 'csv': 
            this.exportCSV(exportData, headers, filename);
            break;
          case 'excel': 
            this.exportExcel(exportData, headers, filename);
            break;
          case 'pdf': 
            this.exportPDF(exportData, headers, filename);
            break;
          default: 
            console.error('Invalid export type:', type);
        }
      } catch (error) {
        console.error('Export error:', error);
        alert(`Export failed: ${error.message}`);
      }
    },

    exportCSV(data, headers, filename) {
      const csvContent = [
        headers.map(h => `"${h.label.replace(/"/g, '""')}"`).join(','),
        ...data.map(row =>
          headers.map(h => {
            const value = row[h.key] ?? '';
            return `"${String(value).replace(/"/g, '""')}"`;
          }).join(',')
        )
      ].join('\r\n');

      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
      saveAs(blob, `${filename}.csv`);
    },

    exportExcel(data, headers, filename) {
      const worksheetData = data.map(row => 
        headers.reduce((obj, header) => {
          obj[header.label] = row[header.key];
          return obj;
        }, {})
      );
      
      const worksheet = XLSX.utils.json_to_sheet(worksheetData);
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Report');
      XLSX.writeFile(workbook, `${filename}.xlsx`);
    },

    exportPDF(data, headers, filename) {
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth = doc.internal.pageSize.getWidth();
      
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.text('Quiz Performance Report', pageWidth/2, 20, { align: 'center' });
      
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Generated: ${new Date().toLocaleString()}`, pageWidth/2, 28, { align: 'center' });

      autoTable(doc, {
        head: [headers.map(h => h.label)],
        body: data.map(row => headers.map(h => row[h.key])),
        startY: 35,
        theme: 'grid',
        styles: { 
          fontSize: 9,
          cellPadding: 2,
          valign: 'middle'
        },
        headStyles: { 
          fillColor: [41, 128, 185],
          textColor: 255,
          fontStyle: 'bold'
        },
        alternateRowStyles: {
          fillColor: [245, 245, 245]
        },
        margin: { left: 10, right: 10 }
      });

      doc.save(`${filename}.pdf`);
    },
    computeAverageScores() {
      const scoresBySubject = {};
      const countsBySubject = {};
      this.quizList.forEach(sub => {
        const subject = sub.subject_name || "Unknown";
        scoresBySubject[subject] = (scoresBySubject[subject] || 0) + sub.score;
        countsBySubject[subject] = (countsBySubject[subject] || 0) + 1;
      });
      const averages = {};
      Object.keys(scoresBySubject).forEach(subject => {
        averages[subject] = (scoresBySubject[subject] / countsBySubject[subject]).toFixed(2);
      });
      this.averageScoresBySubject = averages;
    },
    getAuthHeaders() {
      const token = localStorage.getItem("token");
      return {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      };
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString();
    },
    getRandomColor() {
      const letters = "0123456789ABCDEF";
      let color = "#";
      for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
      }
      return color;
    }
  },
  async mounted() {
    const user = JSON.parse(localStorage.getItem("user") || "{}");
    this.isAdmin = user.role === "admin";
    if (!this.isAdmin) {
      await this.fetchQuizList();
      await this.fetchUserCharts();
    } else {
      await this.fetchAdminUserDetails();
      await this.fetchAdminCharts();
      this.adminActiveTab = "details";
    }
  }
};
</script>

<style scoped>
.report-dashboard {
  padding: 20px;
  font-family: Arial, sans-serif;
}
h1 {
  margin-bottom: 20px;
  text-align: center;
}
.tabs {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  gap: 15px;
}
.tabs button {
  padding: 10px 20px;
  border: none;
  background: #f2f2f2;
  cursor: pointer;
  font-size: 1.1rem;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}
.tabs button.active {
  background: #ffffff;
  border-color: #3498db;
  color: #3498db;
  font-weight: bold;
}
.export-buttons {
  margin-bottom: 15px;
  text-align: right;
}
.export-buttons button {
  margin-left: 10px;
  padding: 8px 16px;
  background-color: #3498db;
  border: none;
  color: #fff;
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.3s ease;
}
.export-buttons button:hover {
  background-color: #2980b9;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
table th,
table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}
table th {
  background: #f2f2f2;
}
.charts-wrapper {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.left-charts {
  flex: 1 1 60%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.right-charts {
  flex: 1 1 35%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.chart-container {
  position: relative;
  text-align: center;
  border: 1px solid #eee;
  padding: 10px;
  background: #fafafa;
}
.small-chart {
  height: 300px;
}
.pie-chart-container {
  height: 400px;
}
.bar-chart-container {
  margin-top: 150px; 
}
.total-number {
  font-size: 1.1rem;
  font-weight: bold;
  margin-bottom: 5px;
}
</style>
