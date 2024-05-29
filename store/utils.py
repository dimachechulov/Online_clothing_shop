from .models import *
def get_user_context(dict,request):
    context = dict
    genders = Gender.objects.all()
    ordered = 1
    if not request.user.is_authenticated:
        ordered = 0
    else:
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            context["order"] = order_qs[0]

        else:
            ordered = 0
    context["genders"] = genders
    context["gender_selected"] = -1
    context["cat_selected"] = -1

    context["ordered"] = ordered
    return context
