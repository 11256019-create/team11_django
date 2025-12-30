from django.db import models
from django.contrib.auth.models import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='關聯帳號')
    name = models.CharField(max_length=50, verbose_name='教師姓名')
    def __str__(self): return self.name

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name='關聯帳號')
    name = models.CharField(max_length=50, verbose_name='學生姓名')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='個人頭像')

    def __str__(self):
        return self.name

class Course(models.Model):
    course_id = models.CharField(max_length=10, verbose_name='課程代碼')
    name = models.CharField(max_length=100, verbose_name='課程名稱')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, verbose_name='授課教師')
    students = models.ManyToManyField(Student, through='Enrollment')
    def __str__(self): return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='學生')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='課程')
    midterm_score = models.FloatField(default=0, verbose_name='期中成績')
    final_score = models.FloatField(default=0, verbose_name='期末成績')

    def average(self):
        return round((self.midterm_score + self.final_score) / 2, 2)

class Comment(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='comments', verbose_name='課程')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='留言者')
    content = models.TextField(verbose_name='留言內容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='留言時間')

    def __str__(self):
        return f"{self.user.username} - {self.course.name}"