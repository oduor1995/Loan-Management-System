# church_management/reportbuilder_urls.py
from django.urls import path, include
from rest_framework import routers
from django.contrib.admin.views.decorators import staff_member_required

# Correct imports
from report_builder.api import views as api_views
from report_builder import views as rb_views

router = routers.DefaultRouter()

# Use unique basenames:
router.register(r'reports', api_views.ReportViewSet, basename='reports')
router.register(r'report-nested', api_views.ReportNestedViewSet, basename='report-nested')
router.register(r'formats', api_views.FormatViewSet, basename='formats')
router.register(r'filterfields', api_views.FilterFieldViewSet, basename='filterfields')
router.register(r'contenttypes', api_views.ContentTypeViewSet, basename='contenttypes')

urlpatterns = [
    # Main SPA page
    path('', staff_member_required(rb_views.ReportSPAView.as_view()), name='report_builder_home'),
    path('', include(router.urls)),
]
