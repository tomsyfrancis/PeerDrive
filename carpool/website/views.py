from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from collections import defaultdict

from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from shapely.geometry import LineString, Point
import openrouteservice

from website.models import Customer, Mycar, ContactUs, Booking, Feedback


# --- Geo/routing helpers ---

_geolocator = Nominatim(user_agent="carpool_app", timeout=10)
_ors_client = openrouteservice.Client(key=__import__('os').environ.get('ORS_API_KEY', ''))


def get_coordinates(place_name):
    """Return (lat, lon) tuple for a place name, or None if not found."""
    location = _geolocator.geocode(place_name)
    return (location.latitude, location.longitude) if location else None


def get_distance_and_duration(from_place, to_place):
    """Return (distance_km, duration_min, geometry) via OpenRouteService."""
    try:
        loc1 = _geolocator.geocode(from_place)
        loc2 = _geolocator.geocode(to_place)
        if not loc1 or not loc2:
            return None, None, None
        coords = ((loc1.longitude, loc1.latitude), (loc2.longitude, loc2.latitude))
        route = _ors_client.directions(coords, profile='driving-car', format='geojson')
        segment = route['features'][0]['properties']['segments'][0]
        distance_km = round(segment['distance'] / 1000, 2)
        duration_min = round(segment['duration'] / 60, 2)
        geometry = route['features'][0]['geometry']
        return distance_km, duration_min, geometry
    except Exception as e:
        print(f"Routing error: {e}")
        return None, None, None


# --- Views ---

def home(request):
    return render(request, "home.html")


def LoginUser(request):
    if request.method == "GET":
        return render(request, "login.html")

    usern = request.POST['usern']
    password = request.POST['password']
    user = authenticate(username=usern, password=password)
    if user is not None:
        login(request, user)
        return redirect('home')
    messages.error(request, "Invalid username or password!")
    return redirect('login')


def Register(request):
    if request.method == 'GET':
        return render(request, "registration.html")

    usern = request.POST['usern']
    fname = request.POST['fname']
    email = request.POST['email']
    password = request.POST['password']
    mobile = request.POST['mobile']
    gender = request.POST['gender']

    if len(mobile) != 10 or not mobile.isdigit():
        messages.warning(request, "Phone number must be 10 digits.")
    elif mobile[0] in '012345':
        messages.warning(request, "Phone number is not valid.")
    else:
        try:
            obj = User.objects.create_user(usern, email, password)
            Customer.objects.create(usern=obj, fname=fname, email=email, mobile=mobile, gender=gender)
            return redirect('login')
        except IntegrityError:
            messages.warning(request, "Account already exists!")
            return redirect('register')

    return render(request, "registration.html")


def Contactus(request):
    if request.method == "GET":
        return render(request, "contact.html")

    name = request.POST['name']
    email = request.POST['email']
    phone = request.POST['phone']
    msg = request.POST['msg']

    if len(phone) != 10 or not phone.isdigit():
        messages.warning(request, "Phone number must be 10 digits.")
    elif phone[0] in '012345':
        messages.warning(request, "Phone number is not valid.")
    else:
        ContactUs.objects.create(name=name, email=email, phone=phone, msg=msg)
        messages.success(request, "Thank you for contacting us, we will reach you soon.")

    return render(request, "contact.html")


