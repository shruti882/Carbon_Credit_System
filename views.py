from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login  # Make sure to alias it
from django.contrib import messages
from django.contrib.auth.models import *
import random
from app.models import CreditTransaction
from .models import UserProfile, Industry, TreePlantation
from django.contrib.auth import login
import string
from django.utils.crypto import get_random_string
import secrets
from django.utils import timezone
from web3 import Web3
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth import logout as auth_logout 
from django.shortcuts import get_object_or_404
from .models import TreePlantation,CreditRequest  # Ensure this line is present
import uuid
from django.db.models import Sum
from django.db.models import F
from .models import TreePlantation



transaction_ids = {}



def generate_ethereum_address():
    """Generate a fake Ethereum address (in real cases, use web3.py)"""
    return "0x" + secrets.token_hex(20)  # Ethereum address is 42 characters (0x + 40 hex)

w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID'))  # Mainnet or Rinkeby


def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, "about.html")

# views.py

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        role = request.POST["role"]

        # Only assign city if the user is NOT an officer
        city = request.POST["city"] if role != "officer" else None  

        # Generate Ethereum address for farmers & industries
        ethereum_address = generate_ethereum_address() if role in ["farmer", "industry"] else None

        # ✅ Create user with proper password handling
        user = User.objects.create_user(username=username, password=password)

        # ✅ Create UserProfile based on role
        if role == "farmer":
            user_profile = UserProfile.objects.create(
                user=user,
                role=role,
                city=city,
                ethereum_address=ethereum_address,
                credit_balance=2  # Default 2 credits for farmers
            )
        elif role == "industry":
            user_profile = UserProfile.objects.create(
                user=user,
                role=role,
                city=city,
                ethereum_address=ethereum_address,
                wallet_balance=1000  # Default ₹1000 for industries
            )
        elif role == "officer":
            user_profile = UserProfile.objects.create(
                user=user,
                role=role
            )

        # ✅ Log in the user immediately after registration
        login(request, user)
        
        # ✅ Redirect user to the correct dashboard
        if role == "officer":
            return redirect("app:login")
        elif role == "farmer":
            return redirect("app:login")
        elif role == "industry":
            return redirect("app:login")

    return render(request, "register.html")



def login_view(request):
    # Handle POST request (user login)
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login user
            login(request, user)
            
            # Get the user profile to check the role
            user_profile = UserProfile.objects.get(user=user)
            
            # Redirect based on role
            if user_profile.role == 'officer':
                return redirect('app:officer_dashboard')  # Officer dashboard URL
            elif user_profile.role == 'farmer':
                return redirect('app:farmer_dashboard')  # Farmer dashboard URL
            elif user_profile.role == 'industry':
                return redirect('app:industry_dashboard')  # Industry dashboard URL
            else:
                messages.error(request, "Role not recognized.")
                return redirect('app:login')
        else:
            # If authentication failed
            messages.error(request, "Invalid credentials")
            return redirect('app:login')
    
    # Handle GET request (render login page)
    return render(request, 'login.html')  # Render your login page template
@login_required
def plant_tree(request):
    if request.user.groups.filter(name='Farmer').exists():
        if request.method == "POST":
            tree_name = request.POST['name']
            species = request.POST['species']
            credits = 100  # 100 tree = 1 credit (You can adjust logic)
            
            tree = Tree.objects.create(name=tree_name, species=species, planted_by=request.user, credits=credits)
            return redirect('app:farmer_dashboard')
    
    return render(request, 'plant_tree.html')  # Render the form for planting a tree


@login_required
def officer_dashboard(request):
    if request.user.userprofile.role != 'officer':
        return redirect('app:dashboard')  # Only officers can access

    farmers = UserProfile.objects.filter(role='farmer')
    industries = UserProfile.objects.filter(role='industry')  # ✅ Correct model
    proofs = TreePlantation.objects.filter(verified=False)  # ✅ Only show unverified proofs
    transactions = CreditTransaction.objects.all()  # ✅ Fetch all transactions

    context = {
        'farmers': farmers,
        'industries': industries,  # ✅ Fetch industries correctly
        'proofs': proofs,
        'transactions': transactions  # ✅ Added transaction history
    }
    return render(request, 'officer_dashboard.html', context)




