from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
import secrets, requests, json
from .models import Membership, PayHistory, Subscription, UserMembership
import datetime
from datetime import timedelta
from datetime import datetime as dt



def gen_token(length=10, charset="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"):
	return "".join([secrets.choice(charset) for _ in range(0, length)])


def init_payment(amount, email):
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': 'Bearer sk_test_5962ae85817f9a90c7266dc2a5a87ea997c073b6',
        'Content-Type' : 'application/json',
        'Accept': 'application/json',
        }
    datum = {
        "email": email,
        "amount": amount,
        "reference": "OLX-"+gen_token(),
        "callback_url": "http://localhost:3000/Subscribe",
        }
    x = requests.post(url, data=json.dumps(datum), headers=headers)
    if x.status_code != 200:
        return str(x.status_code)
    
    results = x.json()
    return results

def verify_payment(reference):
    url = 'https://api.paystack.co/transaction/verify/'+reference
    headers = {
        'Authorization': 'Bearer sk_test_5962ae85817f9a90c7266dc2a5a87ea997c073b6',
        'Content-Type' : 'application/json',
        'Accept': 'application/json',
        }
    datum = {
        "reference": reference
    }
    x = requests.get(url, data=json.dumps(datum), headers=headers)
    if x.status_code != 200:
        return str(x.status_code)
    
    results = x.json()
    return results

class CustomUserCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format='json'):
        serializer = CustomUserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request, format='None'):
    #     data = self.request.data
        
    #     user_name = data['user_name']
    #     email = data['email']
    #     password = data['password']
    #     password2 = data['password2']

    #     if password == password2:
    #         if User.objects.filter(email=email).exists():
    #             return Response({'error': 'Email already exists'})
    #         else:
    #             if len(password) < 6:
    #                 return Response({'error': 'Password must be at least 6 characters'})
    #             else:
    #                 user = User.objects.create_user(email=email, password=password, user_name=user_name)
    #                 user.save()

    #                 return Response({'success': 'User created successfully'})

    #     else:
    #         return Response({'error': 'Passwords do not match'})

class BlacklistTokenUpdateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# class GetUserName(APIView):
#         permission_classes = [AllowAny]

#         def get(self, request, format=None):
#             user = NewUser.objects.all()
#             serializer = CustomUserSerializer(user, many=True)
#             return Response(serializer.data)

#             # if serializer.is_valid():
#             #     json = serializer.data.user_name
#             #     return Response(json, status=status.HTTP_201_CREATED)



class ProtectedPage(APIView):
    def get(self, request):
        if request.user.is_authenticated == False:
            return Response({"status": False, "message": "You are not logged in yet."}, status=status.HTTP_401_UNAUTHORIZED)
        user_membership = UserMembership.objects.get(user=request.user)
        subscriptions = Subscription.objects.filter(user_membership=user_membership).exists()
        if subscriptions:
            return Response({"status": True, "message": "This user has paid"}, status=status.HTTP_200_OK)
        else:
            return Response({"status": False, "message": "This user has not paid"}, status=status.HTTP_400_BAD_REQUEST)

class SubscribeUser(APIView):
    def post(self, request):
        if request.user.is_authenticated == False:
            return Response({"status": False, "message": "You are not logged in yet."}, status=status.HTTP_401_UNAUTHORIZED)
        plan = request.data.get('sub_plan')
        fetch_membership = Membership.objects.filter(membership_type=plan).exists()
        if fetch_membership == False:
            return Response({"status": False, "message": "The Plan you entered does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        membership = Membership.objects.get(membership_type=plan)
        price = float(membership.price)*100 # We need to multiply the price by 100 because Paystack receives in kobo and not naira.
        price = int(price)
        initialized = init_payment(price, request.user.email)
        amount = price/100
        instance = PayHistory.objects.create(amount=amount, payment_for=membership, user=request.user, paystack_charge_id=initialized['data']['reference'], paystack_access_code=initialized['data']['access_code'])
        UserMembership.objects.filter(user=instance.user).update(reference_code=initialized['data']['reference'])
        return Response({"status": True, "message": "User can now proceed to make payment with the Authorization URL", "data": initialized["data"]}, status=status.HTTP_200_OK)
    
    def get(self, request):
        ref_code = request.GET.get("reference")
        check_pay = PayHistory.objects.filter(paystack_charge_id=ref_code).exists()
        if check_pay == False:
            # This means payment was not made error should be thrown here...
            return Response({"status": False, "message": "Invalid Reference code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            payment = PayHistory.objects.get(paystack_charge_id=ref_code)
            initialized = verify_payment(ref_code)
            if initialized['data']['status'] == 'success':
                PayHistory.objects.filter(paystack_charge_id=initialized['data']['reference']).update(paid=True)
                new_payment = PayHistory.objects.get(paystack_charge_id=initialized['data']['reference'])
                instance = Membership.objects.get(id=new_payment.payment_for.id)
                sub = UserMembership.objects.filter(reference_code=initialized['data']['reference']).update(membership=instance)
                user_membership = UserMembership.objects.get(reference_code=ref_code)
                Subscription.objects.create(user_membership=user_membership, expires_in=dt.now().date() + timedelta(days=user_membership.membership.duration))
                return Response({"status": True, "message": "Payment successful. Subscription has been purchased.", "data": initialized["data"]}, status=status.HTTP_200_OK)
            elif initialized["data"]["status"] == "abandoned":
                return Response({"status": False, "message": "Payment was abandoned. Subscription has not been purchased."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"status": False, "message": "Payment Unsuccessful. Subscription has not been purchased."}, status=status.HTTP_400_BAD_REQUEST)
