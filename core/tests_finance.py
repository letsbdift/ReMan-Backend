from django.test import TestCase
from decimal import Decimal
from core.models import Transaction, Expense, Contact, Project, ExpenseCategory

class FinancialAnalyticsTest(TestCase):
    def setUp(self):
        # Create Partners
        self.p1 = Contact.objects.create(name="Partner A", contact_type="Partner", mobile="111")
        self.p2 = Contact.objects.create(name="Partner B", contact_type="Partner", mobile="222")
        self.p3 = Contact.objects.create(name="Partner C", contact_type="Partner", mobile="333")
        
        self.proj = Project.objects.create(project_name="Test Project", location="Test")
        self.cat = ExpenseCategory.objects.create(name="Land")
        
        # Investments:
        # A invests 450,000 (Transaction)
        Transaction.objects.create(project=self.proj, paid_by="Partner A", amount=Decimal('450000'), transaction_type="Paid", payment_type="Other")
        # B invests 300,000 (Expense)
        Expense.objects.create(project=self.proj, paid_by="Partner B", amount=Decimal('300000'), category=self.cat, description="Land")
        # C invests 150,000 (Transaction)
        Transaction.objects.create(project=self.proj, paid_by="Partner C", amount=Decimal('150000'), transaction_type="Paid", payment_type="Other")
        
    def test_partner_analytics_logic(self):
        from decimal import Decimal
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        
        all_partners = Contact.objects.filter(contact_type='Partner').order_by('name')
        N_partners = all_partners.count()
        total_partnership_investment = Decimal('0.00')
        partner_stats = []
        
        for p in all_partners:
            p_pay = Transaction.objects.filter(paid_by__icontains=p.name).aggregate(t=Coalesce(Sum('amount'), Decimal('0.00')))['t']
            p_exp = Expense.objects.filter(paid_by__icontains=p.name).aggregate(t=Coalesce(Sum('amount'), Decimal('0.00')))['t']
            invested = p_pay + p_exp
            received = Transaction.objects.filter(contact=p, transaction_type='Paid').aggregate(t=Coalesce(Sum('amount'), Decimal('0.00')))['t']
            
            total_partnership_investment += invested
            partner_stats.append({
                'name': p.name,
                'invested': invested,
                'received': received,
                'net_position': invested - received
            })
            
        self.assertEqual(total_partnership_investment, Decimal('900000'))
        
        expected = total_partnership_investment / N_partners
        self.assertEqual(expected, Decimal('300000'))
        
        # Partner A balance
        a_stat = next(s for s in partner_stats if s['name'] == 'Partner A')
        self.assertEqual(a_stat['invested'], Decimal('450000'))
        self.assertEqual(a_stat['net_position'] - expected, Decimal('150000'))
        
        # Partner C balance
        c_stat = next(s for s in partner_stats if s['name'] == 'Partner C')
        self.assertEqual(c_stat['invested'], Decimal('150000'))
        self.assertEqual(c_stat['net_position'] - expected, Decimal('-150000'))
        
    def test_settlement_reconciliation(self):
        debtors = [{'name': 'C', 'amount': Decimal('150000')}]
        creditors = [{'name': 'A', 'amount': Decimal('150000')}]
        
        settlements = []
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            d = debtors[i]
            c = creditors[j]
            transfer = min(d['amount'], c['amount'])
            
            if transfer > 0:
                settlements.append({'from': d['name'], 'to': c['name'], 'amount': transfer})
                
            d['amount'] -= transfer
            c['amount'] -= transfer
            if d['amount'] <= 0: i += 1
            if c['amount'] <= 0: j += 1
            
        self.assertEqual(len(settlements), 1)
        self.assertEqual(settlements[0]['amount'], Decimal('150000'))
        self.assertEqual(settlements[0]['from'], 'C')
        self.assertEqual(settlements[0]['to'], 'A')