def issue_free_credits(request):
    if request.method == "POST" and request.user.userprofile.role == 'officer':
        current_year = timezone.now().year # Get the current year

        for industry in Industry.objects.all():
            if industry.last_credit_issued != current_year:
                industry.credits += 2  # Add 2 free credits
                industry.last_credit_issued = current_year
                industry.save()

        messages.success(request, "2 free credits issued to all industries for this year!")
    return redirect('app:officer_dashboard')


def submit_proof_page(request):
    # Fetch proof records of the logged-in farmer
    user_profile = UserProfile.objects.get(user=request.user)
    proofs = TreePlantation.objects.filter(farmer=user_profile)

    return render(request, "submit_proof.html", {"proofs": proofs})

@login_required


def farmer_dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)  # ✅ Get logged-in farmer
    industries = UserProfile.objects.filter(role='industry', city=user_profile.city)  # ✅ Industries in same city
    proofs = TreePlantation.objects.filter(farmer=user_profile)  # ✅ Tree proofs
    transactions = CreditTransaction.objects.filter(seller=user_profile)  # ✅ Completed transactions

    # ✅ Fetch only pending credit requests
    pending_requests = CreditRequest.objects.filter(seller=user_profile, status="pending")

    context = {
        "user_profile": user_profile,
        "industries": industries,  # ✅ Include industries in the same city
        "proofs": proofs,  # ✅ Include tree proofs
        "transactions": transactions,  # ✅ Show completed transactions
        "pending_requests": pending_requests,  # ✅ Show pending requests
        "wallet_balance": user_profile.wallet_balance,  # ✅ Include wallet balance
    }
    return render(request, "farmer_dashboard.html", context)

@login_required
def send_credit_request(request, farmer_id):
    if request.method == "POST":
        industry = request.user.userprofile
        farmer = get_object_or_404(UserProfile, id=farmer_id, role="farmer")

        credits_requested = int(request.POST.get("credits_requested", 0))
        
        if credits_requested <= 0 or credits_requested > farmer.credit_balance:
            return JsonResponse({"error": "Invalid credit request"}, status=400)

        eth_amount = credits_requested * 0.1  # Example conversion: 1 credit = 0.1 ETH

        CreditRequest.objects.create(
            seller=farmer,
            buyer=industry,
            credits_requested=credits_requested,
            eth_amount=eth_amount,
            status="pending"
        )

        return redirect("app:industry_dashboard")
    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required
def approve_credit_request(request, transaction_id):
    # Fetch the credit request, ensuring it exists and is pending
    credit_request = get_object_or_404(CreditRequest, id=transaction_id, status="pending")

    seller = credit_request.seller  # Farmer
    buyer = credit_request.buyer  # Industry

    # Check if the farmer has enough credits
    if seller.credit_balance < credit_request.credits_requested:
        messages.error(request, "Not enough credits available!") 
        return redirect("farmer_dashboard")

    # Check if the industry has enough ETH to buy credits
    if buyer.wallet_balance < credit_request.eth_amount:
        messages.error(request, "Industry does not have enough ETH!")
        return redirect("farmer_dashboard")

    # Generate a unique transaction ID
    transaction_id = get_random_string(12)

    # Create a transaction record
    CreditTransaction.objects.create(
        transaction_id=transaction_id,
        seller=seller,
        buyer=buyer,
        credits_sold=credit_request.credits_requested,
        eth_amount=credit_request.eth_amount,
    )

    # Update balances
    seller.credit_balance -= credit_request.credits_requested
    seller.wallet_balance += credit_request.eth_amount
    buyer.wallet_balance -= credit_request.eth_amount

    seller.save()
    buyer.save()

    # Update the credit request status
    credit_request.status = "approved"
    credit_request.save()

    messages.success(request, "Transaction approved successfully!")
    return redirect("app:farmer_dashboard")


