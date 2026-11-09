from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import (
    Site, 
    Contact, Lead, LandDeal, FollowUp, Activity, 
    Transaction, Expense, SharedPurpose, SharedExpense, Settlement, SitePayment, PartnerCapitalLedger, EXPENSE_CATEGORIES
)
from django.db.models import Sum
from datetime import date, timedelta

@login_required
def dashboard(request):
    from datetime import date
    from django.db.models import Sum, Count, Q
    from decimal import Decimal
    from django.db.models.functions import Coalesce
    today = date.today()
    
    project_id = request.GET.get('project_id')
    all_projects = Project.objects.all().order_by("-id")
    selected_project = None
    
    overdue_f = FollowUp.objects.filter(status='Pending', date__lt=today)
    overdue_l = Lead.objects.filter(next_follow_up__date__lt=today).exclude(status__in=['Closed', 'Lost', 'Lost to Competitor'])
    overdue_d = LandDeal.objects.filter(next_follow_up__date__lt=today).exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost'])
    
    today_f = FollowUp.objects.filter(status='Pending', date=today)
    today_l = Lead.objects.filter(next_follow_up__date=today).exclude(status__in=['Closed', 'Lost', 'Lost to Competitor'])
    today_d = LandDeal.objects.filter(next_follow_up__date=today).exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost'])

    active_deals = LandDeal.objects.exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost'])
    projects_progress_qs = Project.objects.annotate(
        total_units=Count('sites'),
        sold_units=Count('sites', filter=Q(sites__status='Sold'))
    ).all()
    
    recent_transactions = Transaction.objects.all().order_by('-transaction_date', '-created_at')
    total_received_qs = Transaction.objects.filter(transaction_type='Received')
    total_paid_qs = Transaction.objects.filter(transaction_type='Paid')
    
    base_transactions = Transaction.objects.all()
    base_expenses = Expense.objects.all()
    recent_activities = Activity.objects.all().order_by('-date', '-id')

    if project_id and project_id != 'all':
        selected_project = Project.objects.filter(pk=project_id).first()
        if selected_project:
            overdue_f = overdue_f.filter(project=selected_project)
            overdue_l = overdue_l.filter(project=selected_project)
            overdue_d = overdue_d.filter(project=selected_project)
            
            today_f = today_f.filter(project=selected_project)
            today_l = today_l.filter(project=selected_project)
            today_d = today_d.filter(project=selected_project)
            
            active_deals = active_deals.filter(project=selected_project)
            projects_progress_qs = projects_progress_qs.filter(pk=selected_project.pk)
            
            recent_transactions = recent_transactions.filter(project=selected_project)
            total_received_qs = total_received_qs.filter(project=selected_project)
            total_paid_qs = total_paid_qs.filter(project=selected_project)
            base_transactions = base_transactions.filter(project=selected_project)
            base_expenses = base_expenses.filter(project=selected_project)
            
            # Since Activity doesn't have project link yet, we just show all or none. 
            # We'll leave recent_activities as is, or filter by text temporarily
            # A better way is to filter activities if they mention project name, but let's just keep global for now.

    overdue_items = []
    for f in overdue_f: overdue_items.append({'date': f.date, 'title': f.related_to, 'type': 'Follow-up', 'reason': f.reason, 'url': f'/followups/{f.pk}/edit/'})
    for l in overdue_l: overdue_items.append({'date': l.next_follow_up.date(), 'title': getattr(l, 'name', 'Lead') or 'Lead', 'type': 'Lead', 'reason': 'Scheduled Lead Follow-up', 'url': f'/leads/{l.pk}/edit/'})
    for d in overdue_d: overdue_items.append({'date': d.next_follow_up.date(), 'title': d.deal_name, 'type': 'Land Deal', 'reason': 'Scheduled Deal Follow-up', 'url': f'/deals/{d.pk}/edit/'})

    today_items = []
    for f in today_f: today_items.append({'title': f.related_to, 'type': 'Follow-up', 'reason': f.reason, 'url': f'/followups/{f.pk}/edit/'})
    for l in today_l: today_items.append({'title': getattr(l, 'name', 'Lead') or 'Lead', 'type': 'Lead', 'reason': 'Scheduled Lead Follow-up', 'url': f'/leads/{l.pk}/edit/'})
    for d in today_d: today_items.append({'title': d.deal_name, 'type': 'Land Deal', 'reason': 'Scheduled Deal Follow-up', 'url': f'/deals/{d.pk}/edit/'})
    
    overdue_items.sort(key=lambda x: x['date'])
    today_count = len(today_items)
    overdue_count = len(overdue_items)

    
    active_deals = LandDeal.objects.exclude(status__in=['Deal Closed', 'Deal Cancelled', 'Deal Lost'])
    deal_pipeline = active_deals.aggregate(total=Coalesce(Sum('negotiated_price'), Sum('expected_price'), Decimal('0.00')))['total']
    site_pipeline = Site.objects.filter(status__in=['Booked', 'Blocked']).aggregate(total=Coalesce(Sum('price'), Decimal('0.00')))['total']
    pipeline_value = deal_pipeline + site_pipeline
    
    total_sites = Site.objects.count()
    sold_sites = Site.objects.filter(status='Sold').count()
    available_sites = Site.objects.filter(status='Available').count()
    booked_sites = Site.objects.filter(status='Booked').count()
    blocked_sites = Site.objects.filter(status='Blocked').count()
    total_leads = Lead.objects.count()
    total_deals = LandDeal.objects.count()
    conversion_rate = 0
    if total_leads > 0:
        conversion_rate = int((total_deals / total_leads) * 100)

    if project_id and project_id != 'all':
        deal_pipeline = active_deals.filter(project=selected_project).aggregate(total=Coalesce(Sum('negotiated_price'), Sum('expected_price'), Decimal('0.00')))['total']
        site_pipeline = Site.objects.filter(project=selected_project, status__in=['Booked', 'Blocked']).aggregate(total=Coalesce(Sum('price'), Decimal('0.00')))['total']
        pipeline_value = deal_pipeline + site_pipeline
        total_sites = Site.objects.filter(project=selected_project).count()
        sold_sites = Site.objects.filter(project=selected_project, status='Sold').count()
        available_sites = Site.objects.filter(project=selected_project, status='Available').count()
        booked_sites = Site.objects.filter(project=selected_project, status='Booked').count()
        blocked_sites = Site.objects.filter(project=selected_project, status='Blocked').count()
        
        total_leads_proj = Lead.objects.filter(project=selected_project).count()
        total_deals_proj = LandDeal.objects.filter(project=selected_project).count()
        if total_leads_proj > 0:
            conversion_rate = int((total_deals_proj / total_leads_proj) * 100)

    deal_stages = active_deals.values('status').annotate(count=Count('id'))

    project_progress = []
    for p in projects_progress_qs:
        pct = 0
        if p.total_units > 0:
            pct = int((p.sold_units / p.total_units) * 100)
        project_progress.append({
            'name': p.project_name,
            'status': p.status,
            'pct': pct,
            'sold': p.sold_units,
            'total': p.total_units
        })

    recent_transactions = recent_transactions[:5]
    total_received = total_received_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    # Total Paid should be Transaction(Paid) + Expense(Paid)
    total_paid = total_paid_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    # Expenses are now automatically converted to Transactions when Paid, so total_paid includes them naturally.
    
    
    pending_payables = base_expenses.filter(status='To Be Paid').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']

    
    recent_activities = recent_activities[:8]
    # --- ACCURATE FINANCIAL CALCULATIONS ---
    # Total Revenue = Sum of all 'Received' site sale payments and receivables
    total_revenue = total_received_qs.aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # Total Expenses = Sum of all paid project/development/advance expenses + paid shared expenses
    paid_expenses = base_expenses.filter(status__iexact='Paid').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    shared_qs = SharedExpense.objects.all()
    if selected_project:
        shared_qs = shared_qs.filter(purpose__project=selected_project)
    paid_shared_expenses = shared_qs.aggregate(total=Coalesce(Sum('total_amount'), Decimal('0.00')))['total']
    total_expenses = paid_expenses + paid_shared_expenses
    total_expenses_all = total_expenses
    
    # Net Profit = Total Revenue - Total Expenses
    calculated_net_profit = total_revenue - total_expenses
    pending_payables = base_expenses.exclude(status__iexact='Paid').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # --- PARTNER FINANCIAL ANALYTICS ---
    all_partners = Contact.objects.filter(contact_type='Partner').order_by('name')
    N_partners = all_partners.count()
    partner_stats = []
    total_partnership_investment = Decimal('0.00')
    total_partnership_receipts = Decimal('0.00')
    
    for p in all_partners:
        invested = base_transactions.filter(transaction_type='Paid', paid_by__icontains=p.name).aggregate(t=Coalesce(Sum('amount'), Decimal('0.00')))['t']
        received = base_transactions.filter(transaction_type='Received', paid_by__icontains=p.name).aggregate(t=Coalesce(Sum('amount'), Decimal('0.00')))['t']
        
        total_partnership_investment += invested
        total_partnership_receipts += received
        
        # Calculate profit share based on ownership percentage
        ownership = getattr(p, 'ownership_percentage', Decimal('0.00'))
        if ownership is None:
            ownership = Decimal('0.00')
        if ownership == 0 and N_partners > 0:
            # Fallback to equal split if no percentages are set
            profit_share = calculated_net_profit / N_partners
        else:
            profit_share = calculated_net_profit * (ownership / Decimal('100.0'))
            
        partner_stats.append({
            'name': p.name,
            'invested': invested,
            'received': received,
            'profit_share': profit_share,
            'net_position': invested - received,
            'balance': Decimal('0.00'),
            'expected': Decimal('0.00'),
            'status': '',
            'amount_due': Decimal('0.00')
        })
        
    expected_contribution = (total_partnership_investment / N_partners) if N_partners > 0 else Decimal('0.00')
    
    debtors = []
    creditors = []
    
    for stat in partner_stats:
        stat['expected'] = expected_contribution
        balance = stat['net_position'] - expected_contribution
        stat['balance'] = balance
        stat['amount_due'] = abs(balance)
        
        if balance > Decimal('0.01'):
            stat['status'] = f"Should Receive ₹{balance:,.2f}"
            creditors.append({'name': stat['name'], 'amount': balance})
        elif balance < Decimal('-0.01'):
            stat['status'] = f"Owes ₹{abs(balance):,.2f}"
            debtors.append({'name': stat['name'], 'amount': abs(balance)})
        else:
            stat['status'] = "Balanced"
            
    settlements = []
    debtors.sort(key=lambda x: x['amount'], reverse=True)
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    
    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        d = debtors[i]
        c = creditors[j]
        transfer = min(d['amount'], c['amount'])
        
        if transfer > Decimal('0.01'):
            settlements.append({'from': d['name'], 'to': c['name'], 'amount': transfer})
            
        d['amount'] -= transfer
        c['amount'] -= transfer
        
        if d['amount'] <= Decimal('0.01'): i += 1
        if c['amount'] <= Decimal('0.01'): j += 1
        
    # Category totals (Django ORM)
    category_totals = list(base_expenses.exclude(status__iexact='Paid').values('category').annotate(total=Coalesce(Sum('amount'), Decimal('0.00'))).order_by('-total'))
    cat_dict = dict(EXPENSE_CATEGORIES)
    category_labels = [cat_dict.get(c['category'], c['category']) or 'Other' for c in category_totals]
    category_values = [float(c['total']) for c in category_totals]
    
    # Partner Chart Data
    partner_labels = [s['name'] for s in partner_stats]
    partner_invested_values = [float(s['invested']) for s in partner_stats]
    partner_received_values = [float(s['received']) for s in partner_stats]
    partner_profit_values = [float(max(s.get('profit_share', 0), 0)) for s in partner_stats]

    context = {
        'all_projects': all_projects,
        'selected_project': selected_project,
        'overdue_items': overdue_items,
        'today_items': today_items,
        'today_count': today_count,
        'overdue_count': overdue_count,
        

        'partner_stats': partner_stats,
        'total_partnership_investment': total_partnership_investment,
        'expected_contribution': expected_contribution,
        'settlements': settlements,
        'category_totals': category_totals,
        'category_labels': category_labels,
        'category_values': category_values,
        'partner_labels': partner_labels,
        'partner_invested_values': partner_invested_values,
        'partner_received_values': partner_received_values,
        'partner_profit_values': partner_profit_values,
        'pipeline_value': pipeline_value,
        'total_sites': total_sites,
        'sold_sites': sold_sites,
        'available_sites': available_sites,
        'booked_sites': booked_sites,
        'blocked_sites': blocked_sites,
        'conversion_rate': conversion_rate,
        'active_deals': active_deals,

        'deal_stages': deal_stages,
        'project_progress': project_progress,
        'recent_transactions': recent_transactions,
        'total_received': total_received or 0,
        'total_revenue': total_received or 0,
        'total_paid': total_paid or 0,
        'total_expenses': total_expenses_all or 0,
        'total_expenses_all': total_expenses_all or 0,
        'net_profit': calculated_net_profit,
        'pending_payables': pending_payables or 0,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard.html', context)



@login_required
def contact_list(request):
    project_id = request.GET.get('project_id', 'all')
    contact_type = request.GET.get('contact_type', 'all')
    q = request.GET.get('q', '')
    
    contacts = Contact.objects.all().order_by('-id')
    if project_id and project_id != 'all':
        contacts = contacts.filter(project_id=project_id)
    if contact_type and contact_type != 'all':
        contacts = contacts.filter(contact_type=contact_type)
    if q:
        from django.db.models import Q
        contacts = contacts.filter(Q(name__icontains=q) | Q(mobile__icontains=q) | Q(email__icontains=q))
        
    all_projects = Project.objects.all().order_by('-id')
    
    # Get distinct contact types for the dropdown
    contact_types = Contact.objects.values_list('contact_type', flat=True).distinct()
    # Filter out empty strings/None
    contact_types = [ct for ct in contact_types if ct]
    
    return render(request, 'core/contact_list.html', {
        'contacts': contacts, 
        'all_projects': all_projects, 
        'contact_types': contact_types,
        'selected_project_id': str(project_id),
        'selected_contact_type': contact_type,
        'search_q': q
    })


@login_required
def lead_list(request):
    leads = Lead.objects.all().order_by("-id")
    return render(request, 'core/lead_list.html', {'leads': leads})

@login_required
@login_required
def deal_list(request):
    project_id = request.GET.get('project_id', 'all')
    deals = LandDeal.objects.all().order_by('-created_at', '-id')
    if project_id and project_id != 'all':
        deals = deals.filter(project_id=project_id)
    all_projects = Project.objects.all().order_by("-id")
    return render(request, 'core/deal_list.html', {
        'deals': deals, 
        'all_projects': all_projects, 
        'selected_project_id': str(project_id)
    })




@login_required
def expense_list(request):
    project_id = request.GET.get('project_id', 'all')
    paid_by_name = request.GET.get('paid_by_name', 'all')
    category = request.GET.get('category') or request.GET.get('category_id', 'all')
    
    expenses = Expense.objects.all().order_by('-expense_date', '-id')
    
    if project_id and project_id != 'all':
        expenses = expenses.filter(project_id=project_id)
    if paid_by_name and paid_by_name != 'all':
        expenses = expenses.filter(paid_by__icontains=paid_by_name)
    if category and category != 'all':
        expenses = expenses.filter(category=category)
        
    from django.db.models import Sum
    from decimal import Decimal
    grand_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
    all_projects = Project.objects.all().order_by('-id')
    all_partners = Contact.objects.filter(contact_type='Partner').order_by('name')
    all_categories = EXPENSE_CATEGORIES
    
    return render(request, 'core/expense_list.html', {
        'expenses': expenses, 
        'all_projects': all_projects, 
        'all_categories': all_categories,
        'all_partners': all_partners,
        'selected_project_id': str(project_id),
        'selected_paid_by_name': paid_by_name,
        'selected_category': str(category),
        'selected_category_id': str(category),
        'grand_total': grand_total
    })




@login_required
def shared_expense_list(request):
    project_id = request.GET.get('project_id', 'all')
    purposes = SharedPurpose.objects.all().order_by('-created_at', '-id')
    if project_id and project_id != 'all':
        purposes = purposes.filter(project_id=project_id)
        
    from decimal import Decimal
    balances = {}
    for p in purposes:
        p_balances = p.get_balances()
        for contact, bal in p_balances.items():
            balances[contact] = balances.get(contact, Decimal('0.00')) + bal
            
    debtors = []
    creditors = []
    for contact, bal in balances.items():
        if bal < -0.01:
            debtors.append({'contact': contact, 'amount': abs(bal)})
        elif bal > 0.01:
            creditors.append({'contact': contact, 'amount': bal})
            
    all_projects = Project.objects.all().order_by("-id")
    return render(request, 'core/shared_expense_list.html', {
        'purposes': purposes,
        'debtors': debtors,
        'creditors': creditors,
        'all_projects': all_projects,
        'selected_project_id': str(project_id)
    })


from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy

class ProjectFilteredListView(ListView):
    def get_queryset(self):
        qs = super().get_queryset().order_by("-id")
        project_id = self.request.GET.get('project_id', 'all')
        if project_id and project_id != 'all':
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['all_projects'] = Project.objects.all().order_by("-id")
        ctx['selected_project_id'] = self.request.GET.get('project_id', 'all')
        return ctx

from .forms import *

class BaseCRUDView:
    template_name = 'core/generic_form.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        return context

    def get_initial(self):
        initial = super().get_initial()
        project_id = self.request.GET.get('project_id')
        if project_id and project_id != 'all':
            initial['project'] = project_id
        return initial

class ContactCreate(BaseCRUDView, CreateView): model = Contact; form_class = ContactForm; success_url = reverse_lazy('contact_list')
class ContactUpdate(BaseCRUDView, UpdateView): model = Contact; form_class = ContactForm; success_url = reverse_lazy('contact_list')

class LeadCreate(BaseCRUDView, CreateView): model = Lead; form_class = LeadForm; success_url = reverse_lazy('lead_list')
class LeadUpdate(BaseCRUDView, UpdateView): model = Lead; form_class = LeadForm; success_url = reverse_lazy('lead_list')

class LandDealCreate(BaseCRUDView, CreateView): model = LandDeal; form_class = LandDealForm; success_url = reverse_lazy('deal_list')
class LandDealUpdate(BaseCRUDView, UpdateView): model = LandDeal; form_class = LandDealForm; success_url = reverse_lazy('deal_list')

class FollowUpList(ProjectFilteredListView): model = FollowUp; template_name = 'core/followup_list.html'; context_object_name = 'followups'
class FollowUpCreate(BaseCRUDView, CreateView): model = FollowUp; form_class = FollowUpForm; success_url = reverse_lazy('followup_list')
class FollowUpUpdate(BaseCRUDView, UpdateView): model = FollowUp; form_class = FollowUpForm; success_url = reverse_lazy('followup_list')

class ProjectList(ListView): model = Project; template_name = 'core/project_list.html'; context_object_name = 'projects'
class ProjectCreate(BaseCRUDView, CreateView): model = Project; form_class = ProjectForm; success_url = reverse_lazy('project_list')
class ProjectUpdate(BaseCRUDView, UpdateView): model = Project; form_class = ProjectForm; success_url = reverse_lazy('project_list')




class TransactionList(ListView):
    model = Transaction
    template_name = 'core/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        qs = Transaction.objects.all().order_by('-transaction_date', '-created_at')
        project_id = self.request.GET.get('project_id', 'all')
        transaction_type = self.request.GET.get('transaction_type', 'all')
        partner_name = self.request.GET.get('partner_name', 'all')
        payment_method = self.request.GET.get('payment_method', 'all')
        
        if project_id and project_id != 'all':
            qs = qs.filter(project_id=project_id)
        if transaction_type and transaction_type != 'all':
            qs = qs.filter(transaction_type=transaction_type)
        if partner_name and partner_name != 'all':
            from django.db.models import Q
            qs = qs.filter(Q(paid_by__icontains=partner_name) | Q(contact__name__icontains=partner_name))
        if payment_method and payment_method != 'all':
            qs = qs.filter(payment_method=payment_method)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        
        # Dynamic Grand Total
        qs = self.get_queryset()
        from django.db.models import Sum
        from decimal import Decimal
        ctx['grand_total'] = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        ctx['all_projects'] = Project.objects.all().order_by('-id')
        ctx['all_partners'] = Contact.objects.filter(contact_type='Partner').order_by('name')
        ctx['selected_transaction_type'] = self.request.GET.get('transaction_type', 'all')
        ctx['selected_partner_name'] = self.request.GET.get('partner_name', 'all')
        ctx['selected_project_id'] = self.request.GET.get('project_id', 'all')
        ctx['selected_payment_method'] = self.request.GET.get('payment_method', 'all')
        ctx['selected_project_id'] = self.request.GET.get('project_id', 'all')
        ctx['selected_paid_by_name'] = self.request.GET.get('paid_by_name', 'all')
        ctx['selected_payment_method'] = self.request.GET.get('payment_method', 'all')
        return ctx



class TransactionCreate(BaseCRUDView, CreateView): model = Transaction; form_class = TransactionForm; success_url = reverse_lazy('transaction_list'); template_name = 'core/transaction_form.html'
class TransactionUpdate(BaseCRUDView, UpdateView): model = Transaction; form_class = TransactionForm; success_url = reverse_lazy('transaction_list'); template_name = 'core/transaction_form.html'

class ExpenseCreate(BaseCRUDView, CreateView): model = Expense; form_class = ExpenseForm; success_url = reverse_lazy('expense_list')
class ExpenseUpdate(BaseCRUDView, UpdateView): model = Expense; form_class = ExpenseForm; success_url = reverse_lazy('expense_list')

class DocumentList(ProjectFilteredListView): model = Document; template_name = 'core/document_list.html'; context_object_name = 'object_list'
class DocumentCreate(BaseCRUDView, CreateView): model = Document; form_class = DocumentForm; success_url = reverse_lazy('document_list')
class DocumentUpdate(BaseCRUDView, UpdateView): model = Document; form_class = DocumentForm; success_url = reverse_lazy('document_list')



class SharedExpenseCreate(BaseCRUDView, CreateView): 
    model = SharedExpense
    form_class = SharedExpenseForm
    success_url = reverse_lazy('shared_expense_list')
    
    def get_initial(self):
        initial = super().get_initial()
        purpose_id = self.request.GET.get('purpose')
        if purpose_id:
            initial['purpose'] = purpose_id
            initial['description'] = 'Recurring Payment'
            initial['split_method'] = 'Equal'
            from datetime import date
            initial['date'] = date.today()
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        expense = self.object
        final_parts = getattr(expense, '_final_participants', [])
        if not final_parts:
            final_parts = list(expense.purpose.participants.all())
            
        if expense.split_method == 'Equal' and final_parts:
            expense.splits.all().delete()
            split_amount = expense.total_amount / len(final_parts)
            for p in final_parts:
                ExpenseSplit.objects.create(shared_expense=expense, participant=p, amount=split_amount)
        elif expense.split_method == 'Exact':
            custom_splits_str = form.cleaned_data.get('custom_splits', '')
            expense.splits.all().delete()
            if custom_splits_str:
                pairs = custom_splits_str.split(',')
                for pair in pairs:
                    if ':' in pair:
                        name, amt = pair.split(':')
                        name = name.strip()
                        amt = amt.strip()
                        try:
                            amount = float(amt)
                            contact = Contact.objects.filter(name__iexact=name).first()
                            if contact:
                                ExpenseSplit.objects.create(shared_expense=expense, participant=contact, amount=amount)
                        except ValueError:
                            pass
        return response
        return response

class SharedExpenseUpdate(BaseCRUDView, UpdateView):
    model = SharedExpense
    form_class = SharedExpenseForm
    success_url = reverse_lazy('shared_expense_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        expense = self.object
        final_parts = getattr(expense, '_final_participants', [])
        if not final_parts:
            final_parts = list(expense.purpose.participants.all())
            
        if expense.split_method == 'Equal' and final_parts:
            expense.splits.all().delete()
            split_amount = expense.total_amount / len(final_parts)
            for p in final_parts:
                ExpenseSplit.objects.create(shared_expense=expense, participant=p, amount=split_amount)
        elif expense.split_method == 'Exact':
            custom_splits_str = form.cleaned_data.get('custom_splits', '')
            expense.splits.all().delete()
            if custom_splits_str:
                pairs = custom_splits_str.split(',')
                for pair in pairs:
                    if ':' in pair:
                        name, amt = pair.split(':')
                        name = name.strip()
                        amt = amt.strip()
                        try:
                            amount = float(amt)
                            contact = Contact.objects.filter(name__iexact=name).first()
                            if contact:
                                ExpenseSplit.objects.create(shared_expense=expense, participant=contact, amount=amount)
                        except ValueError:
                            pass
        return response
        return response

    
    def form_valid(self, form):
        response = super().form_valid(form)
        expense = self.object
        # Automatically split equally among purpose participants
        if expense.split_method == 'Equal':
            participants = expense.purpose.participants.all()
            if participants.count() > 0:
                split_amount = expense.total_amount / participants.count()
                for p in participants:
                    ExpenseSplit.objects.create(shared_expense=expense, participant=p, amount=split_amount)
        return response

class SharedExpenseUpdate(BaseCRUDView, UpdateView):
    model = SharedExpense
    form_class = SharedExpenseForm
    success_url = reverse_lazy('shared_expense_list')

class SettlementCreate(BaseCRUDView, CreateView):
    model = Settlement
    form_class = SettlementForm
    success_url = reverse_lazy('shared_expense_list')

from django.views.generic.detail import DetailView


class SharedPurposeUpdate(BaseCRUDView, UpdateView):
    model = SharedPurpose
    form_class = SharedPurposeForm
    success_url = reverse_lazy('shared_expense_list')

class SharedPurposeDelete(DeleteView):
    model = SharedPurpose
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('shared_expense_list')

class SharedPurposeDetailView(DetailView):
    model = SharedPurpose
    template_name = 'core/shared_purpose_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.object
        summary = []
        total_expenses = 0
        
        for p in group.participants.all():
            paid = sum(exp.total_amount for exp in group.expenses.filter(paid_by=p))
            share = sum(split.amount for exp in group.expenses.all() for split in exp.splits.filter(participant=p))
            
            net = paid - share
            status = "Settled"
            balance = 0
            if net > 0.01:
                status = "Receivable"
                balance = round(net, 2)
            elif net < -0.01:
                status = "Owes"
                balance = round(abs(net), 2)
                
            summary.append({
                'participant': p,
                'paid': round(paid, 2),
                'share': round(share, 2),
                'status': status,
                'balance': balance
            })
            total_expenses += paid
            
        context['summary'] = summary
        context['total_expenses'] = round(total_expenses, 2)
        return context


class SharedExpenseDelete(BaseCRUDView, DeleteView):
    model = SharedExpense
    template_name = 'core/generic_confirm_delete.html'
    success_url = reverse_lazy('shared_expense_list')

@login_required
def expense_delete_all(request):
    if request.method == 'POST':
        # Delete all expenses
        from .models import Site, Expense, Activity
        Expense.objects.all().delete()
        Activity.objects.create(activity_type="Payment", related_to="Business Expense", note="Deleted ALL business expenses in one go.")
        messages.success(request, "All expenses and their history have been deleted.")
    return redirect('expense_list')

class SiteList(ProjectFilteredListView):
    model = Site
    template_name = 'core/site_list.html'
    context_object_name = 'sites'
    
    def get_queryset(self):
        qs = super().get_queryset().order_by("-added_date", "site_number")
        status = self.request.GET.get('status', 'All')
        if status != 'All':
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['selected_status'] = self.request.GET.get('status', 'All')
        ctx['recent_site_payments'] = SitePayment.objects.all().order_by('-payment_date', '-id')[:10]
        return ctx

class SiteCreate(BaseCRUDView, CreateView):
    model = Site
    template_name = 'core/site_form.html'
    form_class = SiteForm
    success_url = reverse_lazy('site_list')

    def form_valid(self, form):
        site = form.save(commit=False)
        from datetime import date
        today = date.today()
        if site.status == 'Booked' and not site.booking_date:
            site.booking_date = today
        elif site.status == 'Sold' and not site.sold_date:
            site.sold_date = today
            if not site.booking_date:
                site.booking_date = today
        site.save()
        return super().form_valid(form)

class SiteUpdate(BaseCRUDView, UpdateView):
    model = Site
    template_name = 'core/site_form.html'
    form_class = SiteForm
    success_url = reverse_lazy('site_list')

    def form_valid(self, form):
        site = form.save(commit=False)
        from datetime import date
        today = date.today()
        if site.status == 'Booked' and not site.booking_date:
            site.booking_date = today
        elif site.status == 'Sold' and not site.sold_date:
            site.sold_date = today
            if not site.booking_date:
                site.booking_date = today
        site.save()
        return super().form_valid(form)

class SitePaymentCreate(BaseCRUDView, CreateView):
    model = SitePayment
    template_name = 'core/site_payment_form.html'
    form_class = SitePaymentForm
    success_url = reverse_lazy('site_list')

    def get_initial(self):
        initial = super().get_initial()
        site_id = self.kwargs.get('site_id') or self.request.GET.get('site_id')
        if site_id:
            site = Site.objects.filter(pk=site_id).first()
            if site:
                initial['site'] = site
                if site.customer:
                    initial['customer'] = site.customer
                    initial['paid_by'] = site.customer.name
                if site.balance:
                    initial['amount'] = site.balance
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        site_id = self.kwargs.get('site_id') or self.request.GET.get('site_id')
        if site_id:
            ctx['site_obj'] = Site.objects.filter(pk=site_id).first()
        return ctx

class SitePaymentList(ListView):
    model = SitePayment
    template_name = 'core/site_payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        qs = SitePayment.objects.all().order_by('-payment_date', '-id')
        site_id = self.request.GET.get('site_id')
        if site_id and site_id != 'all':
            qs = qs.filter(site_id=site_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.db.models import Sum
        from decimal import Decimal
        qs = self.get_queryset()
        ctx['grand_total'] = qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        ctx['all_sites'] = Site.objects.all().order_by('site_number')
        ctx['selected_site_id'] = self.request.GET.get('site_id', 'all')
        return ctx

from django.urls import reverse_lazy

class ProjectFilteredListView(ListView):
    def get_queryset(self):
        qs = super().get_queryset().order_by("-id")
        project_id = self.request.GET.get('project_id', 'all')
        if project_id and project_id != 'all':
            qs = qs.filter(project_id=project_id)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['all_projects'] = Project.objects.all().order_by("-id")
        ctx['selected_project_id'] = self.request.GET.get('project_id', 'all')
        return ctx


class SiteDelete(DeleteView): model = Site; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('site_list')
class ContactDelete(DeleteView): model = Contact; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('contact_list')
class LeadDelete(DeleteView): model = Lead; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('lead_list')
class DocumentDelete(DeleteView): model = Document; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('document_list')
class LandDealDelete(DeleteView): model = LandDeal; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('deal_list')
class FollowUpDelete(DeleteView): model = FollowUp; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('followup_list')
class ProjectDelete(DeleteView): model = Project; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('project_list')
class TransactionDelete(DeleteView): model = Transaction; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('transaction_list')
class ExpenseDelete(DeleteView): model = Expense; template_name = 'core/generic_confirm_delete.html'; success_url = reverse_lazy('expense_list')

def pwa_manifest(request):
    from django.http import JsonResponse
    return JsonResponse({
        "name": "RE Manager",
        "short_name": "RE Manager",
        "description": "Real Estate Site Inventory Management System",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#0d6efd",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    })

def pwa_icon_192(request):
    from django.http import HttpResponse
    import base64
    return HttpResponse(base64.b64decode(b"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"), content_type="image/png")

def pwa_icon_512(request):
    from django.http import HttpResponse
    import base64
    return HttpResponse(base64.b64decode(b"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"), content_type="image/png")

from django.contrib import messages
from django.shortcuts import redirect

@login_required
def site_import(request):
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        file = request.FILES.get('file')
        
        if not project_id or project_id == 'all':
            messages.error(request, "Please select a specific project before importing.")
            return redirect('site_list')
            
        if not file:
            messages.error(request, "Please upload a file.")
            return redirect('site_list')
            
        project = Project.objects.get(pk=project_id)
        
        try:
            import pandas as pd
            df = pd.read_excel(file)
            
            # Expected columns: site_number, dimensions, total_area, price_per_sqft, status
            created_count = 0
            for index, row in df.iterrows():
                site_num = str(row.get('site_number', '')).strip()
                if not site_num or site_num == 'nan':
                    continue
                    
                # Create or update site
                site, created = Site.objects.get_or_create(
                    project=project,
                    site_number=site_num,
                    defaults={
                        'area': str(row.get('area', '')).strip() if pd.notna(row.get('area')) else '0',
                        'dimensions': str(row.get('dimensions', '')).strip() if pd.notna(row.get('dimensions')) else '',
                        'facing': str(row.get('facing', '')).strip() if pd.notna(row.get('facing')) else '',
                        'road_width': str(row.get('road_width', '')).strip() if pd.notna(row.get('road_width')) else '',
                        'price': row.get('price', 0) if pd.notna(row.get('price')) else 0,
                        'status': str(row.get('status', 'Available')).strip() if pd.notna(row.get('status')) else 'Available'
                    }
                )
                if created:
                    created_count += 1
                    
            messages.success(request, f"Successfully imported {created_count} sites into {project.project_name}.")
            
        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            
    return redirect(f"/sites/?project_id={request.POST.get('project_id', 'all')}")

from django.http import HttpResponse
import csv

@login_required
def site_import_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="site_import_template.csv"'

    writer = csv.writer(response)
    # Header row exactly matching the expected pandas columns
    writer.writerow(['site_number', 'area', 'dimensions', 'facing', 'road_width', 'price', 'status'])
    
    # Couple of sample rows
    writer.writerow(['A-101', '1200', '30x40', 'East', '30ft', '2400000', 'Available'])
    writer.writerow(['A-102', '1500', '30x50', 'West', '40ft', '3000000', 'Blocked'])
    writer.writerow(['B-201', '2400', '40x60', 'North', '30ft', '4800000', 'Available'])

    return response

class ActivityList(ListView):
    model = Activity
    template_name = 'core/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 50
    def get_queryset(self):
        return Activity.objects.all().order_by('-date', '-id')

@login_required
def global_search(request):
    query = request.GET.get('q', '')
    results = {}
    if query:
        results['contacts'] = Contact.objects.filter(Q(name__icontains=query) | Q(mobile__icontains=query) | Q(company__icontains=query))[:10]
        results['deals'] = LandDeal.objects.filter(Q(deal_name__icontains=query) | Q(location__icontains=query))[:10]
        results['sites'] = Site.objects.filter(Q(site_number__icontains=query) | Q(customer__name__icontains=query))[:10]
        results['projects'] = Project.objects.filter(Q(project_name__icontains=query) | Q(location__icontains=query))[:10]
    return render(request, 'core/search_results.html', {'query': query, 'results': results})
