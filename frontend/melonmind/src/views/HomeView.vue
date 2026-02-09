<template>
  <div class="dashboard">
    <div class="row">
      <div class="col-lg-3 col-sm-6">
        <div class="card gradient-1">
          <div class="card-body">
            <h3 class="card-title text-white">Documents Loaded</h3>
            <div class="d-inline-block">
              <h2 class="text-white">{{ stats.processed_documents }}</h2>
              <p class="text-white mb-0">Total PDFs Processed</p>
            </div>
            <!-- <div class="float-right display-5 opacity-5">
              <i class="fa fa-file-pdf"></i>
            </div> -->

          </div>
        </div>
      </div>
      <div class="col-lg-3 col-sm-6">
        <div class="card gradient-2">
          <div class="card-body">
            <h3 class="card-title text-white">Total Documents</h3>
            <div class="d-inline-block">
              <h2 class="text-white">{{ stats.total_documents }}</h2>
              <p class="text-white mb-0">In Knowledge Base</p>
            </div>
            <!-- <div class="float-right display-5 opacity-5">
              <i class="fa fa-files-o"></i>
            </div> -->

          </div>
        </div>
      </div>
      <div class="col-lg-3 col-sm-6">
        <div class="card gradient-3">
          <div class="card-body">
            <h3 class="card-title text-white">Processing</h3>
            <div class="d-inline-block">
              <h2 class="text-white">{{ stats.processing_documents }}</h2>
              <p class="text-white mb-0">Documents Processing</p>
            </div>
            <!-- <div class="float-right display-5 opacity-5">
              <i class="fa fa-spinner"></i>
            </div> -->

          </div>
        </div>
      </div>
      <div class="col-lg-3 col-sm-6">
        <div class="card gradient-4">
          <div class="card-body">
            <h3 class="card-title text-white">Failed Documents</h3>
            <div class="d-inline-block">
              <h2 class="text-white">{{ stats.failed_documents }}</h2>
              <p class="text-white mb-0">Processing Failures</p>
            </div>
            <!-- <div class="float-right display-5 opacity-5">
              <i class="fa fa-exclamation-triangle"></i>
            </div> -->

          </div>
        </div>
      </div>
      <div class="col-lg-3 col-sm-6">
        <div class="card gradient-5">
          <div class="card-body">
            <h3 class="card-title text-white">Uploaded</h3>
            <div class="d-inline-block">
              <h2 class="text-white">{{ stats.uploaded_documents }}</h2>
              <p class="text-white mb-0">Documents Uploaded</p>
            </div>
            <!-- <div class="float-right display-5 opacity-5">
              <i class="fa fa-upload"></i>
            </div> -->

          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-12">
        <div class="card">
          <div class="card-body pb-0 d-flex justify-content-between">
            <div>
              <h4 class="mb-1">Processing Activity</h4>
              <p>Recent document processing events</p>
              <h3 class="m-0">Status: Operational</h3>
            </div>
            <div>
              <ul>
                <li class="d-inline-block mr-3"><a class="text-dark" href="#">Day</a></li>
                <li class="d-inline-block mr-3"><a class="text-dark" href="#">Week</a></li>
                <li class="d-inline-block"><a class="text-dark" href="#">Month</a></li>
              </ul>
            </div>
          </div>
          <div class="chart-wrapper">
            <canvas id="chart_widget_2"></canvas>
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col-lg-6 col-md-12">
        <div class="card">
          <div class="card-body">
            <h4 class="card-title">Document Processing Summary</h4>
            <div id="processing-summary-chart">
              <!-- 图表占位符 -->
              <p>Processing summary chart would appear here</p>
            </div>
          </div>
        </div>
      </div>
      <div class="col-lg-6 col-md-12">
        <div class="card card-widget">
          <div class="card-body">
            <h5 class="text-muted">System Status</h5>
            <h2 class="mt-4">Operational</h2>
            <span>Current System Status</span>
            <div class="mt-4">
              <h4>95%</h4>
              <h6>PDF Processing Success Rate <span class="pull-right">95%</span></h6>
              <div class="progress mb-3" style="height: 7px">
                <div class="progress-bar bg-primary" style="width: 95%;" role="progressbar">
                  <span class="sr-only">95% Success Rate</span>
                </div>
              </div>
            </div>
            <div class="mt-4">
              <h4>98%</h4>
              <h6 class="m-t-10 text-muted">Vector Database Uptime <span class="pull-right">98%</span></h6>
              <div class="progress mb-3" style="height: 7px">
                <div class="progress-bar bg-success" style="width: 98%;" role="progressbar">
                  <span class="sr-only">98% Uptime</span>
                </div>
              </div>
            </div>
            <div class="mt-4">
              <h4>92%</h4>
              <h6 class="m-t-10 text-muted">API Response Time <span class="pull-right">92%</span></h6>
              <div class="progress mb-3" style="height: 7px">
                <div class="progress-bar bg-warning" style="width: 92%;" role="progressbar">
                  <span class="sr-only">92% Performance</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { knowledgeBaseAPI } from '@/services/api';