@login_required
def reject_credit_request(request, transaction_id):
    credit_request = get_object_or_404(CreditRequest, id=transaction_id, status="pending")
    credit_request.status = "rejected"
    credit_request.save()

    messages.success(request, "Credit request rejected successfully!")
    
    return redirect("app:farmer_dashboard")  # Use namespace


@login_required
def process_transaction(request, request_id):
    credit_request = get_object_or_404(CreditRequest, id=request_id)

    # ✅ Ensure the request has been approved before proceeding
    if credit_request.status != "approved":
        messages.error(request, "Transaction cannot proceed without approval.")
        return redirect("app:farmer_dashboard")

    # ✅ Ensure the farmer still has enough credits
    if credit_request.seller.credit_balance < credit_request.credits_requested:
        messages.error(request, "Not enough credits available.")
        return redirect("app:farmer_dashboard")

    # ✅ Ensure the industry still has enough ETH
    if credit_request.buyer.wallet_balance < credit_request.eth_amount:
        messages.error(request, "Industry does not have enough ETH.")
        return redirect("app:farmer_dashboard")

    # ✅ **Perform the transaction now**
    CreditTransaction.objects.create(
        seller=credit_request.seller,
        buyer=credit_request.buyer,
        seller_eth_address=credit_request.seller.ethereum_address,
        buyer_eth_address=credit_request.buyer.ethereum_address,
        credits_sold=credit_request.credits_requested,
        eth_amount=credit_request.eth_amount,
    )

    # ✅ Update balances (Only now the ETH and credits move)
    credit_request.seller.credit_balance -= credit_request.credits_requested  # Deduct from farmer
    credit_request.buyer.credit_balance += credit_request.credits_requested  # Add to industry
    credit_request.buyer.wallet_balance -= credit_request.eth_amount  # Deduct ETH from industry
    credit_request.seller.wallet_balance += credit_request.eth_amount  # Add ETH to farmer

    # ✅ Save updated balances
    credit_request.seller.save()
    credit_request.buyer.save()

    messages.success(request, "Transaction completed successfully!")
    return redirect("app:farmer_dashboard")

@login_required
def upload_proof(request):
    if request.method == "POST":
        tree_count = request.POST["tree_count"]
        proof_image = request.FILES["proof_image"]
        
        # Get the UserProfile instance for the logged-in farmer
        farmer_profile = UserProfile.objects.get(user=request.user)

        # Create TreePlantation entry
        TreePlantation.objects.create(
            farmer=farmer_profile,  # ✅ Correct UserProfile assignment
            tree_count=tree_count,
            proof_image=proof_image,
            verified=False  # Default: Not yet verified
        )

        messages.success(request, "Proof uploaded successfully!")
        return redirect("app:farmer_dashboard")

    return render(request, "upload_proof.html")


@login_required
def upload_tree_proof(request):
    if request.method == "POST":
        tree_count = request.POST.get("tree_count")
        image = request.FILES.get("image")

        if tree_count and image:
            TreePlantation.objects.create(
                farmer=request.user,
                tree_count=int(tree_count),
                image=image,
                verified=False
            )
            return redirect("app:farmer_dashboard")

    return render(request, "upload_tree_proof.html")

@login_required
def verify_tree_proof(request, proof_id):
    if request.user.userprofile.role != 'officer':
        return redirect('app:dashboard')  # Only officers can verify

    proof = get_object_or_404(TreePlantation, id=proof_id)

    # ✅ Directly get the farmer's UserProfile
    farmer_profile = proof.farmer  # `proof.farmer` is already a UserProfile instance

    # ✅ Update credits correctly
    farmer_profile.credit_balance += proof.tree_count // 100  # 100 trees = 1 credit
    farmer_profile.save()

    # ✅ Mark proof as verified
    proof.verified = True
    proof.save()

    return redirect('app:officer_dashboard')

