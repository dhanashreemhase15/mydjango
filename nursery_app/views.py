from django.shortcuts import render, HttpResponse,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from .models import product,Cart,Order
from django.db.models import Q
import random
import razorpay
from django.core.mail import send_mail
# Create your views here.
def home(request):
    context={}
    p=product.objects.filter(is_active=True) #5 objects
    #print(p)
    context['products']=p
    return render(request,'index.html',context)

def product_details(request,pid):
    p=product.objects.filter(id=pid)    #queryset<[object(1)]>
    context={}
    context['products']=p
    return render(request,'product_details.html',context)

def register(request):
    if request.method=='POST':
        uname=request.POST['uname'] #""
        upass=request.POST['upass'] #""
        ucpass=request.POST['ucpass'] #""
        context={}
        if uname=="" or upass=="" or ucpass=="":
            context['errmsg']="Fields can not be empty"
        elif upass!=ucpass:
            context['errmsg']="Password & confirm password did not matched"
        else:
            try:    
                u=User.objects.create(password=upass,username=uname,email=uname)  #colname=value
                u.set_password(upass)
                u.save()
                context['success']="User Created Successfully"
            except Exception:
                context['errmsg']="User with the same name already Exit!!"
        return render(request,'register.html',context)
        #return HttpResponse("Data is fetched "+uname)
    else:
        return render(request,'register.html')  #GET
    
def user_login(request):
    if request.method=='POST':
        uname=request.POST['uname'] #""
        upass=request.POST['upass'] #""
        context={}
        if uname=="" or upass=="":
            context['errmsg']="Fields can not be empty"
        else:
            u=authenticate(username=uname,password=upass)
            #print(u) # u.password, u.username, u.email
            if u is not None:
                login(request,u) #start session in django_session
                return redirect('/')
            else:
                context['errmsg']="Invalid username and password"
        #return HttpResponse("Data fetched"+uname)
        return render(request,'login.html',context)
    else:
        return render(request,'login.html')
    
def user_logout(request):
    logout(request)
    return redirect('/')

def addtocart(request,pid):
    userid=request.user.id     #5
    #print(pid)  #fetch 3rd object from product
    #print(userid) #fetch 5th object from user
    u=User.objects.filter(id=userid) #queryset<[object(5)]> u[0]
    p=product.objects.filter(id=pid) #queryset<[object(3)]> p[0]
    #check whether the product is there in cart or not
    q1=Q(uid=u[0]) #5
    q2=Q(pid=p[0]) #3
    c=Cart.objects.filter(q1 & q2)  #return [1 object]
    n=len(c) #1
    context={}
    context['products']=p
    if n==1:
        context['errmsg']="Product already exist in Cart!!"
    else:
        c=Cart.objects.create(uid=u[0],pid=p[0])
        c.save()
        context['success']="Product Added successfully to cart"
    return render(request,'product_details.html',context)

def viewcart(request):
    c=Cart.objects.filter(uid=request.user.id) #3 objects
    # print(c)
    # print(c[0].uid)
    # print(c[0].pid.name)
    # print(c[0].pid.price)
    n=len(c)  #3
    s=0
    for x in c:
        print(x.pid.price)
        s=s+x.pid.price * x.qty  #1300 +180 =>1480
    context={}
    context['total']=s
    context['n']=n
    context['data']=c
    return render(request,'cart.html',context)

def remove(request,cid):
    c=Cart.objects.filter(id=cid)
    c.delete()
    return redirect('/viewcart')

def updateqty(request,qv,cid):
    c=Cart.objects.filter(id=cid)  #5 <-cart id
    print(c[0].qty)
    if qv=='1':
        t=c[0].qty+1
        c.update(qty=t)
    else:
        if c[0].qty>1:
            t=c[0].qty-1
            c.update(qty=t)
    return redirect('/viewcart')

def placeorder(request):
    userid=request.user.id #4
    c=Cart.objects.filter(uid=userid)
    print(c)  #[object(5), object(6)]
    oid=random.randrange(1000,9999)   # 4 digits only
    for x in c:
        # print(x)
        # print(x.pid)
        # print(x.uid)
        # print(x.qty)
        o=Order.objects.create(order_id=oid,pid=x.pid,uid=x.uid,qty=x.qty)
        o.save()
        x.delete()
    orders=Order.objects.filter(uid=request.user.id)
    context={}
    context['data']=orders
    s=0
    n=len(orders)
    for x in orders:
        print(x.pid.price)
        s=s+x.pid.price * x.qty
    context['total']=s
    context['n']=n
    #return HttpResponse("In placeorder")
    return render(request,'placeorder.html',context)

def makepayment(request):
    orders=Order.objects.filter(uid=request.user.id)
    s=0
    n=len(orders)
    for x in orders:
        print(x.pid.price)
        s=s+x.pid.price * x.qty
        oid=x.order_id
    client = razorpay.Client(auth=("rzp_test_pjmfONoAV5hhRJ", "2qLFlWxOv0vaA1jxWEEHwbcA"))
    data = { "amount": s*100, "currency": "INR", "receipt": oid }
    payment = client.order.create(data=data)
    # print(payment)
    uemail=request.user.email
    context={}
    context['data']=payment
    context['uemail']=uemail
    # return HttpResponse('makepayment')
    return render(request,'pay.html',context)

def sendusermail(request,uemail):
    print(uemail)
    msg="Order details are -----"
    send_mail(
    "Nursery-order placed succesfully!!",
    msg,
    "dhanashreemhase15@gmail.com",
    [uemail],
    fail_silently=False,
    )
    return HttpResponse("mail send successfully")

def catfilter(request,cv):
    q1=Q(is_active=True)
    q2=Q(cat=cv)
    p=product.objects.filter(q1 & q2)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def sort(request,sv):
    if sv == '0':
        col='price'
    else:
        col='-price'
    p=product.objects.filter(is_active=True).order_by(col)
    context={}
    context['products']=p
    return render(request,'index.html',context)

def range(request):
    min=request.GET['min']
    max=request.GET['max']
    # print(min)
    # print(max)
    q1=Q(is_active=True)
    q2=Q(price__lte=max)
    q3=Q(price__gte=min)
    p=product.objects.filter(q1 & q2 & q3)
    context={}
    context['products']=p
    return render(request,'index.html',context)