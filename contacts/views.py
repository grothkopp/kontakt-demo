from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from .models import Contact


@login_required
@never_cache
def contact_list(request):
    contacts = list(Contact.objects.filter(owner=request.user))
    selected_tag = request.GET.get("tag", "")
    visible_contacts = contacts
    if selected_tag:
        visible_contacts = [contact for contact in contacts if contact.tag == selected_tag]
    return render(request, "contacts.html", {
        "contacts": visible_contacts,
        "selected_tag": selected_tag,
        "tags": Contact.Tag.choices,
        "contact_count": len(contacts),
        "customer_count": sum(contact.tag == Contact.Tag.CUSTOMER for contact in contacts),
        "company_count": len({contact.company for contact in contacts}),
    })
