from django.urls import path
from booking import views

urlpatterns = [
    path('webflow/', views.webflow_to_typeform_redirect),
    path('typeform/', views.typeform_webhook),
    path('calendly/', views.fetch_calendly_data),
    path('calendly/reschedule/', views.handle_reschedule_calendly_data),
    path('calendly_invitee/<slug:invitee_uuid>', views.get_customer_from_calendly_invitee),
    path('product/selected/<slug:url_token>', views.selected_product_list, name="selected_product_list"),
    path('select_product/', views.select_product, name="select_product"),
    path('update_product_criteria/', views.update_product_criteria, name="update_product_criteria"),
    path('customer_order/', views.submit_customer_order, name="customer_order"),
]
