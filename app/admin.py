from django.contrib import admin
from django.contrib.admin.decorators import register
from simple_history.admin import SimpleHistoryAdmin

from app.models import (
    Appointment,
    Customer,
    CustomerPhoto,
    Job,
    JobIssue,
    JobNote,
    JobPhoto,
    JobType,
    Address,
    Pro,
    ProBusiness,
    SupplyHouse,
    MaterialList,
)

admin.site.site_header = 'HomeBreeze Administration'
admin.site.register(Address, SimpleHistoryAdmin)
admin.site.register(Customer, SimpleHistoryAdmin)
admin.site.register(CustomerPhoto, SimpleHistoryAdmin)
admin.site.register(ProBusiness, SimpleHistoryAdmin)
admin.site.register(SupplyHouse, SimpleHistoryAdmin)
admin.site.register(Pro, SimpleHistoryAdmin)
admin.site.register(JobIssue, SimpleHistoryAdmin)
admin.site.register(JobNote, SimpleHistoryAdmin)


class JobPhotoInline(admin.TabularInline):
    model = JobPhoto
    extra = 1
    readonly_fields = ('thumbnail',)


class JobAdmin(admin.ModelAdmin):
    inlines = [
        JobPhotoInline
    ]


admin.site.register(Job, JobAdmin)
admin.site.register(JobType, SimpleHistoryAdmin)
admin.site.register(Appointment, SimpleHistoryAdmin)
admin.site.register(MaterialList, SimpleHistoryAdmin)
