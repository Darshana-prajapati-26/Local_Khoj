from django import forms
from django.utils.text import slugify
from .models import Service, ServiceCategory


class VendorServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['category', 'name', 'slug', 'description', 'price', 'duration_minutes', 'image', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['slug'].required = False
        self.fields['slug'].help_text = 'Leave blank to auto-generate.'

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        name = self.cleaned_data.get('name', '')
        if not slug and name:
            slug = slugify(name)
        # Ensure uniqueness
        if slug:
            qs = Service.objects.filter(slug=slug)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                slug = f"{slug}-{Service.objects.count()}"
        return slug
