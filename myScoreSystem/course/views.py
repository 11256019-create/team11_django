from django.shortcuts import render, get_object_or_404
from .models import Student, Course, Enrollment
from django.shortcuts import redirect

def home(request):
    return render(request, 'home.html')

def course_list(request):
    student = Student.objects.first()
    enrollments = Enrollment.objects.filter(student=student)
    avg_score = sum(e.average() for e in enrollments) / len(enrollments) if enrollments else 0
    return render(request, 'course_list.html', {
        'student': student,
        'enrollments': enrollments,
        'avg_score': round(avg_score, 2)
    })

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    return render(request, 'course_detail.html', {'course': course, 'enrollments': enrollments})

def add_course(request):
    errors = []
    initial = {}
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        course_id = request.POST.get('course_id', '').strip()
        teacher = request.POST.get('teacher', '').strip()
        initial = {'name': name, 'course_id': course_id, 'teacher': teacher}
        # basic validation
        if not name or not course_id or not teacher:
            errors.append('請填寫所有欄位。')
            return render(request, 'add_course.html', {'errors': errors, 'initial': initial})

        Course.objects.create(name=name, course_id=course_id, teacher=teacher)
        return redirect('course_list')

    return render(request, 'add_course.html', {'initial': initial})
