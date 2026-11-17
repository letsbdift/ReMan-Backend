from datetime import date
from .models import FollowUp, Lead, LandDeal, Expense, Site

def alerts_context(request):
    if not request.user.is_authenticated:
        return {'active_alerts_count': 0}
    try:
        today = date.today()
        overdue_followups = FollowUp.objects.filter(status='Pending', date__lte=today).count()
        overdue_leads = Lead.objects.filter(next_follow_up__date__lte=today).exclude(status__in=['Converted', 'Not Interested', 'Lost']).count()
        overdue_deals = LandDeal.objects.filter(next_follow_up__date__lte=today).exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost']).count()
        pending_expenses = Expense.objects.filter(status='To Be Paid').count()
        
        total_alerts = overdue_followups + overdue_leads + overdue_deals + pending_expenses
        return {
            'active_alerts_count': total_alerts,
            'overdue_alerts_count': overdue_followups + overdue_leads + overdue_deals,
            'pending_expenses_count': pending_expenses
        }
    except Exception:
        return {'active_alerts_count': 0}
