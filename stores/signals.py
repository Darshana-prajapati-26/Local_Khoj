"""
Signals to keep Store.rating and Store.total_reviews in sync
whenever a StoreReview is created, updated, or deleted.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg


@receiver(post_save, sender='stores.StoreReview')
def update_store_rating_on_save(sender, instance, **kwargs):
    _recalculate(instance.store)


@receiver(post_delete, sender='stores.StoreReview')
def update_store_rating_on_delete(sender, instance, **kwargs):
    _recalculate(instance.store)


def _recalculate(store):
    """Recompute avg rating and review count, then save only those fields."""
    from stores.models import StoreReview
    qs = StoreReview.objects.filter(store=store, is_approved=True)
    agg = qs.aggregate(avg=Avg('rating'))
    avg = round(agg['avg'] or 0.0, 1)
    count = qs.count()
    # Use update() to avoid triggering Store.save() recursion
    from stores.models import Store
    Store.objects.filter(pk=store.pk).update(rating=avg, total_reviews=count)
