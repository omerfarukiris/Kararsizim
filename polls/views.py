from django.shortcuts import render


def home(request):
    # Geçici: anket listesi Aşama 3'te eklenecek.
    return render(request, "polls/home.html")
