from django import forms
from datetime import date
from .models import *

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                pass
            else:
                field.widget.attrs['class'] = 'form-control'
                if isinstance(field, forms.DateTimeField):
                    field.widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'})
                elif isinstance(field, forms.DateField):
                    field.widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                    if not self.initial.get(field_name):
                        if not self.instance or not self.instance.pk:
                            self.initial[field_name] = today

class ContactForm(StyledModelForm):
    class Meta:
        model = Contact
        exclude = ['received_by']

class LeadForm(StyledModelForm):
    class Meta:
        model = Lead
        exclude = ['received_by']

class LandDealForm(StyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['landowner'].queryset = Contact.objects.filter(contact_type='Landowner')
        self.fields['broker'].queryset = Contact.objects.filter(contact_type='Broker')

    class Meta:
        model = LandDeal
        exclude = ['received_by']

class FollowUpForm(StyledModelForm):
    class Meta:
        model = FollowUp
        exclude = ['received_by']

class ProjectForm(StyledModelForm):
    class Meta:
        model = Project
        exclude = ['received_by']

class TransactionForm(StyledModelForm):
    class Meta:
        model = Transaction
        exclude = ['received_by']
        labels = {
            'transaction_date': 'Transaction Date',
            'date': 'Transaction Date',
            'payment_type': 'Transaction purpose',
            'payment_method': 'Transaction method',
            'project_or_deal': 'Project or Deal',
            'paid_by': 'Paid By / Received By',
            'payment_type_other_reason': 'Transaction purpose other reason'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.fields['payment_type'].required = True
        if 'contact' in self.fields:
            self.fields['contact'].required = False
            self.fields['contact'].empty_label = "---------"
        
        for f in ['transaction_date', 'date']:
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                if not self.initial.get(f) and (not self.instance or not self.instance.pk):
                    self.initial[f] = today
        
        partners = Contact.objects.filter(contact_type='Partner')
        choices = [('', '---------'), ('Company funds', 'Company funds')]
        for p in partners:
            choices.append((p.name, p.name))
        
        self.fields['paid_by'] = forms.ChoiceField(choices=choices, required=True, label="Paid By / Received By")
        self.fields['paid_by'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        tx_date = cleaned_data.get('transaction_date') or cleaned_data.get('date')
        if tx_date:
            cleaned_data['transaction_date'] = tx_date
            cleaned_data['date'] = tx_date
            self.instance.transaction_date = tx_date
            self.instance.date = tx_date
            
        ttype = cleaned_data.get('transaction_type')
        ptype = cleaned_data.get('payment_type')
        paid_by = cleaned_data.get('paid_by')
        
        if not paid_by:
            self.add_error('paid_by', 'This field is required.')
            
        if ptype == 'Other' and not cleaned_data.get('payment_type_other_reason'):
            self.add_error('payment_type_other_reason', 'Please specify the reason for Other.')
            
        return cleaned_data

class ExpenseForm(StyledModelForm):
    class Meta:
        model = Expense
        fields = '__all__'
        labels = {
            'expense_date': 'Expense Date',
            'date': 'Expense Date',
            'category': 'Expense Category',
            'paid_by': 'Paid By (Partner)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        self.fields['payment_method'].required = True
        
        for f in ['expense_date', 'date']:
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                if not self.initial.get(f) and (not self.instance or not self.instance.pk):
                    self.initial[f] = today
        
        if 'category' in self.fields:
            self.fields['category'] = forms.ChoiceField(
                choices=EXPENSE_CATEGORIES,
                widget=forms.Select(attrs={'class': 'form-select'}),
                label='Expense Category',
                initial='OTHER'
            )

        partners = Contact.objects.filter(contact_type='Partner')
        choices = [('', '---------'), ('Company funds', 'Company funds')]
        for p in partners:
            choices.append((p.name, p.name))
        self.fields['paid_by'] = forms.ChoiceField(choices=choices, required=False, label="Paid By (Partner)")
        self.fields['paid_by'].widget.attrs.update({'class': 'form-select'})

    def clean(self):
        cleaned_data = super().clean()
        exp_date = cleaned_data.get('expense_date') or cleaned_data.get('date')
        if exp_date:
            cleaned_data['expense_date'] = exp_date
            cleaned_data['date'] = exp_date
            self.instance.expense_date = exp_date
            self.instance.date = exp_date
        return cleaned_data

class DocumentForm(StyledModelForm):
    class Meta:
        model = Document
        exclude = ['received_by']

class SharedExpenseForm(StyledModelForm):
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        label="Assign to Project (if creating a new Title)",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    new_group_name = forms.CharField(
        required=False,
        label='OR Create New Expense Title',
        help_text='Example: Site Development - Survey No. 125',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Site Development'})
    )
    expense_participants = forms.ModelMultipleChoiceField(
        queryset=Contact.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Split With (Select Existing)'
    )
    new_expense_participants = forms.CharField(
        required=False,
        label='OR Add New People',
        help_text='Type names separated by commas (e.g. Yusuf, Imran).',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'User1, User2'})
    )
    new_payer = forms.CharField(
        required=False,
        label='OR New Payer Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., User3'})
    )
    custom_splits = forms.CharField(
        required=False,
        label='Custom Splits (Optional)',
        help_text='If split method is "Exact", specify like: John:50, Ali:20',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John: 50, User2: 25'})
    )

    class Meta:
        model = SharedExpense
        fields = ['project', 'purpose', 'new_group_name', 'description', 'total_amount', 'paid_by', 'new_payer', 'expense_participants', 'new_expense_participants', 'split_method', 'custom_splits', 'date', 'notes', 'receipt']
        labels = {
            'purpose': 'Expense Title (Select Existing)',
            'description': 'Expense Description (e.g., JCB Work)',
            'paid_by': 'Paid By (Select Existing)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'purpose' in self.fields: self.fields['purpose'].required = False
        if 'paid_by' in self.fields: self.fields['paid_by'].required = False
        
        is_known_purpose = False
        if self.instance and self.instance.pk and self.instance.purpose_id:
            is_known_purpose = True
        elif 'initial' in kwargs and kwargs.get('initial') and kwargs['initial'].get('purpose'):
            is_known_purpose = True
            
        if is_known_purpose:
            for field in ['new_group_name', 'expense_participants', 'new_expense_participants', 'new_payer', 'custom_splits']:
                if field in self.fields: del self.fields[field]
                
            for hidden_field in ['purpose', 'description', 'split_method', 'date']:
                if hidden_field in self.fields:
                    self.fields[hidden_field].widget = forms.HiddenInput()
                    self.fields[hidden_field].label = ''
        else:
            if self.instance.pk and 'expense_participants' in self.fields:
                participant_ids = self.instance.splits.values_list('participant_id', flat=True)
                self.fields['expense_participants'].initial = list(participant_ids)

    def clean(self):
        cleaned_data = super().clean()
        purpose = cleaned_data.get('purpose')
        new_group_name = cleaned_data.get('new_group_name')
        paid_by = cleaned_data.get('paid_by')
        new_payer = cleaned_data.get('new_payer')
        
        is_known = 'new_group_name' not in self.fields
        if not is_known and not purpose and not new_group_name:
            raise forms.ValidationError("You must either select an existing Expense Title or create a new one.")
            
        if not paid_by and not new_payer:
            raise forms.ValidationError("You must either select who paid or type a new payer name.")
            
        return cleaned_data

    def save(self, commit=True):
        new_group_name = self.cleaned_data.get('new_group_name')
        new_payer = self.cleaned_data.get('new_payer')

        if new_payer and not self.cleaned_data.get('paid_by'):
            payer_contact, _ = Contact.objects.get_or_create(name=new_payer.strip(), defaults={'contact_type': 'Other', 'mobile': 'N/A'})
            self.instance.paid_by = payer_contact

        purpose = self.cleaned_data.get('purpose')
        if new_group_name and not purpose:
            proj = self.cleaned_data.get('project')
            purpose = SharedPurpose.objects.create(name=new_group_name, project=proj)
            self.instance.purpose = purpose
            
        instance = super().save(commit)
        
        final_parts = list(self.cleaned_data.get('expense_participants', []))
        new_names_str = self.cleaned_data.get('new_expense_participants', '')
        
        if new_names_str:
            names = [n.strip() for n in new_names_str.split(',') if n.strip()]
            for name in names:
                contact, _ = Contact.objects.get_or_create(name=name, defaults={'contact_type': 'Other', 'mobile': 'N/A'})
                final_parts.append(contact)

        for p in final_parts:
            instance.purpose.participants.add(p)
        if instance.paid_by:
            instance.purpose.participants.add(instance.paid_by)
            
        instance._final_participants = final_parts
        return instance

class SharedPurposeForm(StyledModelForm):
    new_participants = forms.CharField(
        required=False,
        label='Add New People (Quick Add)',
        help_text='Type new names separated by commas (e.g. Ali, John, Sarah) to create and add them instantly.',
        widget=forms.TextInput(attrs={'placeholder': 'User1, User2', 'class': 'form-control'})
    )

    class Meta:
        model = SharedPurpose
        fields = ['project', 'name', 'participants', 'new_participants', 'notes']
        labels = {
            'name': 'Expense Group Name (e.g., Trip, Site A)',
            'participants': 'Select Existing People'
        }
        widgets = {
            'participants': forms.CheckboxSelectMultiple()
        }

    def save(self, commit=True):
        instance = super().save(commit)
        new_names = self.cleaned_data.get('new_participants', '')
        if new_names:
            names = [n.strip() for n in new_names.split(',') if n.strip()]
            for name in names:
                contact, created = Contact.objects.get_or_create(
                    name=name,
                    defaults={'contact_type': 'Other', 'mobile': 'Added via Expense'}
                )
                instance.participants.add(contact)
        return instance

class SettlementForm(StyledModelForm):
    class Meta:
        model = Settlement
        fields = ['from_person', 'to_person', 'amount', 'date', 'entry_date', 'payment_method']
        labels = {
            'entry_date': 'Settlement Date',
            'date': 'Settlement Date'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        for f in ['entry_date', 'date']:
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                if not self.initial.get(f) and (not self.instance or not getattr(self.instance, f, None)):
                    self.initial[f] = today

class SiteForm(StyledModelForm):
    class Meta:
        model = Site
        fields = '__all__'
        labels = {
            'added_date': 'Added Date',
            'booking_date': 'Booking Date',
            'sold_date': 'Sold Date'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        for f in ['added_date', 'booking_date', 'sold_date']:
            if f in self.fields:
                self.fields[f].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
                if f == 'added_date' and not self.initial.get('added_date') and (not self.instance or not self.instance.added_date):
                    self.initial['added_date'] = today

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        today = date.today()
        if status == 'Booked' and not cleaned_data.get('booking_date'):
            cleaned_data['booking_date'] = today
            self.instance.booking_date = today
        elif status == 'Sold' and not cleaned_data.get('sold_date'):
            cleaned_data['sold_date'] = today
            self.instance.sold_date = today
            if not cleaned_data.get('booking_date'):
                cleaned_data['booking_date'] = today
                self.instance.booking_date = today
        return cleaned_data

class SitePaymentForm(StyledModelForm):
    class Meta:
        model = SitePayment
        fields = ['site', 'amount', 'payment_date', 'customer', 'paid_by', 'payment_method', 'notes']
        labels = {
            'payment_date': 'Payment Date',
            'payment_method': 'Payment Method',
            'paid_by': 'Paid By (Name)',
            'amount': 'Payment Amount (₹)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        if 'payment_date' in self.fields:
            self.fields['payment_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
            if not self.initial.get('payment_date') and (not self.instance or not self.instance.payment_date):
                self.initial['payment_date'] = today
        if 'payment_method' in self.fields:
            self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})
        if 'site' in self.fields:
            self.fields['site'].widget.attrs.update({'class': 'form-select'})
        if 'customer' in self.fields:
            self.fields['customer'].widget.attrs.update({'class': 'form-select'})

class PartnerCapitalLedgerForm(StyledModelForm):
    class Meta:
        model = PartnerCapitalLedger
        fields = ['partner', 'project', 'entry_type', 'amount', 'entry_date', 'notes']
        labels = {
            'entry_date': 'Entry Date',
            'entry_type': 'Entry Type',
            'amount': 'Amount (₹)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        if 'entry_date' in self.fields:
            self.fields['entry_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
            if not self.initial.get('entry_date') and (not self.instance or not self.instance.entry_date):
                self.initial['entry_date'] = today
        if 'partner' in self.fields:
            self.fields['partner'].queryset = Contact.objects.filter(contact_type='Partner')
            self.fields['partner'].widget.attrs.update({'class': 'form-select'})
        if 'entry_type' in self.fields:
            self.fields['entry_type'].widget.attrs.update({'class': 'form-select'})
        if 'project' in self.fields:
            self.fields['project'].widget.attrs.update({'class': 'form-select'})
