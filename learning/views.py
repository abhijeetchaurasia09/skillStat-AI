from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Course, LearningMaterial, Recommendation
from .forms import PDFUploadForm
from .services import RecommendationService, IGOTIntegrationService
from competency.services import CompetencyService
from ai_engine.services import PDFExtractionService

@login_required
def learning_path_view(request):
    """
    Renders the user's personalized learning path, prioritized strictly by identified skill gaps.
    Features explainable AI cards detailing WHY each course was recommended.
    """
    recommendations = RecommendationService.get_personalized_learning_path(request.user)
    skill_gaps = CompetencyService.get_skill_gaps(request.user)
    igot_status = IGOTIntegrationService.get_connection_status()

    return render(request, 'learning/learning_path.html', {
        'recommendations': recommendations,
        'skill_gaps': skill_gaps,
        'igot_status': igot_status,
    })


@login_required
def course_list_view(request):
    """
    Browse all courses across competencies.
    """
    courses = Course.objects.filter(is_active=True).select_related('skill')
    return render(request, 'learning/course_list.html', {
        'courses': courses,
    })


@login_required
def course_detail_view(request, course_id):
    """
    Details of a specific course, its linked competency, learning materials, and AI Quiz generator CTA.
    """
    course = get_object_or_404(Course, id=course_id)
    materials = LearningMaterial.objects.filter(course=course)
    recommendation = Recommendation.objects.filter(user=request.user, course=course).first()

    return render(request, 'learning/course_detail.html', {
        'course': course,
        'materials': materials,
        'recommendation': recommendation,
    })


@login_required
def pdf_upload_view(request):
    """
    Uploads learning material (PDF), validates format and file size,
    extracts text via pypdf with robust error trapping, and saves extracted content.
    """
    if request.method == 'POST':
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.user = request.user
            material.save()

            # Execute text extraction using pypdf service
            extraction = PDFExtractionService.extract_text(material.file)
            
            material.extraction_status = extraction['status']
            material.page_count = extraction.get('page_count', 0)
            material.extracted_text = extraction.get('text', '')
            material.extraction_error = extraction.get('error') or ''
            material.save()

            if extraction['success']:
                messages.success(
                    request,
                    f"PDF uploaded and parsed successfully! Extracted {extraction['word_count']} words across {extraction['page_count']} pages."
                )
                return redirect('learning:material_detail', material_id=material.id)
            elif extraction['status'] == 'empty':
                messages.warning(
                    request,
                    f"PDF uploaded, but no readable text could be extracted. It may contain scanned images. {extraction.get('error', '')}"
                )
                return redirect('learning:material_detail', material_id=material.id)
            else:
                messages.error(
                    request,
                    f"PDF upload completed, but text extraction failed: {extraction.get('error', 'Unknown error')}"
                )
                return redirect('learning:material_detail', material_id=material.id)
        else:
            messages.error(request, "Failed to upload document. Please check the errors below.")
    else:
        form = PDFUploadForm()

    return render(request, 'learning/pdf_upload.html', {'form': form})


@login_required
def material_list_view(request):
    """
    Lists all uploaded learning materials and documents.
    """
    materials = LearningMaterial.objects.all().select_related('skill', 'course', 'user')
    return render(request, 'learning/material_list.html', {
        'materials': materials,
    })


@login_required
def material_detail_view(request, material_id):
    """
    Displays extracted text preview, extraction health status, and quick AI MCQ generation trigger.
    """
    material = get_object_or_404(LearningMaterial, id=material_id)
    return render(request, 'learning/material_detail.html', {
        'material': material,
    })
