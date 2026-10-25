from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Contact(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    CONTACT_TYPES = [
        ('Landowner', 'Landowner'),
        ('Broker', 'Broker'),
        ('Customer', 'Customer'),
        ('Partner', 'Partner'),
        ('Contractor', 'Contractor'),
        ('Vendor', 'Vendor'),
        ('Investor', 'Investor'),
        ('Other', 'Other')
    ]
    name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20, db_index=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    contact_type = models.CharField(max_length=50, choices=CONTACT_TYPES)
    ownership_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Used for automated profit distribution")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.contact_type})"

class Lead(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    STATUS_CHOICES = [
        ('New', 'New'), ('Contacted', 'Contacted'), ('Follow-up', 'Follow-up'), 
        ('Interested', 'Interested'), ('Negotiation', 'Negotiation'), 
        ('Converted', 'Converted'), ('Not Interested', 'Not Interested'), ('Lost', 'Lost')
    ]
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    lead_type = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    interested_property = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='New')
    next_follow_up = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.status}"

class LandDeal(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    STATUS_CHOICES = [
        ('New', 'New'), ('Discussion', 'Discussion'), ('Property Visit', 'Property Visit'),
        ('Documents Pending', 'Documents Pending'), ('Verification', 'Verification'),
        ('Negotiation', 'Negotiation'), ('Advance Paid', 'Advance Paid'), 
        ('Agreement', 'Agreement'), ('Deal Closed', 'Deal Closed'), 
        ('Deal Cancelled', 'Deal Cancelled'), ('Deal Lost', 'Deal Lost')
    ]
    deal_name = models.CharField(max_length=255)
    landowner = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, related_name='land_deals')
    broker = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, related_name='brokered_deals')
    location = models.CharField(max_length=255)
    survey_number = models.CharField(max_length=100, blank=True, null=True)
    land_area = models.CharField(max_length=100)
    expected_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    offered_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    negotiated_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='New')
    next_follow_up = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.deal_name

class FollowUp(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    STATUS_CHOICES = [
        ('Pending', 'Pending'), ('Completed', 'Completed'), 
        ('Rescheduled', 'Rescheduled'), ('Cancelled', 'Cancelled')
    ]
    # Simple reference instead of complex GenericForeignKey for minimal setup
    related_to = models.CharField(max_length=255, help_text="E.g., Contact: John, Deal: Sunrise Land")
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    reason = models.CharField(max_length=255)
    note = models.TextField(blank=True, null=True)
    next_action = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.related_to} - {self.date}"

class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('Call', 'Call'), ('WhatsApp', 'WhatsApp'), ('Meeting', 'Meeting'),
        ('Property Visit', 'Property Visit'), ('Transaction', 'Transaction'), 
        ('Document', 'Document'), ('Negotiation', 'Negotiation'), 
        ('Note', 'Note'), ('Other', 'Other')
    ]
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    related_to = models.CharField(max_length=255)
    date = models.DateTimeField(default=timezone.now)
    note = models.TextField()

    def __str__(self):
        return f"{self.activity_type} on {self.date.date()}"

