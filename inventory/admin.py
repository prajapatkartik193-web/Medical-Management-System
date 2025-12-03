# inventory/admin.py
from django.contrib import admin
from .models import Supplier, Medicine, Customer, Invoice, InvoiceItem

admin.site.register(Supplier)
admin.site.register(Medicine)
admin.site.register(Customer)
admin.site.register(Invoice)
admin.site.register(InvoiceItem)