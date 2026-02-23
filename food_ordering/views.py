from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FoodItem, TimeSlot, OrderGroup, OrderItem
from django.utils import timezone
from django.db.models import Count

@login_required
def food_dashboard(request):
    if request.user.role in ['STUDENT', 'FACULTY']:
        return redirect('student_menu')
    elif request.user.role == 'ADMIN':
        return redirect('stall_admin_dashboard')
    else:
        messages.error(request, "Ordering is not currently supported in this module.")
        return redirect('dashboard')

@login_required
def student_menu(request):
    if request.user.role not in ['STUDENT', 'FACULTY']:
        return redirect('dashboard')
        
    items = FoodItem.objects.filter(is_available=True)
    time_slots = TimeSlot.objects.all().order_by('start_time')
    my_orders = OrderGroup.objects.filter(student=request.user, created_at__date=timezone.now().date()).order_by('-created_at')
    
    if request.method == 'POST':
        import json
        try:
            data = json.loads(request.body)
            slot_id = data.get('time_slot_id')
            cart_items = data.get('items', [])
            
            if not slot_id or not cart_items:
                messages.error(request, "Invalid order data. Please provide items and a time slot.")
                return redirect('student_menu')
                
            slot = get_object_or_404(TimeSlot, id=slot_id)
            
            # Create a single Order Group (Receipt) for the entire cart
            order_group = OrderGroup.objects.create(
                student=request.user,
                time_slot=slot
            )
            
            # Create items within that receipt
            for cart_item in cart_items:
                item_id = cart_item.get('item_id')
                quantity = int(cart_item.get('quantity', 1))
                item = get_object_or_404(FoodItem, id=item_id)
                
                OrderItem.objects.create(
                    order_group=order_group,
                    item=item,
                    quantity=quantity
                )
            
            messages.success(request, f"Successfully placed order #{order_group.id}. Scheduled for {slot}.")
            # Assuming an AJAX response
            from django.http import JsonResponse
            return JsonResponse({"status": "success", "message": "Order placed successfully!"})
            
        except json.JSONDecodeError:
            messages.error(request, "Failed to process the order format.")
            return redirect('student_menu')

    return render(request, 'food_ordering/student_menu.html', {
        'items': items,
        'time_slots': time_slots,
        'my_orders': my_orders
    })

@login_required
def stall_admin_dashboard(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    today = timezone.now().date()
    # Get all order groups for today
    today_orders = OrderGroup.objects.filter(created_at__date=today).order_by('-created_at')
    
    # Calculate demand per time slot to find peak times
    peak_times = OrderGroup.objects.filter(created_at__date=today)\
        .values('time_slot__start_time', 'time_slot__end_time')\
        .annotate(order_count=Count('id'))\
        .order_by('-order_count')
        
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('status')
        order = get_object_or_404(OrderGroup, id=order_id)
        order.status = new_status
        order.save()
        messages.success(request, f"Order #{order.id} status updated to {new_status}.")
        return redirect('stall_admin_dashboard')

    return render(request, 'food_ordering/admin_dashboard.html', {
        'today_orders': today_orders,
        'peak_times': peak_times,
        'status_choices': OrderGroup.STATUS_CHOICES
    })