class Project(models.Model):
    STATUS_CHOICES = [
        ('Planning', 'Planning'), ('Land Purchased', 'Land Purchased'),
        ('Approval', 'Approval'), ('Development', 'Development'),
        ('Ready for Sale', 'Ready for Sale'), ('Sales in Progress', 'Sales in Progress'),
        ('Completed', 'Completed'), ('On Hold', 'On Hold')
    ]
    project_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    landowner = models.ForeignKey('Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='landowner_projects')
    survey_number = models.CharField(max_length=100, blank=True, null=True)
    land_area = models.CharField(max_length=100)
    purchase_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    development_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Planning')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    @property
    def total_sites(self):
        return self.sites.count()

    @property
    def expected_revenue(self):
        return sum(site.price for site in self.sites.all() if site.price)

    def __str__(self):
        return self.project_name

class Site(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'), ('Blocked', 'Blocked'), 
        ('Booked', 'Booked'), ('Sold', 'Sold'), ('Cancelled', 'Cancelled')
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sites')
    site_number = models.CharField(max_length=50)
    area = models.CharField(max_length=100)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    facing = models.CharField(max_length=50, blank=True, null=True)
    road_width = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Available')
    customer = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True)
    amount_received = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        was_sold = False
        if not is_new:
            old = Site.objects.get(pk=self.pk)
            was_sold = (old.status == 'Sold')

        super().save(*args, **kwargs)

        if self.status == 'Sold' and not was_sold:
            Transaction.objects.create(
                project=self.project,
                contact=self.customer,
                transaction_type='Received',
                payment_type='Site Sale',
                amount=self.price,
                project_or_deal=f"Site {self.site_number}",
                notes="Auto-generated receipt for sold site"
            )

    def __str__(self):
        return f"{self.project.project_name} - Site {self.site_number}"

class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'), ('UPI', 'UPI'),
        ('NEFT', 'NEFT'), ('IMPS', 'IMPS'), ('RTGS', 'RTGS'), ('Quick Transfer', 'Quick Transfer')
    ]
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    PAYMENT_TYPES = [
        ('Land Advance', 'Land Advance'), ('Land Purchase', 'Land Purchase'),
        ('Customer Payment', 'Customer Payment'), ('Booking Installment', 'Booking Installment'),
        ('Site Sold', 'Site Sold'), ('Token Advance', 'Token Advance'),
        ('Development Charges', 'Development Charges'), ('Registration Fees', 'Registration Fees'),
        ('Broker Payment', 'Broker Payment'),
        ('Contract Payment', 'Contract Payment'), ('Vendor Payment', 'Vendor Payment'), 
        ('Refund', 'Refund'), ('Other', 'Other')
    ]
    date = models.DateField(default=timezone.now)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Contact/Person")
    project_or_deal = models.CharField(max_length=255, blank=True, null=True)
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('Paid', 'Paid'), ('Received', 'Received')])
    received_by = models.CharField(max_length=150, blank=True, null=True)
    payment_type_other_reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Completed')
    attachments = models.FileField(upload_to='transactions/', blank=True, null=True)
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHODS, blank=True, null=True)
    paid_by = models.CharField(max_length=150, blank=True, null=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('To Be Paid', 'To Be Paid'), ('Paid', 'Paid')], default='Paid')

    def __str__(self):
        contact_name = self.contact.name if self.contact else (self.paid_by or 'No Contact')
        return f"{self.transaction_type} {self.amount} - {contact_name}"

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Expense(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'), ('Cheque', 'Cheque'), ('UPI', 'UPI'),
        ('NEFT', 'NEFT'), ('IMPS', 'IMPS'), ('RTGS', 'RTGS'), ('Quick Transfer', 'Quick Transfer')
    ]
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    project_or_deal = models.CharField(max_length=255, blank=True, null=True)
    paid_to = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    payment_method = models.CharField(max_length=100, choices=PAYMENT_METHODS, blank=True, null=True)
    paid_by = models.CharField(max_length=150, blank=True, null=True)
    receipt = models.FileField(upload_to='receipts/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('To Be Paid', 'To Be Paid'), ('Paid', 'Paid')], default='Paid')

    def __str__(self):
        return f"{self.amount} - {self.category}"

# --- SPLITWISE-STYLE SHARED EXPENSES ---

class SharedPurpose(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    participants = models.ManyToManyField(Contact, related_name='shared_purposes')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
        
    def get_balances(self):
        balances = {p: Decimal('0.00') for p in self.participants.all()}
        
        # Add amounts paid by each participant
        for expense in self.expenses.all():
            if expense.paid_by in balances:
                balances[expense.paid_by] += expense.total_amount
            
            # Subtract amounts owed by each participant
            for split in expense.splits.all():
                if split.participant in balances:
                    balances[split.participant] -= split.amount
                    
        # Apply settlements
        for settlement in self.settlements.all():
            if settlement.from_person in balances:
                balances[settlement.from_person] += settlement.amount
            if settlement.to_person in balances:
                balances[settlement.to_person] -= settlement.amount
                
        return balances

class SharedExpense(models.Model):
    SPLIT_METHODS = [
        ('Equal', 'Equal split'),
        ('Exact', 'Exact amount'),
        ('Percentage', 'Percentage')
    ]
    purpose = models.ForeignKey(SharedPurpose, on_delete=models.CASCADE, related_name='expenses')
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    paid_by = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='expenses_paid')
    split_method = models.CharField(max_length=50, choices=SPLIT_METHODS, default='Equal')
    notes = models.TextField(blank=True, null=True)
    receipt = models.FileField(upload_to='shared_receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} - {self.total_amount}"

class ExpenseSplit(models.Model):
    shared_expense = models.ForeignKey(SharedExpense, on_delete=models.CASCADE, related_name='splits')
    participant = models.ForeignKey(Contact, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.participant.name} - {self.amount}"

class Settlement(models.Model):
    purpose = models.ForeignKey(SharedPurpose, on_delete=models.CASCADE, related_name='settlements', null=True, blank=True)
    from_person = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='settlements_sent')
    to_person = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='settlements_received')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=100, blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.from_person} paid {self.to_person} {self.amount}"

