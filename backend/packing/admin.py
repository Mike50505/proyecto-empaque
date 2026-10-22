from django.contrib import admin
from .models import *

for model in [BalanceGroup,Employee,Shift]: admin.site.register(model)

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display=['number','customer','scope','universe_id','provisional']
    search_fields=['number','customer']

# El ledger se consulta en administración; sus cambios pasan por servicios auditados.
class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
for model in [Program,Demand,Capture,Allocation,OpeningBalance,Revision,Audit,WeekTransfer,ImportBatch,Snapshot,ClosedPeriod,CorrectionRequest,IntegrationState]: admin.site.register(model,ReadOnlyAdmin)
