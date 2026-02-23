from django.db import models

class CampusBlock(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Classroom(models.Model):
    block = models.ForeignKey(CampusBlock, on_delete=models.CASCADE, related_name='classrooms')
    room_number = models.CharField(max_length=20)
    capacity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('block', 'room_number')

    def __str__(self):
        return f"{self.block.name} - {self.room_number} (Cap: {self.capacity})"