@login_required
def industry_dashboard(request):
    industry = request.user.userprofile  # ✅ Get logged-in industry

    wallet_balance = industry.wallet_balance  # ✅ Industry wallet balance

    # ✅ Include the free 2 credits given every year
    total_credits_bought = CreditTransaction.objects.filter(buyer=industry).aggregate(total=Sum('credits_sold'))['total'] or 0
    industry_credit_balance = 2 + total_credits_bought  # ✅ Free 2 credits + bought credits

    # ✅ Get farmers in the same city who have credits to sell
    farmers = UserProfile.objects.filter(city=industry.city, role="farmer", credit_balance__gt=0)

    # ✅ Get credit requests made by this industry (all statuses)
    credit_requests = CreditRequest.objects.filter(buyer=industry).select_related('seller')

    # ✅ Get industry requests (approved & rejected separately)
    approved_requests = credit_requests.filter(status="approved")
    rejected_requests = credit_requests.filter(status="rejected")

    # ✅ Get transaction history for this industry
    transactions = CreditTransaction.objects.filter(buyer=industry).select_related('seller')

    # ✅ Include sent requests
    sent_requests = credit_requests  # (Since credit_requests already filters by buyer)

    return render(request, "industry_dashboard.html", {
        "user_profile": industry,
        "wallet_balance": wallet_balance,
        "industry_credit_balance": industry_credit_balance,  # ✅ Correctly calculated balance
        "farmers": farmers,
        "credit_requests": credit_requests,  # ✅ Show all credit requests
        "industry_requests": credit_requests,  # ✅ Same as sent_requests
        "approved_requests": approved_requests,  # ✅ Show approved requests separately
        "rejected_requests": rejected_requests,  # ✅ Show rejected requests separately
        "transactions": transactions,  # ✅ Show transaction history
        "sent_requests": sent_requests,  # ✅ Include sent requests
    })
def request_credits_page(request):
    # Get farmers in the same city as the logged-in industry
    industry = request.user.userprofile
    farmers = UserProfile.objects.filter(role="farmer", city=industry.city)


    return render(request, "request_credits.html", {"farmers": farmers})

@login_required
def verify_tree_proof(request, proof_id):
    # Only officers are allowed to verify proofs
    if request.user.userprofile.role != "officer":
        messages.error(request, "You are not authorized to verify proofs.")
        return redirect("app:officer_dashboard")
    
    # Retrieve the proof object
    proof = get_object_or_404(TreePlantation, id=proof_id)
    
    # Mark the proof as verified
    proof.verified = True
    proof.save()
    
    messages.success(request, "Proof verified successfully!")
    return redirect("app:view_proofs")  # Or whichever URL name you use to show proofs
@login_required
def available_farmers(request):
    farmers = UserProfile.objects.filter(role='farmer', credit_balance__gt=0)
    return render(request, 'available_farmers.html', {'farmers': farmers})


@login_required
def buy_credits(request, farmer_id):
    if request.method == "POST":
        buyer = request.user.userprofile  # Logged-in industry
        seller = get_object_or_404(UserProfile, id=farmer_id, role="farmer")

        credits_requested = int(request.POST.get("credits_requested"))
        eth_amount = float(request.POST.get("eth_amount"))

        # ❌ Prevent auto transaction (Only create a request)
        CreditRequest.objects.create(
            seller=seller,
            buyer=buyer,
            credits_requested=credits_requested,
            eth_amount=eth_amount,
            status="pending"  # ✅ Default status is pending
        )

        messages.success(request, "Credit request sent to the farmer!")
        return redirect("industry_dashboard")  # Redirect to industry dashboard

    return redirect("industry_dashboard")  # If not POST request
