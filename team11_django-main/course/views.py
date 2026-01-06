from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, Course, Enrollment, Teacher, Comment
from .forms import StudentRegisterForm, StudentProfileForm, CommentForm 

def home(request):
    return render(request, 'home.html')

# 學生註冊
def register(request):
    if request.method == 'POST':
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '註冊成功，請登入！')
            return redirect('login')
    else:
        form = StudentRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

# [修正] 課程列表：區分 管理員(全部) vs 老師(自己) vs 學生(已選/未選)
@login_required
def course_list(request):
    user = request.user
    
    # 1. 管理員 (Staff)：擁有最高權限，看到所有課程
    if user.is_staff:
        courses = Course.objects.all()
        return render(request, 'course_list.html', {'courses': courses, 'role': 'admin'})

    # 2. 老師 (Teacher)：只看到「自己教」的課程
    elif hasattr(user, 'teacher'):
        # 篩選條件：teacher 欄位等於當前使用者的 teacher 物件
        courses = Course.objects.filter(teacher=user.teacher)
        return render(request, 'course_list.html', {'courses': courses, 'role': 'teacher'})
    
    # 3. 學生 (Student)：看到「已選」跟「未選」
    elif hasattr(user, 'student'):
        student = user.student
        
        # A. 找出已修的課程
        my_enrollments = Enrollment.objects.filter(student=student)
        my_course_ids = my_enrollments.values_list('course_id', flat=True)
        
        # B. 找出「未修」的課程 (排除掉上面的 ID)
        available_courses = Course.objects.exclude(id__in=my_course_ids)
        
        # C. 計算學期平均
        total_score = 0
        count = 0
        for e in my_enrollments:
            total_score += e.average()
            count += 1
        semester_avg = round(total_score / count, 2) if count > 0 else 0

        return render(request, 'course_list.html', {
            'enrollments': my_enrollments,      # 已選修
            'available_courses': available_courses, # 未選修
            'semester_avg': semester_avg,
            'role': 'student'
        })
    
    else:
        return render(request, 'home.html')

# 學生加選課程
@login_required
def enroll_course(request, course_id):
    if hasattr(request.user, 'student'):
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student
        Enrollment.objects.get_or_create(student=student, course=course)
        messages.success(request, f'已成功加入課程：{course.name}')
    return redirect('course_list')

# 學生退選課程
@login_required
def drop_course(request, course_id):
    if hasattr(request.user, 'student'):
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student
        Enrollment.objects.filter(student=student, course=course).delete()
        messages.warning(request, f'已退選課程：{course.name}')
    return redirect('course_list')

# 學生個人資料修改
@login_required
def profile(request):
    if not hasattr(request.user, 'student'):
        return redirect('home')
    
    student = request.user.student
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, '個人資料更新成功！')
            return redirect('profile')
    else:
        form = StudentProfileForm(instance=student)
    
    return render(request, 'profile.html', {'form': form, 'student': student})

# 課程詳情：包含留言版
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    
    # 取得該課程的所有留言 (依照時間倒序)
    comments = course.comments.all().order_by('-created_at')
    
    is_teacher = hasattr(request.user, 'teacher')
    
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.course = course
            comment.user = request.user
            comment.save()
            messages.success(request, '留言已送出！')
            return redirect('course_detail', course_id=course.id)
    else:
        comment_form = CommentForm()

    return render(request, 'course_detail.html', {
        'course': course, 
        'enrollments': enrollments,
        'is_teacher': is_teacher,
        'comments': comments,
        'comment_form': comment_form
    })

# 刪除留言
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.user:
        course_id = comment.course.id
        comment.delete()
        messages.success(request, '留言已刪除')
        return redirect('course_detail', course_id=course_id)
    return redirect('home')

# [修正] 新增課程：區分管理員與老師權限
@login_required
def add_course(request):
    # 權限檢查：只有管理員或老師能進來
    if not (request.user.is_staff or hasattr(request.user, 'teacher')):
        return redirect('course_list')

    errors = []
    initial = {}
    teachers = []
    
    # 判斷是否為管理員
    is_admin = request.user.is_staff
    
    # 如果是管理員，才抓出所有老師給他選
    if is_admin:
        teachers = Teacher.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        course_id = request.POST.get('course_id', '').strip()
        
        # 決定誰是老師
        teacher_obj = None
        
        if is_admin:
            # 管理員：從表單選單中抓取
            teacher_id = request.POST.get('teacher', '').strip()
            if teacher_id:
                try:
                    teacher_obj = Teacher.objects.get(id=teacher_id)
                except Teacher.DoesNotExist:
                    pass
        elif hasattr(request.user, 'teacher'):
            # 老師：直接指定「自己」
            teacher_obj = request.user.teacher

        initial = {'name': name, 'course_id': course_id}
        
        if not name or not course_id:
            errors.append('請填寫課程名稱與代碼')
        elif not teacher_obj:
            errors.append('找不到指定的老師資訊')
        else:
            Course.objects.create(name=name, course_id=course_id, teacher=teacher_obj)
            messages.success(request, f'成功新增課程：{name}')
            return redirect('course_list')

    return render(request, 'add_course.html', {
        'errors': errors, 
        'initial': initial, 
        'teachers': teachers, 
        'is_admin': is_admin
    })

# [修正] 打分數：增加權限檢查
@login_required
def grade_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # 安全檢查：必須是管理員 或 該課程的授課老師
    is_admin = request.user.is_staff
    is_owner_teacher = hasattr(request.user, 'teacher') and course.teacher.user == request.user

    if not (is_admin or is_owner_teacher):
        messages.error(request, '您沒有權限管理此課程！')
        return redirect('course_list')

    enrollments = Enrollment.objects.filter(course=course)

    if request.method == 'POST':
        for enrollment in enrollments:
            mid = request.POST.get(f'midterm_{enrollment.id}')
            fin = request.POST.get(f'final_{enrollment.id}')
            if mid: enrollment.midterm_score = float(mid)
            if fin: enrollment.final_score = float(fin)
            enrollment.save()
        messages.success(request, '成績已儲存成功！')
        return redirect('course_detail', course_id=course.id)

    return render(request, 'grade_course.html', {'course': course, 'enrollments': enrollments})