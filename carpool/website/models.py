from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Customer(models.Model):
    usern = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    fname = models.CharField(max_length=80, blank=True)
    email = models.EmailField(max_length=80, unique=True)
    driving_license_no = models.CharField(max_length=20, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20)
    mobile = models.CharField(max_length=11)

    def __str__(self):
        return self.fname


class Mycar(models.Model):
    cust = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    car_num = models.CharField(max_length=10, unique=True)
    car_type = models.CharField(max_length=30)
    from_place = models.CharField(max_length=30)
    to_place = models.CharField(max_length=30)
    from_date = models.DateTimeField(null=True)
    to_date = models.DateTimeField(null=True)
    seat_count = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    price = models.FloatField()

    def __str__(self):
        return self.car_num


class ContactUs(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField(max_length=80, unique=True)
    phone = models.CharField(max_length=11, blank=True)
    msg = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Booking(models.Model):
    name = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    car = models.ForeignKey(Mycar, on_delete=models.SET_NULL, null=True)
    contact = models.CharField(max_length=11)
    email = models.EmailField(max_length=80)
    pickup = models.DateField(null=True)
    dropoff = models.DateField(null=True)
    pick_add = models.CharField(max_length=100)
    drop_add = models.CharField(max_length=100)
    date_added = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)


class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    rating = models.IntegerField()
    message = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating} stars"
