# inventory/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Medicine, Supplier, Customer, Invoice, InvoiceItem , ReturnInvoice, ReturnItem , CustomOrder
from django.db.models import F, Sum
from .forms import CustomerForm
from decimal import Decimal
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
import os

# --- Dashboard ---
def dashboard(request):
    total_medicines = Medicine.objects.count()
    total_customers = Customer.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.count()
    context = {
        'total_medicines': total_medicines,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
    }
    return render(request, 'inventory/dashboard.html', context)

# --- Medicine Management ---
def medicine_list(request):
    medicines = Medicine.objects.all()
    return render(request, 'inventory/medicine_list.html', {'medicines': medicines})

def add_medicine(request):
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        supplier_id = request.POST['supplier']
        in_stock_total = request.POST['in_stock_total']
        mrp = request.POST['mrp']
        
        supplier = get_object_or_404(Supplier, id=supplier_id)
        
        Medicine.objects.create(
            name=name,
            description=description,
            supplier=supplier,
            in_stock_total=in_stock_total,
            mrp=mrp
        )
        return redirect('medicine_list')
    
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/add_medicine.html', {'suppliers': suppliers})

# --- Customer Management ---
def customer_list(request):
    customers = Customer.objects.filter(is_active=True)
    return render(request, 'inventory/customer_list.html', {'customers': customers})

def add_customer(request):
    if request.method == 'POST':
        # Bind the POST data to a form instance
        form = CustomerForm(request.POST)
        if form.is_valid(): # This checks for uniqueness and other errors
            form.save()
            return redirect('customer_list')
    else:
        # If a GET request, create a blank form
        form = CustomerForm()
        
    return render(request, 'inventory/add_customer.html', {'form': form})
    
# --- Supplier Management ---
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

def add_supplier(request):
    if request.method == 'POST':
        name = request.POST['name']
        contact_person = request.POST['contact_person']
        phone_number = request.POST['phone_number']
        address = request.POST['address']
        Supplier.objects.create(name=name, contact_person=contact_person, phone_number=phone_number, address=address)
        return redirect('supplier_list')
    return render(request, 'inventory/add_supplier.html')

# --- Invoice Management ---
def invoice_list(request):
    query = request.GET.get('q')
    if query:
        # Search by invoice ID
        invoices = Invoice.objects.filter(id=query)
    else:
        invoices = Invoice.objects.all().order_by('-invoice_date')
    return render(request, 'inventory/invoice_list.html', {'invoices': invoices, 'query': query})

def create_invoice(request):
    if request.method == 'POST':
        customer_id = request.POST['customer']
        customer = get_object_or_404(Customer, id=customer_id)
        invoice = Invoice.objects.create(customer=customer)
        return redirect('invoice_detail', invoice_id=invoice.id)
    
    customers = Customer.objects.filter(is_active=True)
    return render(request, 'inventory/create_invoice.html', {'customers': customers})

def recalculate_invoice(invoice):
    """
    Recalculates all financial fields for a given invoice.
    """
    # Calculate Sub Total
    sub_total = invoice.items.aggregate(
        total=Sum(F('quantity') * F('rate'))
    )['total'] or Decimal('0.00')
    invoice.sub_total = sub_total

    # Calculate Discount
    discount_percent = invoice.discount_percentage
    discount_amount = (sub_total * discount_percent) / 100
    invoice.discount_amount = discount_amount

    # Calculate Taxable Total
    taxable_total = sub_total - discount_amount
    invoice.taxable_total = taxable_total

    # Calculate CGST and SGST (assuming fixed rates from model)
    cgst_percent = invoice.cgst_percentage
    sgst_percent = invoice.sgst_percentage
    
    cgst_amount = (taxable_total * cgst_percent) / 100
    sgst_amount = (taxable_total * sgst_percent) / 100
    invoice.cgst_amount = cgst_amount
    invoice.sgst_amount = sgst_amount

    # Calculate Grand Total
    grand_total = taxable_total + cgst_amount + sgst_amount
    invoice.grand_total = grand_total
    
    invoice.save()

def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    medicines = Medicine.objects.filter(in_stock_total__gt=0)
    
    # Always recalculate on page load to ensure data is fresh
    recalculate_invoice(invoice)
    
    context = {
        'invoice': invoice,
        'medicines': medicines,
    }
    return render(request, 'inventory/invoice_detail.html', context)