def Search(request):
    if request.method == "GET":
        return render(request, "search.html")

    from_place = request.POST['from_place']
    to_place = request.POST['to_place']
    travel_date = request.POST.get('travel_date')

    try:
        user_from_loc = _geolocator.geocode(from_place)
        user_to_loc = _geolocator.geocode(to_place)
    except Exception:
        user_from_loc = user_to_loc = None

    if not user_from_loc or not user_to_loc:
        messages.error(request, "Could not locate the entered places.")
        return render(request, "search.html")

    user_from_coords = (user_from_loc.latitude, user_from_loc.longitude)
    user_to_coords = (user_to_loc.latitude, user_to_loc.longitude)

    cars = Mycar.objects.all()

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'early':
        cars = cars.order_by('from_date')
    elif sort == 'low_price':
        cars = cars.order_by('price')
    elif sort == 'shortest':
        cars = cars.order_by('to_date')

    # Time filtering
    time_filter = request.GET.getlist('time')
    if time_filter:
        filtered = []
        for car in cars:
            if not car.from_date:
                continue
            hour = car.from_date.hour
            if "early" in time_filter and hour < 6:
                filtered.append(car)
            elif "morning" in time_filter and 6 <= hour <= 12:
                filtered.append(car)
            elif "afternoon" in time_filter and 12 < hour <= 18:
                filtered.append(car)
            elif "evening" in time_filter and hour > 18:
                filtered.append(car)
        cars = filtered

    matched_cars = []
    for car in cars:
        try:
            car_from_loc = _geolocator.geocode(car.from_place)
            car_to_loc = _geolocator.geocode(car.to_place)
            if not car_from_loc or not car_to_loc:
                continue

            car_from_coords = (car_from_loc.latitude, car_from_loc.longitude)
            car_to_coords = (car_to_loc.latitude, car_to_loc.longitude)

            distance_km, duration_min, geometry = get_distance_and_duration(car.from_place, car.to_place)
            car.distance_km = round(distance_km, 1) if distance_km else None
            car.duration_min = int(duration_min) if duration_min else None
            car.route_geometry = geometry
            car.estimated_arrival = (
                car.from_date + timedelta(minutes=duration_min)
                if car.from_date and duration_min else None
            )

            if (geodesic(car_from_coords, user_from_coords).km <= 10 and
                    geodesic(car_to_coords, user_to_coords).km <= 10):
                matched_cars.append(car)

        except Exception as e:
            print(f"Error processing car {car.car_num}: {e}")
            continue

    # Date filter
    if travel_date:
        try:
            travel_date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
            matched_cars = [
                car for car in matched_cars
                if car.from_date and car.to_date
                and car.from_date.date() <= travel_date_obj <= car.to_date.date()
            ]
        except Exception as e:
            print("Invalid travel date:", e)

    return render(request, "searched_cars.html", {'cars': matched_cars})


@login_required(login_url='login')
def Cardetails(request, car_id):
    car = Mycar.objects.get(pk=car_id)

    if request.method == "GET":
        distance_km, duration_min, _ = get_distance_and_duration(car.from_place, car.to_place)
        duration_min = duration_min or 90
        car.duration_min = int(duration_min)
        car.distance_km = round(distance_km, 1) if distance_km else None
        car.estimated_arrival = (
            car.from_date + timedelta(minutes=duration_min) if car.from_date else None
        )
        return render(request, "cardetails.html", {'car': car})

    # POST — handle booking
    contact = request.POST['contact']
    email = request.POST['email']
    pickup = request.POST['pickup']
    dropoff = request.POST['dropoff']
    pick_add = request.POST['pick_add']
    drop_add = request.POST['drop_add']

    if len(contact) != 10 or not contact.isdigit():
        messages.warning(request, "Phone number must be 10 digits.")
        return redirect('cardetails', car_id=car_id)
    if contact[0] in '012345':
        messages.warning(request, "Phone number is not valid.")
        return redirect('cardetails', car_id=car_id)

    cust = Customer.objects.get(usern=request.user)
    if Booking.objects.filter(car=car, pickup=pickup, dropoff=dropoff).exists():
        messages.error(request, "The car is not available for the selected dates.")
        return redirect('cardetails', car_id=car_id)

    Booking.objects.create(
        name=cust, car=car, email=email, contact=contact,
        pickup=pickup, dropoff=dropoff, pick_add=pick_add, drop_add=drop_add
    )
    return redirect('bookedcar', car_id=car_id)


@login_required
def Booked(request, car_id):
    if request.method == "GET":
        cust = Customer.objects.get(usern=request.user)
        book = Booking.objects.filter(car=car_id, name=cust)
        messages.success(request, "Your booking has been done successfully!")
        return render(request, "booked.html", {'book': book})
    return redirect('payments')


def dash(request):
    if request.user.is_authenticated:
        return render(request, "dashboard.html")
    return redirect('login')


def MyBookings(request):
    if request.user.is_authenticated:
        cust = Customer.objects.filter(usern=request.user)
        custs = Booking.objects.filter(name=cust)
        return render(request, "mybooking.html", {'custs': custs})
    return redirect('login')


def MyAccount(request):
    if request.user.is_authenticated:
        cust = Customer.objects.get(usern=request.user)
        return render(request, "myaccount.html", {'cust': cust})
    return redirect('login')


def CustomerBookings(request):
    if request.user.is_authenticated:
        cust = Customer.objects.get(usern=request.user)
        mybook = Booking.objects.filter(name=cust)
        mycar = Mycar.objects.filter(cust=cust)
        bookings = Booking.objects.filter(car__in=mycar).exclude(name=cust)
        return render(request, "cust_booking.html", {'mybook': mybook, 'bookings': bookings})
    return redirect('login')


