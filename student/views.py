from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.conf import settings
from datetime import date, timedelta
from exam import models as QMODEL
from teacher import models as TMODEL
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from django.http import HttpResponse, HttpResponseRedirect
from reportlab.pdfgen import canvas
from django.shortcuts import redirect
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.shortcuts import redirect

from reportlab.platypus import Paragraph
from django.http import HttpResponse
from django.conf import settings

#for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'student/studentclick.html')




def generate_pdf(request, username,address, contact):
    try:
        # Create a PDF object
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="thank_you.pdf"'

        # Create a custom canvas
        c = canvas.Canvas(response, pagesize=letter)

        # Draw background color
        c.setFillColor(colors.HexColor("#D3D3D3"))  # Light sky background color
        c.rect(0, 0, letter[0], letter[1], fill=1)

        # Draw message box
        c.setFillColor(colors.white)  # White message box
        c.setStrokeColor(colors.black)  # Black border
        c.roundRect(100, 400, 400, 200, 10, fill=1)

        # Add text
        c.setFont("Helvetica", 18)
        c.setFillColor(colors.black)
        c.drawString(120, 560, "Your Details, {}!".format(username))

        c.setFont("Helvetica", 14)
        c.drawString(100, 750, "Thank You for Joining Us, {}!".format(username))
        c.drawString(100, 730, "We're excited to have you on board.")
        c.drawString(100, 710, "Stay tuned for updates and exciting content!")
        c.setFont("Helvetica", 12)
        c.drawString(150, 480, "Name: {}".format(username))
        c.drawString(150, 460, "Contact: {}".format(contact))
        c.drawString(150, 440, "Address: {}".format(address))

        # Finish and close the PDF
        c.showPage()
        c.save()

        return response
    except Exception as e:
        # Log the exception
        print("Error generating PDF:", str(e))
        # Handle the error gracefully (e.g., display a generic error page)
        return HttpResponse("An error occurred while generating the PDF.")


def student_signup_view(request):
    if request.method == 'POST':
        userForm = forms.StudentUserForm(request.POST)
        studentForm = forms.StudentForm(request.POST, request.FILES)
        if userForm.is_valid() and studentForm.is_valid():
            user = userForm.save()
            user.set_password(user.password)
            user.save()
            student = studentForm.save(commit=False)
            student.user = user
            student.save()
            # Generate PDF and redirect to login page
           # Assuming you have user and student objects available
            userData = {'username': user.username,'address': student.address,'contact': student.mobile}
            
            return generate_pdf(request, username=user.username, address=student.address, contact=student.mobile)
    else:
        userForm = forms.StudentUserForm()
        studentForm = forms.StudentForm()
    mydict = {'userForm': userForm, 'studentForm': studentForm}
    return render(request, 'student/studentsignup.html', context=mydict)



def is_student(user):
    return user.groups.filter(name='STUDENT').exists()

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    dict={
    
    'total_course':QMODEL.Course.objects.all().count(),
    'total_question':QMODEL.Question.objects.all().count(),
    }
    return render(request,'student/student_dashboard.html',context=dict)

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_exam_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_exam.html',{'courses':courses})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def take_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    total_questions=QMODEL.Question.objects.all().filter(course=course).count()
    questions=QMODEL.Question.objects.all().filter(course=course)
    total_marks=0
    for q in questions:
        total_marks=total_marks + q.marks
    
    return render(request,'student/take_exam.html',{'course':course,'total_questions':total_questions,'total_marks':total_marks})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def start_exam_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    questions=QMODEL.Question.objects.all().filter(course=course)
    if request.method=='POST':
        pass
    response= render(request,'student/start_exam.html',{'course':course,'questions':questions})
    response.set_cookie('course_id',course.id)
    return response


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def calculate_marks_view(request):
    if request.COOKIES.get('course_id') is not None:
        course_id = request.COOKIES.get('course_id')
        course=QMODEL.Course.objects.get(id=course_id)
        
        total_marks=0
        questions=QMODEL.Question.objects.all().filter(course=course)
        for i in range(len(questions)):
            
            selected_ans = request.COOKIES.get(str(i+1))
            actual_answer = questions[i].answer
            if selected_ans == actual_answer:
                total_marks = total_marks + questions[i].marks
        student = models.Student.objects.get(user_id=request.user.id)
        result = QMODEL.Result()
        result.marks=total_marks
        result.exam=course
        result.student=student
        result.save()

        return HttpResponseRedirect('view-result')



@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def view_result_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/view_result.html',{'courses':courses})
    

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def check_marks_view(request,pk):
    course=QMODEL.Course.objects.get(id=pk)
    student = models.Student.objects.get(user_id=request.user.id)
    results= QMODEL.Result.objects.all().filter(exam=course).filter(student=student)
    return render(request,'student/check_marks.html',{'results':results})

@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_marks_view(request):
    courses=QMODEL.Course.objects.all()
    return render(request,'student/student_marks.html',{'courses':courses})
  