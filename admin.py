from django.contrib import admin
# Register your models here.
from .models import UserProfile,CreditTransaction,TreePlantation,FarmerCredits,IndustryWallet

admin.site.register(UserProfile)
# admin.site.register(Tree)
admin.site.register(CreditTransaction)
admin.site.register(TreePlantation)
admin.site.register(FarmerCredits)
admin.site.register(IndustryWallet)