from django.urls import path
from . import views

app_name = 'pdfloader'

urlpatterns = [
    # PDF文档管理
    path('documents/', views.PDFDocumentListView.as_view(), name='pdf-document-list'),
    path('documents/<int:pk>/', views.PDFDocumentDetailView.as_view(), name='pdf-document-detail'),
    path('documents/<int:pk>/chunks/', views.PDFDocumentChunksView.as_view(), name='pdf-document-chunks'),
    
    # PDF处理相关
    path('upload/', views.PDFUploadView.as_view(), name='pdf-upload'),
    path('documents/<int:pk>/status/', views.PDFProcessingStatusView.as_view(), name='pdf-processing-status'),
    
    # 向量搜索
    path('search/', views.VectorSearchView.as_view(), name='vector-search'),
    path('collections/<str:collection_name>/info/', views.PDFCollectionInfoView.as_view(), name='collection-info'),
]