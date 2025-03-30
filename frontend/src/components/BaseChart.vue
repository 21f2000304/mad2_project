<template>
    <div>
      <canvas ref="canvas"></canvas>
    </div>
  </template>
  
  <script>
  import { Chart, registerables } from "chart.js";
  Chart.register(...registerables);
  
  export default {
    name: "BaseChart",
    props: {
      chartData: { type: Object, required: true },
      chartOptions: { type: Object, default: () => ({ responsive: true }) },
      chartType: { type: String, default: "bar" }
    },
    mounted() {
      this.renderChart();
    },
    methods: {
      renderChart() {
        new Chart(this.$refs.canvas, {
          type: this.chartType,
          data: this.chartData,
          options: this.chartOptions
        });
      }
    }
  };
  </script>
  