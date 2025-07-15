from django.shortcuts import render
from bag.contexts import bag_contents

# Create your views here.


def view_bag(request):
    """ A view to render the bag content """
    context = bag_contents(request)
    return render(request, 'bag/bag.html', context)
