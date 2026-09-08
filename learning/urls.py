from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('path/', views.learning_path_view, name='learning_path'),
    path('courses/', views.course_list_view, name='course_list'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    path('upload/', views.pdf_upload_view, name='pdf_upload'),
    path('materials/', views.material_list_view, name='material_list'),
    path('material/<int:material_id>/', views.material_detail_view, name='material_detail'),
]
