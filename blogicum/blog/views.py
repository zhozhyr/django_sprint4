from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import PostForm, CommentForm, ProfileEditForm
from .models import Post, Category, Comment
from django.utils import timezone


PER_PAGE = 10


def filter_posts():
    f_posts = (
        Post.objects.select_related(
            "category",
            "location",
            "author",
        )
        .filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    )
    return f_posts


def index(request):
    template_name = 'blog/index.html'
    post_list = Post.objects.select_related(
        'location', 'author', 'category'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).annotate(
        comment_count=Count("comments")
    ).order_by(
        "-pub_date"
    )
    page_obj = Paginator(post_list, PER_PAGE)
    page_obj = page_obj.get_page(request.GET.get('page'))
    context = {'page_obj': page_obj}
    return render(request, template_name, context)


def post_detail(request, post_id):
    template_name = 'blog/detail.html'
    post = get_object_or_404(
        Post,
        Q(
            pk=post_id,
            pub_date__lte=timezone.now(),
            category__is_published=True,
            is_published=True
        ) | Q(
            pk=post_id,
            author=request.user
        )
    )
    comments = Comment.objects.filter(post=post)
    context = {'post': post,
               'comments': comments,
               'form': CommentForm()}
    return render(request, template_name, context)


def category_posts(request, category_slug):
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )
    post_list = filter_posts().filter(category=category)
    page_obj = Paginator(post_list, PER_PAGE)
    page_obj = page_obj.get_page(request.GET.get('page'))
    context = {'page_obj': page_obj, 'category': category}
    return render(request, template_name, context)


class RegisterView(CreateView):
    template_name = 'registration/registration_form.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('blog:index')


def profile_view(request, username):

    profile = get_object_or_404(User, username=username)

    posts = Post.objects.select_related(
        'location', 'author', 'category'
    ).filter(
        author=profile.pk
    ).annotate(
        comment_count=Count("comments")
    ).order_by(
        "-pub_date"
    )
    page_obj = Paginator(posts, PER_PAGE)
    page_obj = page_obj.get_page(request.GET.get('page'))

    return render(request, 'blog/profile.html',
                  {'profile': profile,
                   'page_obj': page_obj})


@login_required
def edit_profile(request):

    form = ProfileEditForm(instance=request.user)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST)

        if form.is_valid():
            user = User.objects.get(pk=request.user.pk)

            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]

            user.save()

    context = {
        "form": form
    }

    return render(request, 'blog/user.html', context)


@login_required
def post_create(request):

    post = PostForm()
    if request.method == 'POST':
        post = PostForm(request.POST, request.FILES)

        if post.is_valid():
            post_instance = post.save(commit=False)
            post_instance.author = request.user
            post_instance.save()

            user = post_instance.author.username
            return redirect("blog:profile", username=user)

    context = {
        "form": post
    }

    return render(request, "blog/create.html", context=context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        if request.user.pk == post.author.pk:
            if post_form.is_valid():
                post.text = post_form.cleaned_data["text"]
                post.title = post_form.cleaned_data["title"]
                post.pub_date = post_form.cleaned_data["pub_date"]
                post.category = post_form.cleaned_data["category"]
                post.location = post_form.cleaned_data["location"]
                post.save()
        return redirect("blog:post_detail", post_id=post_id)
    else:
        post_form = PostForm(instance=post)
        context = {
            "form": post_form
        }
        return render(request, "blog/create.html", context=context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.pk != post.author.pk:
        return redirect("blog:post_detail", post_id=post_id)
    else:
        user = post.author.username
        post.delete()
        return redirect("blog:profile", username=user)


@login_required
def comment_create(request, post_id):
    if request.method != 'POST':
        return redirect('blog:post_detail', post_id=post_id)

    post = get_object_or_404(
        Post,
        pk=post_id
    )

    comment_form = CommentForm(request.POST)
    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.author = request.user
        comment.post = post

        comment.save()

    return redirect('blog:post_detail', post_id=post_id)


@login_required
def comment_edit(request, post_id, comment_id):
    template_name = 'blog/comment.html'

    comment = get_object_or_404(Comment, pk=comment_id)
    form = CommentForm(instance=comment)

    if request.method == 'POST' and request.user.pk == comment.author.pk:
        comment_form = CommentForm(request.POST)
        if not comment_form.is_valid():
            return redirect('blog:edit_comment', post_id=comment_id)
        comment.text = comment_form.cleaned_data['text']
        comment.save()
        return redirect('blog:post_detail', post_id=post_id)

    context = {
        'form': form,
        'comment': comment
    }
    return render(request, template_name, context)


@login_required
def comment_delete(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == 'POST':
        if request.user.pk == comment.author.pk:
            comment.delete()
        return redirect("blog:post_detail", post_id=post_id)
    else:
        context = {
            "comment": comment
        }
        return render(request, "blog/comment.html", context)
