from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import  Cart, CartItem
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


# Create your views here.

def _cart_id(request):
    # creando la cart
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    current_user = request.user
    product  = Product.objects.get(id=product_id)  #obteniendo el producto
    #validamios si el user esta is_authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == 'POST':
            #dinamic
            for item in request.POST:
                key = item
                value =  request.POST[key]
                try:
                    variation = Variation.objects.get(product = product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass


        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            # pasos para hacer que los item si tienen la mismo variaciones se agrupen y no esten individual
            #existing variations -> database
            #current variation ->  product_variation
            # item_id ->database

            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)


            if product_variation in ex_var_list:
                # incrementamos la cantidad en el grupo de var iguales
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                # obtuvimos el id del producto
                item =CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()


            else:
                # creamos un nuevo item en la cart
                item =CartItem.objects.create(product=product, quantity = 1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product  =  product,
                quantity = 1,
                user = current_user,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')

        #si el cliente no esta auten
    else:
        product_variation = []
        if request.method == 'POST':
            #dinamic
            for item in request.POST:
                key = item
                value =  request.POST[key]
                try:
                    variation = Variation.objects.get(product = product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                except:
                    pass
            #static
            # color = request.POST['color']
            # size = request.POST['size']
                # print(key, value)
                # return HttpResponse(color + ' ' + size)
                # exit()

        try:
            cart = Cart.objects.get(cart_id=_cart_id(request)) #obteniendo la cart y  el cart id presente en la session
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id  =  _cart_id(request)
            )
        cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            # pasos para hacer que los item si tienen la mismo variaciones se agrupen y no esten individual
            #existing variations -> database
            #current variation ->  product_variation
            # item_id ->database

            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id.append(item.id)
            print(ex_var_list)

            if product_variation in ex_var_list:
                # incrementamos la cantidad en el grupo de var iguales
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                # obtuvimos el id del producto
                item =CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()


            else:
                # creamos un nuevo item en la cart
                item =CartItem.objects.create(product=product, quantity = 1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(
                product  =  product,
                quantity = 1,
                cart =  cart,
            )
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
        return redirect('cart')

#decrementando y eliminanado un item de cart
def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        #aki vamos adecrementar caundo estamos is_authenticated
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        #aki vamos adecrementar caundo estamos is_authenticated

        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

#borrando el cart item completo
def remove_cart_item(request, product_id, cart_item_id):

    product = get_object_or_404(Product, id=product_id)
    #borrando el cart item completo cuando is_authenticated
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
    #borrando el cart item completo cuando is_authenticated
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')




def cart(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass #ignorando y siguiendo

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass #ignorando y siguiendo

    context={
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)
