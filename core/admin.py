from django.contrib import admin
from .models import (
    Contact, Lead, LandDeal, FollowUp, Activity, 
    Project, Site, Transaction, ExpenseCategory, Expense, 
    SharedPurpose, SharedExpense, ExpenseSplit, Settlement, Document
)

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
