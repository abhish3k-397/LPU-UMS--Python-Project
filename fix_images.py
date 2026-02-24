import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from food_ordering.models import FoodItem

food_images = {
    "Samosa": "food_items/samosa.png",
    "Veg Burger": "food_items/veg_burger.png",
    "Cold Coffee": "food_items/cold_coffee.png",
    "Masala Dosa": "food_items/masala_dosa.png",
    "Paneer Wrap": "food_items/paneer_wrap.png",
    "Iced Tea": "food_items/iced_tea.png",
}

for name, img_path in food_images.items():
    items = FoodItem.objects.filter(name=name)
    if items.exists():
        for item in items:
            item.image = img_path
            item.save()
            print(f"Updated {name} with image {img_path}")
    else:
        print(f"Could not find FoodItem: {name}")

print("Fix complete!")
