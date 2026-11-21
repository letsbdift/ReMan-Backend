from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Contact, Lead, LandDeal, FollowUp, Activity, 
    Project, Site, Transaction, ExpenseCategory, Expense, 
    SharedPurpose, SharedExpense, ExpenseSplit, Settlement, Document,
    UserProfile
)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Role & Permissions'

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_role', 'is_staff', 'is_superuser')

    def get_role(self, obj):
        return getattr(obj, 'profile', None).role if hasattr(obj, 'profile') else 'Viewer'
    get_role.short_description = 'Assigned Role'

admin.site.register(UserProfile)
admin.site.register(Contact)
admin.site.register(Lead)
admin.site.register(LandDeal)
admin.site.register(FollowUp)
admin.site.register(Activity)
admin.site.register(Project)
admin.site.register(Site)
admin.site.register(Transaction)
admin.site.register(ExpenseCategory)
admin.site.register(Expense)
admin.site.register(SharedPurpose)
admin.site.register(SharedExpense)
admin.site.register(ExpenseSplit)
admin.site.register(Settlement)
admin.site.register(Document)