export default {
  name: 'HomeView',
  setup() {
    const stats = ref({
      total_documents: 0,
      processed_documents: 0,
      processing_documents: 0,
      failed_documents: 0,
      uploaded_documents: 0,
    });
    
    const loadingStats = ref(true);
    
    const loadDocumentStats = async () => {
      try {
        loadingStats.value = true;
        const response = await knowledgeBaseAPI.getDocumentStats();
        stats.value = response.data || stats.value;
      } catch (error) {
        console.error('Error fetching document stats:', error);
        // 设置默认值以防API调用失败
        stats.value = {
          total_documents: 0,
          processed_documents: 0,
          processing_documents: 0,
          failed_documents: 0,
          uploaded_documents: 0,
        };
      } finally {
        loadingStats.value = false;
      }
    };
    
    onMounted(async () => {
      await loadDocumentStats();
    });
    
    return {
      stats,
      loadingStats,
      loadDocumentStats
    };
  }
};
</script>

<style scoped>
.dashboard {
  padding: 20px 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 60vh;
  flex-direction: column;
}

.loading-spinner {
  text-align: center;
}

.loading-spinner i {
  font-size: 3rem;
  color: #3498DB;
  margin-bottom: 1rem;
}

.loading-spinner p {
  color: #666;
  font-size: 1.1rem;
}

.gradient-1 {
  background: linear-gradient(45deg,#6a11cb,#2575fc);
}

.gradient-2 {
  background: linear-gradient(45deg,#fc5286,#fbaaa2);
}

.gradient-3 {
  background: linear-gradient(45deg,#f7971e,#ffd200);
}

.gradient-4 {
  background: linear-gradient(45deg,#57d66c,#56f8ac);
}

.gradient-5 {
  background: linear-gradient(45deg,#ff9a9e,#fad0c4);
}

.card {
  border: none;
  border-radius: 4px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.1);
  margin-bottom: 25px;
}

.card-body {
  padding: 1.25rem;
}

.text-white {
  color: #fff !important;
}

.display-5 {
  font-size: 2.5rem;
  font-weight: 300;
  line-height: 1.2;
}

.opacity-5 {
  opacity: .5;
}

.fa {
  display: inline-block;
  font: normal normal normal 14px/1 FontAwesome;
  font-size: inherit;
  text-rendering: auto;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.fa-file-pdf::before { content: "\f1c1"; }
.fa-files-o::before { content: "\f0c5"; }
.fa-spinner::before { content: "\f110"; }
.fa-exclamation-triangle::before { content: "\f071"; }
.fa-upload::before { content: "\f093"; }

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 -10px;
}

.col-lg-3, .col-lg-6, .col-sm-6, .col-md-12 {
  position: relative;
  width: 100%;
  padding: 0 10px;
  flex: 0 0 auto;
}

.col-lg-3 { flex: 0 0 20%; max-width: 20%; min-width: 100px; }
.col-lg-6 { flex: 0 0 50%; max-width: 50%; }
.col-sm-6 { flex: 0 0 20%; max-width: 20%; min-width: 100px; }
.col-md-12 { flex: 0 0 100%; max-width: 100%; }

@media (max-width: 991px) {
  .col-lg-3, .col-lg-6 {
    flex: 0 0 100%;
    max-width: 100%;
  }
}
</style>