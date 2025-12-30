from django.contrib import admin
from .models import Student, Course, Enrollment, Teacher  # 記得匯入 Teacher

admin.site.register(Student)
admin.site.register(Course)
admin.site.register(Enrollment)
admin.site.register(Teacher) 