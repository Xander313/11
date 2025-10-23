from django.shortcuts import render

# Create your views here.
def agregarLogin(request):
    print('Vista agregarLogin llamada')
    return render(request, 'login/login.html')