from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from booking.models import (
    ProductCatalog,
    Product,
    ProductCriteria,
    TypeformResponse,
    Order
)

import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


class ProductCatalogAdmin(SimpleHistoryAdmin):
    list_display = ('product_title',)
    search_fields = ('product_title', 'base_price',)

    def product_title(self, obj):
        return obj.product.title


class ProductAdmin(SimpleHistoryAdmin):
    list_display = ('title', 'tank_type')
    search_fields = ('title', 'description', 'tank_type', 'home_type')


class OrderAdmin(SimpleHistoryAdmin):
    list_display = ('id', 'order_status', 'appointment_date', 'selected_product',
                    'selected_product_price', 'customer_name', 'customer_address',)
    search_fields = ('appointment_date', 'customer', 'appointment_job')

    def customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}"

    def customer_address(self, obj):
        return f"{obj.customer.address}"

    def appointment_date(self, obj):
        return obj.appointment.date

    def selected_product_price(self, obj):
        return locale.currency(obj.selected_product.product_catalog.final_price())


admin.site.register(ProductCatalog, ProductCatalogAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(TypeformResponse, SimpleHistoryAdmin)
admin.site.register(ProductCriteria, SimpleHistoryAdmin)
admin.site.register(Order, OrderAdmin)
