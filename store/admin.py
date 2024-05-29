from django.contrib import admin
from .models import *

class GenderAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name", )}
class CategoryAdmin(admin.ModelAdmin):

    prepopulated_fields = {"slug": ("name", )}

class ProductAdmin(admin.ModelAdmin):

    prepopulated_fields = {"slug": ("name", )}

class UserAdmin(admin.ModelAdmin):
    fields = ('username', 'first_name', 'last_name',\
                    'middle_name', 'email', 'date_joined','phone_number')
    list_display = ('username','first_name', 'last_name',\
                    'middle_name', 'email', 'date_joined','phone_number')

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'text', 'rating', 'created_at')
    list_filter = ('product', 'rating', 'created_at')
    search_fields = ('text', 'user__username')
    actions = ['delete_selected']


admin.site.register(User ,UserAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Gender,GenderAdmin)
admin.site.register(Order)
admin.site.register(Address)
admin.site.register(OrderProduct)
admin.site.register(Favorite)
admin.site.register(Size)
admin.site.register(Comment, CommentAdmin)