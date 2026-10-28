from django.contrib import admin
from django.urls import path
from packing import api

urlpatterns=[
    path('admin/',admin.site.urls),
    path('api/session/',api.session),path('api/catalog/',api.catalog),
    path('api/employees/',api.employee_create),
    path('api/users/',api.users),path('api/users/<int:pk>/',api.user_detail),
    path('api/balance/',api.balance),path('api/captures/',api.captures),
    path('api/analytics/',api.analytics),
    path('api/captures/<int:pk>/<str:action>/',api.capture_action),
    path('api/programs/',api.programs),path('api/programs/<int:pk>/publication/',api.program_action),
    path('api/programs/<int:pk>/',api.program_detail),
    path('api/demands/<int:pk>/revise/',api.revise),path('api/transfer/',api.transfer),
    path('api/demands/<int:pk>/',api.demand_detail),
    path('api/surplus/apply/',api.apply_surplus),
    path('api/surplus/',api.surplus_inventory),
    path('api/imports/',api.imports),path('api/imports/<int:pk>/',api.import_detail),
    path('api/cuts/',api.cuts),path('api/cuts/<int:pk>/',api.cut_detail),path('api/reopen/',api.reopen),
    path('api/audit/',api.audit),path('api/universe/sync/',api.sync),
    path('api/export/',api.export),path('api/template/',api.template),path('api/production-export/',api.production_export),
]
