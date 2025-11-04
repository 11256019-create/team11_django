from django.db import models

class Student(models.Model):
    name = models.CharField(max_length=50, verbose_name='學生姓名')

    def __str__(self):
        return self.name


class Course(models.Model):
    course_id = models.CharField(max_length=10, verbose_name='課程代碼')
    name = models.CharField(max_length=100, verbose_name='課程名稱')
    teacher = models.CharField(max_length=50, verbose_name='授課教師')
    students = models.ManyToManyField(Student, through='Enrollment')

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='學生')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name='課程')
    midterm_score = models.FloatField(verbose_name='期中成績')
    final_score = models.FloatField(verbose_name='期末成績')

    def average(self):
        return round((self.midterm_score + self.final_score) / 2, 2)
