from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student, Comment

# 註冊表單 (如果您已經有了就不用重複貼)
class StudentRegisterForm(UserCreationForm):
    name = forms.CharField(label='真實姓名', max_length=50, required=True)
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Student.objects.create(user=user, name=self.cleaned_data['name'])
        return user

# [新增] 個人資料修改表單
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'avatar']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

# [新增] 留言表單
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': '寫下你的問題或想法...'})
        }