class Document(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    related_to = models.CharField(max_length=255, help_text="E.g., Deal: Sunrise Land, Site: 101")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- Activity Logging Signals ---
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=SharedExpense)
def log_shared_expense(sender, instance, created, **kwargs):
    action = "Added" if created else "Updated"
    desc = getattr(instance, 'description', 'Transaction')
    Activity.objects.create(activity_type='Other', note=f"{action} shared expense: {desc} (₹{instance.total_amount})")

@receiver(post_save, sender=Settlement)
def log_settlement(sender, instance, created, **kwargs):
    if created:
        Activity.objects.create(activity_type="Transaction", related_to="Settlement", note=f"{instance.from_person.name} paid {instance.to_person.name} ₹{instance.amount}")

@receiver(post_save, sender=SharedPurpose)
def log_purpose(sender, instance, created, **kwargs):
    if created:
        Activity.objects.create(activity_type="Other", related_to="Expense Group", note=f"Created new expense title: {instance.name}")

@receiver(post_save, sender=Expense)
def log_expense(sender, instance, created, **kwargs):
    action = "Added" if created else "Updated"
    Activity.objects.create(activity_type="Transaction", related_to="Business Expense", note=f"{action} business expense: {instance.description} (₹{instance.amount})")

@receiver(post_save, sender=Transaction)
def log_payment(sender, instance, created, **kwargs):
    action = "Received" if created else "Updated"
    Activity.objects.create(activity_type="Transaction", related_to="Transaction", note=f"{action} transaction of ₹{instance.amount}")

