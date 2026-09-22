from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import OperationalError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from . import suggestions
from .models import Contact, TagSuggestion


STALE = "This suggestion is no longer current. Please request a new suggestion."
UNAVAILABLE = "Tag suggestions are unavailable right now. Please try again later."


def notify(request, text):
    # Cookie-backed messages can survive logout; bind feedback to its owner.
    messages.info(request, text, extra_tags=str(request.user.pk))


def filter_tag(request):
    value = request.POST.get("tag", "") if request.method == "POST" else request.GET.get("tag", "")
    return value if value in Contact.Tag.values else ""


def list_url(tag):
    return reverse("contacts") + ("?" + urlencode({"tag": tag}) if tag else "")


def owned_suggestion(request, suggestion_id):
    return get_object_or_404(
        TagSuggestion.objects.select_related("contact"),
        pk=suggestion_id, requester=request.user, contact__owner=request.user,
    )


@login_required
@never_cache
@require_POST
def suggest_tag(request, contact_id):
    contact = get_object_or_404(Contact, pk=contact_id, owner=request.user)
    tag = filter_tag(request)
    data = suggestions.snapshot(contact)
    signature = suggestions.fingerprint(data)
    TagSuggestion.objects.filter(contact=contact, requester=request.user).delete()
    try:
        result = suggestions.validate_result(suggestions.request_suggestion(data))
    except suggestions.SuggestionUnavailable:
        notify(request, UNAVAILABLE)
        return redirect(list_url(tag))
    contact = get_object_or_404(Contact, pk=contact_id, owner=request.user)
    if suggestions.fingerprint(suggestions.snapshot(contact)) != signature:
        notify(request, STALE)
        return redirect(list_url(tag))
    if result["tag"] is None or result["tag"] == contact.tag:
        heading = "Not enough information to suggest a tag." if result["tag"] is None else "The current tag still fits."
        notify(request, f"{contact.name}: {heading} {result['reason']}")
        return redirect(list_url(tag))
    try:
        with transaction.atomic():
            TagSuggestion.objects.filter(contact=contact, requester=request.user).delete()
            pending = TagSuggestion.objects.create(
                contact=contact, requester=request.user, proposed_tag=result["tag"],
                explanation=result["reason"], fingerprint=signature,
            )
    except OperationalError:
        notify(request, "Another request is in progress. Please try again.")
        return redirect(list_url(tag))
    review_url = reverse("review_tag", args=[pending.pk])
    return redirect(review_url + ("?" + urlencode({"tag": tag}) if tag else ""))


@login_required
@never_cache
@require_GET
def review_tag(request, suggestion_id):
    pending = owned_suggestion(request, suggestion_id)
    stale = pending.is_expired() or pending.fingerprint != suggestions.fingerprint(suggestions.snapshot(pending.contact))
    return render(request, "tag_suggestion.html", {
        "suggestion": pending, "contact": pending.contact, "stale": stale,
        "selected_tag": filter_tag(request), "return_url": list_url(filter_tag(request)),
    })


@login_required
@never_cache
@require_POST
def accept_tag(request, suggestion_id):
    tag = filter_tag(request)
    try:
        with transaction.atomic():
            pending = owned_suggestion(request, suggestion_id)
            # Taking the SQLite write lock before re-reading the contact prevents
            # another writer from changing it between validation and update.
            deleted, _ = TagSuggestion.objects.filter(pk=pending.pk).delete()
            if not deleted:
                raise Http404
            contact = get_object_or_404(Contact, pk=pending.contact_id, owner=request.user)
            if (pending.is_expired() or pending.proposed_tag not in Contact.Tag.values
                    or pending.fingerprint != suggestions.fingerprint(suggestions.snapshot(contact))):
                notice = STALE
            else:
                contact.tag = pending.proposed_tag
                contact.save(update_fields=["tag"])
                notice = f"Tag updated to {contact.get_tag_display()} for {contact.name}."
    except OperationalError:
        notice = "Another request is in progress. Please try again."
    notify(request, notice)
    return redirect(list_url(tag))


@login_required
@never_cache
@require_POST
def decline_tag(request, suggestion_id):
    pending = owned_suggestion(request, suggestion_id)
    expired = pending.is_expired()
    pending.delete()
    notify(request, STALE if expired else "Suggestion declined. The contact tag is unchanged.")
    return redirect(list_url(filter_tag(request)))
