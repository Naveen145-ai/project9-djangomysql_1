from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
import json
import urllib.request
import urllib.error

def home(request):
    trending_products = Product.objects.filter(trending=1)
    context = {'trending_products':trending_products}
    return render(request, "store/index.html",context)

def collections(request):
    category = Category.objects.filter(status=0)
    context = {'category': category}
    return render(request, "store/collections.html", context)

def collectionsview(request, slug):
    if Category.objects.filter(slug=slug, status=0).exists():
        category = Category.objects.filter(slug=slug).first()
        products = Product.objects.filter(category=category)
        context = {'products': products, 'category_name': category}
        return render(request, "store/products/index.html", context)
    else:
        messages.warning(request, "No such category found")
        return redirect('collections')

def Productview(request, cate_slug, prod_slug):
    if Category.objects.filter(slug=cate_slug, status=0).exists():
        if Product.objects.filter(slug=prod_slug, status=0).exists():
            product = Product.objects.get(slug=prod_slug, status=0)
            context = {'product': product}
            return render(request, "store/products/view.html", context)
        else:
            messages.error(request, "No such product found")
            return redirect('collections')
    else:
        messages.error(request, "No such category found")
        return redirect('collections')
    

def productlistAjax(request):
    products = Product.objects.filter(status=0).values_list('name',flat=True)
    productList = list(products)

    return JsonResponse(productList, safe=False)   

def searchproduct(request):
    if request.method == 'POST':
        searchedterm = request.POST.get('productsearch')
        if searchedterm == "":
             return redirect(request.META.get('HTTP_REFERER'))
        else:
            product = Product.objects.filter(name__icontains=searchedterm).first()



            if product:
                return redirect('collections/'+product.category.slug+'/'+product.slug)
            else:
                 # AI-powered fallback: turn intent into shopping keywords
                 keywords = _nl_to_keywords(searchedterm)
                 if keywords:
                     q = Q()
                     for kw in keywords:
                         kw = kw.strip()
                         if not kw:
                             continue
                         q |= (
                             Q(name__icontains=kw) |
                             Q(tag__icontains=kw) |
                             Q(description__icontains=kw) |
                             Q(category__name__icontains=kw)
                         )
                     results = Product.objects.filter(q, status=0).select_related('category').distinct()
                     if results.exists():
                         context = {
                             'products': results,
                             'query': searchedterm,
                             'keywords': keywords,
                         }
                         return render(request, "store/products/search_results.html", context)
                 messages.info(request,"No product matched your search")
                 return redirect(request.META.get('HTTP_REFERER'))


            
    return redirect(request.META.get('HTTP_REFERER'))

 


def _nl_to_keywords(query: str):
    """Convert natural language to shopping keywords using OpenAI if configured.
    Returns a list of strings (keywords). Falls back to a simple ruleset if API key is missing or errors occur.
    """
    # Simple intent map fallback
    simple_map = {
        'hungry': ['food', 'snacks', 'grocery'],
        'thirsty': ['beverage', 'drinks', 'juice'],
        'play games': ['gaming', 'video games', 'console', 'controller', 'gaming laptop', 'gaming accessories'],
        'want to play': ['gaming', 'video games', 'console', 'controller', 'gaming accessories'],
        'play': ['gaming', 'video games', 'console', 'controller', 'gaming accessories'],
        'game': ['gaming', 'video games', 'console', 'controller', 'gaming accessories'],
        'sports': ['sports', 'fitness', 'equipment'],
        'workout': ['fitness', 'gym', 'dumbbell', 'treadmill'],
        'run': ['shoes', 'sneakers', 'running shoes', 'sports', 'fitness'],
        'running': ['running shoes', 'shoes', 'sneakers', 'sports'],
        'jog': ['running shoes', 'shoes', 'sneakers'],
        'walking': ['walking shoes', 'shoes', 'sneakers'],
        'walk': ['walking shoes', 'shoes', 'sneakers'],
        'study': ['books', 'stationery', 'laptop'],
        'cold': ['sweater', 'jacket', 'hoodie'],
        'hot': ['fan', 'cooler', 'air conditioner'],
        'party': ['party', 'dress', 'decoration'],
        'travel': ['luggage', 'backpack', 'travel accessories'],
        'shoe': ['shoes', 'sneakers', 'footwear'],
        'shoes': ['shoes', 'sneakers', 'footwear'],
        'sneaker': ['sneakers', 'shoes', 'footwear'],
    }
    qlow = query.lower()
    fallback = []
    for k, v in simple_map.items():
        if k in qlow:
            fallback.extend(v)

    api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
    if not api_key:
        return list(dict.fromkeys(fallback))  # unique while preserving order

    try:
        # Ask model to strictly return JSON array of keywords
        prompt = (
            "You are a shopping search assistant. Convert the user's intent into 3-8 concise shopping keywords or categories. "
            "Only reply with a JSON array of strings, no extra text.\n\n"
            f"User intent: {query}"
        )
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Return only JSON array of keywords."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(data).encode('utf-8'),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode('utf-8'))
        content = resp_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        # Try parse JSON array
        keywords = []
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                keywords = [str(x) for x in parsed]
        except Exception:
            # Fallback: split by comma
            if content:
                keywords = [s.strip() for s in content.split(',') if s.strip()]
        result = keywords or fallback
        # De-duplicate
        return list(dict.fromkeys(result))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception):
        return list(dict.fromkeys(fallback))
