from django import forms
from .models import ReceiverMailing, Message, Mailing
from django.utils import timezone

class ReceiverForm(forms.ModelForm):
    class Meta:
        model = ReceiverMailing
        fields = ['email', 'full_name', 'comm']

    def __init__(self, *args, **kwargs):
        super(ReceiverForm, self).__init__(*args, **kwargs)

        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите email получателя'
        })

        self.fields['full_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите фио получателя'
        })

        self.fields['comm'].widget.attrs.update({
            'class': 'form-select',
            'placeholder': 'Введите комментарий'
        })

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['topic', 'text']

    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)

        self.fields['topic'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите тему сообщения'
        })

        self.fields['text'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите текст сообщения'
        })


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ['start_time', 'end_time', 'message', 'receivers']

    def __init__(self, *args, **kwargs):
        super(MailingForm, self).__init__(*args, **kwargs)

        self.fields['start_time'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        self.fields['start_time'].widget.attrs.update({
            'class': 'form-control datetimepicker',
            'placeholder': 'Выберите дату и время начала'
        })

        self.fields['end_time'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        self.fields['end_time'].widget.attrs.update({
            'class': 'form-control datetimepicker',
            'placeholder': 'Выберите дату и время окончания'
        })

        self.fields['message'].queryset = Message.objects.all()
        self.fields['message'].widget.attrs.update({
            'class': 'form-select',
            'placeholder': 'Выберите сообщение для рассылки'
        })

        self.fields['receivers'].queryset = ReceiverMailing.objects.all()
        self.fields['receivers'].widget.attrs.update({
            'class': 'form-check',
            'placeholder': 'Выберите пользователя для рассылки'
        })

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Время окончания должно быть позже времени начала")

            if self.instance.pk is None and start_time < timezone.now():
                raise forms.ValidationError("Время начала не может быть в прошлом")

        return cleaned_data
