from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .models import Contact


@login_required
@never_cache
def contact_list(request):
    contacts = list(Contact.objects.filter(owner=request.user))
    return render(request, "contacts.html", {
        "contacts": contacts,
        "contact_count": len(contacts),
        "customer_count": sum(contact.tag == Contact.Tag.CUSTOMER for contact in contacts),
        "company_count": len({contact.company for contact in contacts}),
    })