def add_invoice_item(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        medicine_id = request.POST['medicine']
        quantity = int(request.POST['quantity'])
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        if medicine.in_stock_total >= quantity:
            InvoiceItem.objects.create(
                invoice=invoice,
                medicine=medicine,
                quantity=quantity,
                rate=medicine.mrp
            )
            medicine.in_stock_total -= quantity
            medicine.save()
            # Recalculate everything after adding a new item
            recalculate_invoice(invoice)
    return redirect('invoice_detail', invoice_id=invoice.id)

def apply_discount(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    if request.method == 'POST':
        discount = Decimal(request.POST.get('discount', '0'))
        invoice.discount_percentage = discount
        recalculate_invoice(invoice)
    return redirect('invoice_detail', invoice_id=invoice.id)

def medicine_list(request):
    query = request.GET.get('q') # Get the search query from the URL
    if query:
        # Filter medicines where the name contains the search query (case-insensitive)
        medicines = Medicine.objects.filter(name__icontains=query)
    else:
        # If no query, get all medicines
        medicines = Medicine.objects.all()
        
    return render(request, 'inventory/medicine_list.html', {'medicines': medicines, 'query': query})

def add_stock(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        # Get the quantity to add from the form
        additional_stock = int(request.POST.get('additional_stock', 0))
        
        if additional_stock > 0:
            # Add to the existing stock and save
            medicine.in_stock_total += additional_stock
            medicine.save()
            
    return redirect('medicine_list')

def edit_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        # Pass the instance to update the existing customer
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        # Pre-populate the form with the customer's current data
        form = CustomerForm(instance=customer)
        
    return render(request, 'inventory/edit_customer.html', {'form': form})

# ADD THIS FUNCTION
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    # Set the customer to inactive instead of deleting
    customer.is_active = False
    customer.save()
    return redirect('customer_list')

def inactive_customer_list(request):
    customers = Customer.objects.filter(is_active=False)
    return render(request, 'inventory/inactive_customer_list.html', {'customers': customers})

# ADD THIS VIEW TO HANDLE THE REACTIVATION LOGIC
def reactivate_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.is_active = True
    customer.save()
    return redirect('customer_list')

def process_return(request, invoice_id):
    original_invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        # Create a new ReturnInvoice
        return_invoice = ReturnInvoice.objects.create(original_invoice=original_invoice)
        total_refund = Decimal('0.00')

        # Loop through all items in the original invoice
        for item in original_invoice.items.all():
            return_qty_str = request.POST.get(f'return_qty_{item.id}', '0')
            return_qty = int(return_qty_str)

            if return_qty > 0:
                # Add item back to stock
                medicine = item.medicine
                medicine.in_stock_total += return_qty
                medicine.save()

                # Create a ReturnItem record
                ReturnItem.objects.create(
                    return_invoice=return_invoice,
                    medicine=medicine,
                    quantity=return_qty,
                    rate=item.rate # Use the original sale price for the refund
                )
                total_refund += (item.rate * return_qty)
        
        return_invoice.total_refund_amount = total_refund
        return_invoice.save()

        # Redirect to the new return receipt
        return redirect('return_receipt_detail', return_id=return_invoice.id)
    
    # This should not be reached via GET
    return redirect('invoice_detail', invoice_id=invoice_id)


# ADD THIS NEW VIEW for showing the return receipt
def return_receipt_detail(request, return_id):
    return_invoice = get_object_or_404(ReturnInvoice, id=return_id)
    context = {
        'return_invoice': return_invoice
    }
    return render(request, 'inventory/return_receipt_detail.html', context)

# --- Custom Order Management ---

def custom_order_list(request):
    orders = CustomOrder.objects.all().order_by('-order_date')
    return render(request, 'inventory/custom_order_list.html', {'orders': orders})

def add_custom_order(request):
    if request.method == 'POST':
        customer_id = request.POST['customer']
        supplier_id = request.POST['supplier']
        medicine_name = request.POST['medicine_name']
        quantity = request.POST['quantity']
        notes = request.POST.get('notes', '')

        customer = get_object_or_404(Customer, id=customer_id)
        supplier = get_object_or_404(Supplier, id=supplier_id)

        CustomOrder.objects.create(
            customer=customer,
            supplier=supplier,
            medicine_name=medicine_name,
            quantity=quantity,
            notes=notes
        )
        return redirect('custom_order_list')
    
    customers = Customer.objects.filter(is_active=True)
    suppliers = Supplier.objects.all() # Assuming suppliers can't be inactive
    context = {
        'customers': customers,
        'suppliers': suppliers,
    }
    return render(request, 'inventory/add_custom_order.html', context)

def update_custom_order_status(request, pk):
    order = get_object_or_404(CustomOrder, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            order.status = new_status
            order.save()
    return redirect('custom_order_list')

def send_invoice_email(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    if invoice.customer.email:
        subject = f"Your Invoice #{invoice.id} from Medical Store"

        # Render the HTML template to a string
        html_message = render_to_string('inventory/invoice_email.html', {'invoice': invoice})

        # Create the email message
        email = EmailMessage(
            subject,
            html_message,
            os.environ.get('EMAIL_HOST_USER'),  # Your "from" email
            [invoice.customer.email],          # The customer's "to" email
        )
        email.content_subtype = "html"  # This is crucial for sending HTML emails

        try:
            email.send()
            messages.success(request, 'Invoice successfully sent to the customer.')
        except Exception as e:
            messages.error(request, f'Failed to send email. Error: {e}')
    else:
        messages.warning(request, 'This customer does not have an email address.')

    return redirect('invoice_detail', invoice_id=invoice.id)