def MyCarList(request):
    if request.user.is_authenticated:
        username = Customer.objects.get(usern=request.user)
        custs = Mycar.objects.filter(cust=username)
        return render(request, "mycar_list.html", {'custs': custs})
    return redirect('login')


def Cars(request):
    mycars = Mycar.objects.all()
    return render(request, "allcars.html", {'mycars': mycars})


def Change(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'GET':
        return render(request, "change.html")

    user = request.user
    old_password = request.POST['old_password']
    new_password = request.POST['new_password']
    confirm_password = request.POST['confirm_password']

    if authenticate(request, username=user.username, password=old_password) is None:
        messages.error(request, 'The old password is incorrect!')
        return redirect('changepassword')

    if new_password != confirm_password:
        messages.error(request, 'New password and confirm password do not match!')
        return redirect('changepassword')

    user.password = make_password(new_password)
    user.save()
    login(request, user)
    messages.success(request, 'Password changed successfully!')
    return redirect('changepassword')


@login_required
def check_ride_info(request):
    try:
        customer = Customer.objects.get(usern=request.user)
        if not customer.driving_license_no or not customer.dob:
            return redirect('ridedetails')
        return redirect('addmycar')
    except Customer.DoesNotExist:
        return redirect('ridedetails')


def ridedetails(request):
    if request.method == 'POST':
        customer = Customer.objects.get(usern=request.user)
        customer.driving_license_no = request.POST.get('driving_license_no')
        customer.dob = request.POST.get('dob')
        customer.save()
        return redirect('addmycar')
    return render(request, 'ridedetails.html')


def Addcar(request):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'GET':
        return render(request, "addmycar.html")

    car_num = request.POST['car_num']
    from_place = request.POST['from_place']
    to_place = request.POST['to_place']
    car_type = request.POST['car_type']
    price = request.POST['price']
    from_date = request.POST['from_date']
    to_date = request.POST['to_date']
    seat_count = request.POST['seat_count']
    custom = Customer.objects.get(usern=request.user)

    if Mycar.objects.filter(car_num=car_num).exists():
        messages.warning(request, 'Car already exists.')
        return redirect('addmycar')

    Mycar.objects.create(
        car_num=car_num, from_date=from_date, to_date=to_date,
        from_place=from_place, to_place=to_place, car_type=car_type,
        price=price, seat_count=seat_count, cust=custom
    )
    return redirect('home')


def logout_user(request):
    logout(request)
    return redirect('home')


@login_required
def payments(request):
    try:
        booking = Booking.objects.filter(name__usern=request.user).latest('date_added')
    except Booking.DoesNotExist:
        booking = None
    return render(request, 'payments.html', {'booking': booking})


def chats(request):
    return render(request, 'chats.html')


def notifications(request):
    return render(request, 'notifications.html')


def ride_requests(request):
    return render(request, 'ride_requests.html')


def ride_report(request):
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    bookings = Booking.objects.none()

    if from_date and to_date:
        try:
            from_dt = datetime.combine(parse_date(from_date), datetime.min.time())
            to_dt = datetime.combine(parse_date(to_date), datetime.max.time())
            bookings = Booking.objects.filter(
                date_added__range=(from_dt, to_dt),
                name__usern=request.user
            ).order_by('-date_added')
        except Exception as e:
            print("Date filter error:", e)

    return render(request, 'ride_report.html', {
        'bookings': bookings,
        'from_date': from_date,
        'to_date': to_date,
    })


@login_required
def submit_feedback(request):
    if request.method == "POST":
        booking_id = request.POST.get('booking_id') or None
        Feedback.objects.create(
            user=request.user,
            name=request.POST.get('name'),
            rating=request.POST.get('rating'),
            message=request.POST.get('message'),
            booking_id=booking_id,
        )
        return render(request, 'home.html', {'success': True})
    return render(request, 'feedback.html')


@login_required
def total_earnings(request):
    try:
        customer = Customer.objects.get(usern=request.user)
    except Customer.DoesNotExist:
        return render(request, 'error.html', {'msg': 'Customer not found'})

    cars_owned = Mycar.objects.filter(cust=customer)
    bookings = Booking.objects.filter(car__in=cars_owned)
    total = sum(b.car.price for b in bookings)
    return render(request, 'total_earnings.html', {'total_earnings': total, 'bookings': bookings})
