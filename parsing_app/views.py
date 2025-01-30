from django.shortcuts import render
from loguru import logger


# Create your views here.
def main(request):
    return render(request, "index.html")


from django.shortcuts import render, redirect
from .forms import RequestUserForm


def request_user_vies(request):
    if request.method == "POST":
        form = RequestUserForm(request.POST)
        if form.is_valid():
            # form.save()
            logger.info(form.data)
            return redirect("main")
    else:
        logger.info("Не тот метод")
        form = RequestUserForm()
    return render(request, "request_user_form.html", {"form": form})


def search_view(request):
    if request.method == "POST":
        response_id = request.POST.get("response_id")
        start_data = request.POST.get("start_data")
        stop_data = request.POST.get("stop_data")

        print(response_id, start_data, stop_data)
        return redirect("main")
    return render(request, "results_pars.html")
