"""
URL configuration for scoreSystem project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from course import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'), #註冊
    path('profile/', views.profile, name='profile'),    #個人資料
    
    path('', views.home, name='home'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/add/', views.add_course, name='add_course'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/grade/', views.grade_course, name='grade_course'),
    
    # 加退選與留言
    path('courses/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/<int:course_id>/drop/', views.drop_course, name='drop_course'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]

# 讓開發環境可以讀取上傳的圖片
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)