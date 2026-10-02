from django import forms
from django.utils.text import slugify
from .models import Product, ProductReview, ProductCategory


class ProductForm(forms.ModelForm):
    category_new = forms.CharField(
        required=False,
        label="New Product Category (if not listed)",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Snacks"})
    )
    # Removed store category from vendor add product page

    class Meta:
        model = Product
        exclude = ["store"]   # store will be assigned automatically

    def __init__(self, *args, **kwargs):
        store = kwargs.pop("store", None)
        super().__init__(*args, **kwargs)
        s = store or getattr(self.instance, "store", None)
        if "store_category" in self.fields:
            self.fields.pop("store_category")

    def clean(self):
        cleaned = super().clean()
        cat = cleaned.get("category")
        cat_new = (cleaned.get("category_new") or "").strip()
        if not cat and cat_new:
            base_slug = slugify(cat_new or "category")
            slug = base_slug
            i = 1
            while ProductCategory.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{i}"
                i += 1
            obj, _ = ProductCategory.objects.get_or_create(name=cat_new, defaults={"slug": slug})
            cleaned["category"] = obj
        # store category removed from form
        return cleaned


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ["rating", "content", "image"]

    def clean_rating(self):
        r = self.cleaned_data["rating"]
        if r < 1 or r > 5:
            raise forms.ValidationError("Rating must be between 1 and 5")
        return r


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ["name", "slug"]
