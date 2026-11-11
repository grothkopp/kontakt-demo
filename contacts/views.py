from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from .models import Contact
from .suggestions import suggest_tag
from .providers import configured_provider
from .observability import suggest_observed
from django.conf import settings


def contact_context(user):
    contacts = list(Contact.objects.filter(owner=user))
    return {
        "contacts": contacts,
        "provider_label": "Offline fake" if settings.AI_PROVIDER == "fake" else "Live AI",
        "contact_count": len(contacts),
        "customer_count": sum(contact.tag == Contact.Tag.CUSTOMER for contact in contacts),
        "company_count": len({contact.company for contact in contacts}),
    }


@never_cache
@login_required
def contact_list(request):
    return render(request, "contacts.html", contact_context(request.user))


@never_cache
@login_required
@require_POST
def suggest_contact_tag(request, pk):
    contact = get_object_or_404(Contact, pk=pk, owner=request.user)
    result = suggest_observed(contact.note, provider=configured_provider())
    context = contact_context(request.user)
    context.update(suggestion_contact_id=contact.pk, suggestion=result)
    return render(request, "contacts.html", context)
