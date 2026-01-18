from django.db import models
from django.contrib.auth.models import User
import secrets
import uuid

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('industry', 'Industry'),
        ('officer', 'Officer'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    city = models.CharField(max_length=100)
    ethereum_address = models.CharField(max_length=42, unique=True, blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)  # Default ₹1000 balance for industries
    credit_balance = models.IntegerField(default=2)  # Farmers start with 2 credits

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# ---------------------------- Tree Plantation ----------------------------

class TreePlantation(models.Model):
    farmer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Make sure it's UserProfile
    tree_count = models.IntegerField()
    proof_image = models.ImageField(upload_to="proofs/")
    verified = models.BooleanField(default=False)
# ---------------------------- Industry Wallet ----------------------------
class IndustryWallet(models.Model):
    industry = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='industry_wallet')
    credits = models.IntegerField(default=2)  # Admin grants 2 free credits annually
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)  # Default ₹1000 balance

    def __str__(self):
        return f"{self.industry.user.username} - {self.credits} credits - ₹{self.balance}"

# ---------------------------- Credit Transactions ----------------------------
class CreditTransaction(models.Model):
    transaction_id = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        default=f"TXN-{uuid.uuid4().hex[:8]}"
    )
    seller = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name="sold_credits")
    buyer = models.ForeignKey("UserProfile", on_delete=models.CASCADE, related_name="bought_credits")
    seller_eth_address = models.CharField(max_length=42)  
    buyer_eth_address = models.CharField(max_length=42)  
    credits_sold = models.IntegerField()
    eth_amount = models.DecimalField(max_digits=10, decimal_places=2)  
    transaction_date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:8]}"  # Unique formatted transaction ID
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Transaction {self.transaction_id} from {self.seller.user.username} to {self.buyer.user.username}"



class FarmerCredits(models.Model):
    farmer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credits')
    credits = models.IntegerField(default=2)  # Default 2 credits

    def __str__(self):
        return f"{self.farmer.username} - {self.credits} credits"

class Industry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)
    ethereum_address = models.CharField(max_length=255)
    credits = models.IntegerField(default=0)  # Industry credits
    last_credit_issued = models.IntegerField(default=0)  # Track the last year when credits were issued

    def __str__(self):
        return self.user.username

class CreditRequest(models.Model):
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="credit_requests_seller")
    buyer = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="credit_requests_buyer")
    credits_requested = models.PositiveIntegerField()
    eth_amount = models.DecimalField(max_digits=10, decimal_places=2)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.buyer.user.username} requested {self.credits_requested} credits"
