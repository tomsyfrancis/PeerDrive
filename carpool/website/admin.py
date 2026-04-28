from django.contrib import admin
from website.models import Customer, Booking, ContactUs, Mycar
from website.models import Feedback

# 👤 Customer info
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('fname', 'email', 'mobile','dob','driving_license_no',)
    search_fields = ('fname', 'email')

# 🚗 Ride info (Mycar)
@admin.register(Mycar)
class MycarAdmin(admin.ModelAdmin):
    list_display = (
        'car_num', 'car_type', 'from_place', 'to_place',
        'from_date', 'to_date', 'seat_count','price', 'cust'
    )
    search_fields = (
        'car_num', 'car_type', 'from_place', 'to_place',
        'from_date', 'to_date', 'cust__fname'  # if needed
    )

# 📖 Booking info
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('car', 'name', 'pickup', 'dropoff', 'contact', 'date_added')
    search_fields = ('contact', 'email')
    list_filter = ('pickup', 'dropoff')

# 💬 ContactUs messages
@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone')
    search_fields = ('name', 'email')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'rating', 'booking', 'submitted_at')
    list_filter = ('rating', 'submitted_at')
    search_fields = ('name', 'message', 'user__username')
