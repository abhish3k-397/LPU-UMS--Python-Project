from django.db import models

class CampusBlock(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Classroom(models.Model):
    ROOM_TYPES = [
        ('CLASSROOM', 'Classroom'),
        ('LAB', 'Laboratory'),
        ('SEMINAR_HALL', 'Seminar Hall'),
        ('OFFICE', 'Faculty Office'),
    ]
    
    block = models.ForeignKey(CampusBlock, on_delete=models.CASCADE, related_name='classrooms')
    room_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='CLASSROOM')
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ('block', 'room_number')

    def __str__(self):
        return f"{self.block.name} - {self.room_number} ({self.get_room_type_display()})"

class CampusResource(models.Model):
    RESOURCE_STATUS = [
        ('WORKING', 'Operational'),
        ('MAINTENANCE', 'In Maintenance'),
        ('BROKEN', 'Out of Order'),
    ]
    
    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=50) # e.g. Projector, PC, Microscope
    status = models.CharField(max_length=20, choices=RESOURCE_STATUS, default='WORKING')
    purchase_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

class ResourceAllocation(models.Model):
    resource = models.ForeignKey(CampusResource, on_delete=models.CASCADE, related_name='allocations')
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='resources')
    allocated_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resource.name} in {self.classroom}"
