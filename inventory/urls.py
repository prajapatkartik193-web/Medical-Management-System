# inventory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.add_medicine, name='add_medicine'),

    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.add_customer, name='add_customer'),
    
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),

    path('customers/<int:pk>/edit/', views.edit_customer, name='edit_customer'),
    path('customers/<int:pk>/delete/', views.delete_customer, name='delete_customer'),
    
    path('customers/inactive/', views.inactive_customer_list, name='inactive_customer_list'),
    path('customers/<int:pk>/reactivate/', views.reactivate_customer, name='reactivate_customer'),
    
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/add_item/', views.add_invoice_item, name='add_invoice_item'),
    path('invoices/<int:invoice_id>/apply_discount/', views.apply_discount, name='apply_discount'),
    path('medicines/<int:pk>/add_stock/', views.add_stock, name='add_stock'),
    path('invoices/<int:invoice_id>/process_return/', views.process_return, name='process_return'),
    path('returns/<int:return_id>/', views.return_receipt_detail, name='return_receipt_detail'),
    
    path('invoices/<int:invoice_id>/send/', views.send_invoice_email, name='send_invoice_email'),
    path('custom-orders/', views.custom_order_list, name='custom_order_list'),
    path('custom-orders/add/', views.add_custom_order, name='add_custom_order'),
    path('custom-orders/<int:pk>/update/', views.update_custom_order_status, name='update_custom_order_status'),

]