@receiver(post_save, sender=LandDeal)
def log_deal(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    Activity.objects.create(activity_type="Other", related_to="Land Deal", note=f"{action} land deal: {instance.deal_name}")

# Automation: Auto-instantiate and link a new Project when Land Deal status is 'Deal Closed' or 'Closed'
@receiver(post_save, sender=LandDeal)
def handle_closed_land_deal(sender, instance, created, **kwargs):
    is_closed = instance.status in ['Deal Closed', 'Closed']
    if is_closed and not instance.project:
        cost = instance.negotiated_price or instance.expected_price or Decimal('0.00')
        existing_proj = Project.objects.filter(project_name__iexact=instance.deal_name).first()
        if not existing_proj:
            existing_proj = Project.objects.create(
                project_name=instance.deal_name,
                location=instance.location or "Site Location",
                landowner=instance.landowner,
                survey_number=instance.survey_number,
                land_area=instance.land_area or "N/A",
                purchase_cost=cost,
                status='Planning',
                notes=f"Auto-created from closed deal: {instance.deal_name}. {instance.notes or ''}".strip()
            )
            Activity.objects.create(
                activity_type="Project",
                related_to=existing_proj.project_name,
                note=f"Auto-instantiated project '{existing_proj.project_name}' from closed deal"
            )
        LandDeal.objects.filter(pk=instance.pk, project__isnull=True).update(project=existing_proj)

# Automation: Auto-trigger linked Deal/Contact entry when Lead is Converted or Closed
@receiver(post_save, sender=Lead)
def handle_converted_lead(sender, instance, created, **kwargs):
    is_converted = instance.status in ['Converted', 'Closed']
    if is_converted:
        contact = None
        if instance.phone:
            contact = Contact.objects.filter(mobile=instance.phone).first()
        if not contact and instance.name:
            contact = Contact.objects.filter(name__iexact=instance.name).first()
            
        if not contact:
            contact = Contact.objects.create(
                name=instance.name,
                mobile=instance.phone,
                location=instance.location or "",
                contact_type="Customer",
                project=instance.project,
                notes=f"Auto-created from converted lead. Source: {instance.source or 'Lead'}. {instance.notes or ''}".strip()
            )
            Activity.objects.create(
                activity_type="Contact",
                related_to=contact.name,
                note=f"Auto-created contact '{contact.name}' from converted lead"
            )

        deal_title = f"Deal - {instance.name}"
        existing_deal = LandDeal.objects.filter(deal_name__iexact=deal_title).first()
        if not existing_deal:
            new_deal = LandDeal.objects.create(
                deal_name=deal_title,
                project=instance.project,
                landowner=contact,
                location=instance.location or (instance.project.location if instance.project else "Local"),
                land_area="N/A",
                expected_price=Decimal('0.00'),
                status='Discussion',
                notes=f"Auto-created deal entry from converted lead: {instance.name}. {instance.notes or ''}".strip()
            )
            Activity.objects.create(
                activity_type="Land Deal",
                related_to=new_deal.deal_name,
                note=f"Auto-created deal '{new_deal.deal_name}' in pipeline for converted lead"
            )

from django.db.models.signals import post_delete

@receiver(post_delete, sender=SharedExpense)
def log_shared_expense_delete(sender, instance, **kwargs):
    desc = getattr(instance, 'description', 'Transaction')
    Activity.objects.create(activity_type="Transaction", related_to="Shared Expense", note=f"Deleted shared expense: {desc} (₹{instance.total_amount})")


from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

@receiver(pre_save, sender=Expense)
def expense_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Expense.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Expense.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Expense)
def create_transaction_on_paid(sender, instance, created, **kwargs):
    # If it is created as Paid, or changed to Paid from something else
    is_newly_paid = False
    if created and instance.status == 'Paid':
        is_newly_paid = True
    elif not created and getattr(instance, '_old_status', None) != 'Paid' and instance.status == 'Paid':
        is_newly_paid = True
        
    if is_newly_paid:
        reason = f"Expense: {instance.category.name if instance.category else 'Uncategorized'} - {instance.description}"
        if not Transaction.objects.filter(project=instance.project, amount=instance.amount, date=instance.date, transaction_type='Paid', payment_type_other_reason=reason).exists():
            Transaction.objects.create(
                project=instance.project,
                date=instance.date,
                amount=instance.amount,
                transaction_type='Paid',
                payment_type='Other',
                payment_type_other_reason=reason,
                paid_by=instance.paid_by,
                notes=instance.notes
            )


class UnearnedRevenue(models.Model):
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='unearned_revenues')
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    payment_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Transferred', 'Transferred')], default='Pending')

    def transfer_to_revenue(self):
        if self.status == 'Pending':
            Transaction.objects.create(
                transaction_type='Received',
                amount=self.amount,
                date=self.payment_date,
                paid_by=getattr(self.site, 'customer_name', 'Customer'),
                reference=f"Transfer from Unearned Revenue - Site {self.site.site_number}",
                notes="Automatic transfer from booking"
            )
            self.status = 'Transferred'
            self.save()

    def __str__(self):
        return f"Unearned - Site {self.site.site_number} - {self.amount}"
