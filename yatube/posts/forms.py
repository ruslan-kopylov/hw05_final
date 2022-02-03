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
                'creat': 'Текст нового поста',
                'edit': 'Текст поста'
            },
            'group': {
                'creat': 'Группа, к которой будет относиться пост',
                'edit': 'Группа, к которой относится пост'
            }
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
