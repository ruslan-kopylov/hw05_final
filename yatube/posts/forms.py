from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        }
        help_texts = {
            'text': {
                'create': 'Текст нового поста',
                'edit': 'Текст поста'
            },
            'group': {
                'create': 'Группа, к которой будет относиться пост',
                'edit': 'Группа, к которой относится пост'
            },
            'image': 'Иллюстрация к посту'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
