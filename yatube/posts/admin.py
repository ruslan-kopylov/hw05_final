from django.contrib import admin
from .models import Post, Group, Comment


class CommentInline(admin.TabularInline):
    model = Comment
    list_display = ["id", "author", "post"]
    readonly_fields = ["id", "author", "post", "text"]
    ordering = ["id"]
    extra = 0


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'post', 'text')
    list_filter = ('author',)
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    inlines = (CommentInline,)
    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment, CommentAdmin)
