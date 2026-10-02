from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect ,render
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from stores.models import Store
from accounts.decorators import vendor_required
from django import forms
from services.models import Service



class VendorServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        exclude = ['store']


@login_required
@vendor_required
def vendor_add_service(request):

    try:
        store = Store.objects.get(vendor=request.user)
    except Store.DoesNotExist:
        return HttpResponseForbidden("You must create a store first.")

    if request.method == "POST":
        form = VendorServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.store = store
            service.save()
            return redirect("vendor:dashboard")
    else:
        form = VendorServiceForm()

    return render(request, "vendor_panel/vendor_service_form.html", {
        "form": form
    })