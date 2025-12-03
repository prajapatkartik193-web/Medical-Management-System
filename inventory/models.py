# inventory/models.py
from django.db import models
from django.utils import timezone

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()

    def __str__(self):
        return self.name

class Medicine(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    in_stock_total = models.PositiveIntegerField(default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# inventory/models.py

class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    # ADD THIS LINE
    email = models.EmailField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    invoice_date = models.DateTimeField(default=timezone.now)
    
    # RENAMED: This is now the pre-discount, pre-tax total
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # NEW FIELDS
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    taxable_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    cgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=9.0) # Assuming 9%
    cgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    sgst_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=9.0) # Assuming 9%
    sgst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Invoice {self.id} for {self.customer.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of sale

    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
# inventory/models.py

# ADD THESE TWO NEW MODELS
class ReturnInvoice(models.Model):
    original_invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    return_date = models.DateTimeField(default=timezone.now)
    total_refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"Return for Invoice #{self.original_invoice.id}"

class ReturnItem(models.Model):
    return_invoice = models.ForeignKey(ReturnInvoice, related_name='items', on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2) # Price at the time of return

    def __str__(self):
        return f"{self.quantity} x {self.medicine.name}"
    
class CustomOrder(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ordered', 'Ordered from Supplier'),
        ('Arrived', 'Arrived at Store'),
        ('Delivered', 'Delivered to Customer'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    medicine_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    order_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order for {self.quantity}x {self.medicine_name} for {self.customer.name}"
