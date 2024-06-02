from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    index,
    UserAuthViewset,
    UserPDF,
    PdfModuleInfo,
    CoverPageModuleViewset,            # Module No. 1
    IntroductionModuleViewset,         # Module No. 2
    FamilyMembersModelViewset,         # Module No. 3
    CoreValueModuleViewset,            # Module No. 4
    VisionStatementModuleViewset,      # Module No. 5
    MissionStatementModuleViewset,     # Module No. 6
    CodeOfConductModelViewset,         # Module No. 7
    FamilyMediaAggrementModelViewset,  # Module No. 8
    FamilyConstitutionModelViewset,    # Module No. 9
    FamilyBookSummaryModelViewset      # Module No. 10
)

router = DefaultRouter()
router.register("auth", UserAuthViewset, basename="auth")
router.register("pdf/coverpage", CoverPageModuleViewset, basename="coverpage")
router.register("pdf/intoduction", IntroductionModuleViewset, basename="intoduction")
router.register("pdf/familymembers", FamilyMembersModelViewset, basename="familymembers")
router.register("pdf/core_value", CoreValueModuleViewset, basename="core_value")
router.register("pdf/vision_stat", VisionStatementModuleViewset, basename="vision_stat")
router.register("pdf/mission_stat", MissionStatementModuleViewset, basename="mission_stat")
router.register("pdf/code_of_conduct", CodeOfConductModelViewset, basename="code_of_conduct")
router.register("pdf/family_media_aggrement", FamilyMediaAggrementModelViewset, basename="family_media_aggrement")
router.register("pdf/family_constitution", FamilyConstitutionModelViewset, basename="family_constitution")
router.register("pdf/summary", FamilyBookSummaryModelViewset, basename="summary")

urlpatterns = [
    path("", index),
    path("pdf", UserPDF.as_view()),
    path("pdfinfo", PdfModuleInfo.as_view())
]

urlpatterns += router.urls