@login_required
def sell_credits(request, industry_id):
    farmer_credits = FarmerCredits.objects.get(farmer=request.user.userprofile)  # ✅ Get farmer's profile
    industry_profile = UserProfile.objects.get(user__id=industry_id, role="industry")  # ✅ Get industry profile
    industry_wallet = IndustryWallet.objects.get(industry=industry_profile)

    if request.method == 'POST':
        credits_to_sell = int(request.POST.get('credits', 0))
        price = credits_to_sell * 500  # Example price per credit

        if credits_to_sell > farmer_credits.credits:
            messages.error(request, "Not enough credits to sell.")
            return redirect('app:farmer_dashboard')

        if industry_wallet.balance < price:
            messages.error(request, "Industry does not have enough balance.")
            return redirect('app:industry_dashboard')

        # ✅ Transfer credits
        farmer_credits.credits -= credits_to_sell
        farmer_credits.save()

        industry_wallet.credits += credits_to_sell
        industry_wallet.balance -= price
        industry_wallet.save()

        # ✅ Ensure correct user profile references
        CreditTransaction.objects.create(
            seller=request.user.userprofile,  # ✅ Store UserProfile of farmer
            buyer=industry_profile,  # ✅ Store UserProfile of industry
            credits_sold=credits_to_sell
        )

        messages.success(request, "Credits sold successfully.")

    return redirect('app:farmer_dashboard')
def complete_transaction(request, farmer_id):
    industry = request.user.userprofile  # Get industry profile
    farmer = get_object_or_404(UserProfile, id=farmer_id, role='farmer')

    credits_to_buy = int(request.POST.get('credits'))
    eth_amount = credits_to_buy * 1  # Assuming 1 credit = 1 ETH

    # Check if the farmer has enough credits
    if credits_to_buy > farmer.credit_balance:
        messages.error(request, "Farmer does not have enough credits.")
        return redirect('app:industry_dashboard')

    # Check if industry has enough ETH
    if eth_amount > industry.wallet_balance:
        messages.error(request, "You do not have enough ETH to complete this transaction.")
        return redirect('app:industry_dashboard')

    # Deduct credits from farmer
    farmer.credit_balance -= credits_to_buy
    farmer.save()  # ✅ Automatically updates the database

    # Deduct ETH from industry
    industry.wallet_balance -= eth_amount
    industry.save()  # ✅ Automatically updates the database

    # Create a transaction record
    transaction = CreditTransaction.objects.create(
        seller=farmer,
        buyer=industry,
        credits_sold=credits_to_buy,
        eth_amount=eth_amount,
    )

    messages.success(request, f"Transaction successful! You bought {credits_to_buy} credits.")
    return redirect('app:industry_dashboard')

@login_required
def view_proofs(request):
    if request.user.userprofile.role != "officer":
        return redirect("app:officer_dashboard")  # Redirect non-officers

    proofs = TreePlantation.objects.filter(verified=False)
    return render(request, "view_proofs.html", {"proofs": proofs})

@login_required
def verify_proof(request, proof_id):
    # Only allow officers to verify proofs
    if request.user.userprofile.role != "officer":
        messages.error(request, "You are not authorized to verify proofs.")
        return redirect("app:officer_dashboard")
    
    # Get the proof object; if not found, raise a 404 error
    proof = get_object_or_404(TreePlantation, id=proof_id)
    
    # Mark the proof as verified and save changes
    proof.verified = True
    proof.save()
    
    messages.success(request, "Proof verified successfully!")
    # Redirect to the page that displays all proofs (make sure this URL exists)
    return redirect("app:view_proofs")

@login_required
def reject_proof(request, proof_id):
    if request.user.userprofile.role != "officer":
        return redirect("app:officer_dashboard")

    proof = get_object_or_404(TreePlantation, id=proof_id)
    proof.delete()  # Delete rejected proof
    return redirect("app:view_proofs")  # Redirect back to proofs page

def reject_tree_proof(request, proof_id):
    proof = get_object_or_404(TreePlantation, id=proof_id)
    proof.verified = False  # Mark it as rejected
    proof.save()
    messages.error(request, f"Proof for {proof.farmer.user.username} has been rejected.")
    return redirect("app:view_proofs")
# Logout view
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def logout_view(request):
    auth_logout(request)  # Use the Django logout function
    return redirect('app:login')  # Redirect to the login page

