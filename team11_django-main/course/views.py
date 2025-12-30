from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, Course, Enrollment, Teacher, Comment
from .forms import StudentRegisterForm, StudentProfileForm, CommentForm 

def home(request):
    return render(request, 'home.html')

# [新增] 學生註冊
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

# [修改] 課程列表：讓學生能看到「已選」與「未選」課程
@login_required
def course_list(request):
    user = request.user
    
    # 1. 老師或管理員：看到全部
    if hasattr(user, 'teacher') or user.is_staff:
        courses = Course.objects.all()
        return render(request, 'course_list.html', {'courses': courses, 'role': 'teacher'})
    
    # 2. 學生：看到「已選」跟「未選」
    elif hasattr(user, 'student'):
        student = user.student
        
        # A. 找出已修的課程 (Enrollment)
        my_enrollments = Enrollment.objects.filter(student=student)
        
        # [修正這裡] 取出已修課程的 ID 列表
        # 不能用 'course.id'，要用 'course_id' (資料庫欄位) 或 'course__id' (雙底線)
        my_course_ids = my_enrollments.values_list('course_id', flat=True)
        
        # B. 找出「未修」的課程 (排除掉上面的 ID) -> 這是為了讓學生加選用的
        available_courses = Course.objects.exclude(id__in=my_course_ids)
        
        # C. 計算學期平均
        total_score = 0
        count = 0
        for e in my_enrollments:
            total_score += e.average()
            count += 1
        semester_avg = round(total_score / count, 2) if count > 0 else 0

        return render(request, 'course_list.html', {
            'enrollments': my_enrollments,      # 已選修 (用來退選)
            'available_courses': available_courses, # 未選修 (用來加選)
            'semester_avg': semester_avg,
            'role': 'student'
        })
    
    else:
        return render(request, 'home.html')

# [新增] 學生加選課程
@login_required
def enroll_course(request, course_id):
    if hasattr(request.user, 'student'):
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student
        Enrollment.objects.get_or_create(student=student, course=course)
        messages.success(request, f'已成功加入課程：{course.name}')
    return redirect('course_list')

# [新增] 學生退選課程
@login_required
def drop_course(request, course_id):
    if hasattr(request.user, 'student'):
        course = get_object_or_404(Course, id=course_id)
        student = request.user.student
        # 刪除選課紀錄
        Enrollment.objects.filter(student=student, course=course).delete()
        messages.warning(request, f'已退選課程：{course.name}')
    return redirect('course_list')

# [新增] 學生個人資料修改
@login_required
def profile(request):
    # 確保只有學生能用 (或是您也可以開放給老師)
    if not hasattr(request.user, 'student'):
        return redirect('home')
    
    student = request.user.student
    
    if request.method == 'POST':
        # 記得要加 request.FILES 才能處理圖片上傳
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, '個人資料更新成功！')
            return redirect('profile')
    else:
        form = StudentProfileForm(instance=student)
    
    return render(request, 'profile.html', {'form': form, 'student': student})

# [修改] 課程詳情：加入留言版功能
@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    
    # 取得該課程的所有留言 (依照時間倒序)
    comments = course.comments.all().order_by('-created_at')
    
    is_teacher = hasattr(request.user, 'teacher')
    
    # 處理新增留言
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

# [新增] 刪除留言 (僅限本人)
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user == comment.user:
        course_id = comment.course.id
        comment.delete()
        messages.success(request, '留言已刪除')
        return redirect('course_detail', course_id=course_id)
    return redirect('home')

# [保留] 新增課程 (老師/管理員)
@login_required
def add_course(request):
    if not (request.user.is_staff or hasattr(request.user, 'teacher')):
        return redirect('course_list')

    errors = []
    initial = {}
    teachers = Teacher.objects.all()
    
    if request.method == 'POST':
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

# [保留] 打分數 (老師/管理員)
@login_required
def grade_course(request, course_id):
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