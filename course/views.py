from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Student, Course, Enrollment, Teacher

def home(request):
    return render(request, 'home.html')

@login_required  # 必須登入才能看
def course_list(request):
    # 判斷身分
    if hasattr(request.user, 'teacher'):
        # 是老師：看到所有課程
        courses = Course.objects.all()
        return render(request, 'course_list.html', {'courses': courses, 'role': 'teacher'})
    
    elif hasattr(request.user, 'student'):
        # 是學生：只看到自己修的課 (透過 Enrollment 查)
        student_obj = request.user.student
        enrollments = Enrollment.objects.filter(student=student_obj)
        return render(request, 'course_list.html', {'enrollments': enrollments, 'role': 'student'})
    
    else:
        # 是管理員或其他帳號
        courses = Course.objects.all()
        return render(request, 'course_list.html', {'courses': courses, 'role': 'admin'})

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    
    # 判斷是否為老師 (決定要不要顯示打分數按鈕)
    is_teacher = hasattr(request.user, 'teacher')
    
    return render(request, 'course_detail.html', {
        'course': course, 
        'enrollments': enrollments,
        'is_teacher': is_teacher
    })

@login_required
def add_course(request):
    # 安全檢查：只有老師或管理員可以新增
    if not (request.user.is_staff or hasattr(request.user, 'teacher')):
        return redirect('course_list')

    errors = []
    initial = {}
    teachers = Teacher.objects.all()
    
    if request.method == 'POST':
        # ... (這裡保持你原本的程式碼)
        name = request.POST.get('name', '').strip()
        course_id = request.POST.get('course_id', '').strip()
        teacher_id = request.POST.get('teacher', '').strip()
        initial = {'name': name, 'course_id': course_id, 'teacher_id': teacher_id}
        
        if not name or not course_id or not teacher_id:
            errors.append('請填寫完整')
        else:
            teacher_obj = Teacher.objects.get(id=teacher_id)
            Course.objects.create(name=name, course_id=course_id, teacher=teacher_obj)
            return redirect('course_list')

    return render(request, 'add_course.html', {'errors': errors, 'initial': initial, 'teachers': teachers})

@login_required
def grade_course(request, course_id):
    # 安全檢查：只有老師或管理員可以打分
    if not (request.user.is_staff or hasattr(request.user, 'teacher')):
        return redirect('course_list')

    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)

    if request.method == 'POST':
        for enrollment in enrollments:
            mid = request.POST.get(f'midterm_{enrollment.id}')
            fin = request.POST.get(f'final_{enrollment.id}')
            if mid: enrollment.midterm_score = float(mid)
            if fin: enrollment.final_score = float(fin)
            enrollment.save()
        return redirect('course_detail', course_id=course.id)

    return render(request, 'grade_course.html', {'course': course, 'enrollments': enrollments})