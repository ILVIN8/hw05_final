from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


NUMBER_OF_POSTS = 10


@cache_page(20)
def index(request):
    template = "posts/index.html"
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "title": "Главная страница проекта YaTube",
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "group": group,
        "page_obj": page_obj,
    }
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    template = "posts/profile.html"
    author = User.objects.get(username=username)
    user = request.user
    post_list = Post.objects.filter(author=author)
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    post_count = post_list.count()
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    following = (
        not request.user.is_anonymous
        and author.following.filter(user=user, author=author).exists()
    )
    context = {
        "page_obj": page_obj,
        "title": f"Профайл пользователя {username}",
        "author": author,
        "post_count": post_count,
        "following": following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = "posts/post_detail.html"
    post = Post.objects.get(id=post_id)
    group = post.group
    title = post.text[0:29]
    post_count = Post.objects.filter(author=post.author).count()
    comments = Comment.objects.filter(post_id=post_id)
    form = CommentForm(
        request.POST or None,
    )
    context = {
        "post": post,
        "title": f"Пост {title}",
        "group": group,
        "post_count": post_count,
        "username": request.user.username,
        "comments": comments,
        "form": form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author_id = request.user.id
        new_post.save()
        return redirect(f"/profile/{request.user.username}/")

    template = "posts/create_post.html"
    context = {
        "form": form,
    }

    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect(f"/posts/{post_id}/")

    template = "posts/create_post.html"
    context = {
        "form": form,
        "is_edit": True,
    }

    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    template = "posts/follow.html"
    user = request.user
    blogers_id = Follow.objects.filter(user=user).values_list(
        "author_id", flat=True
    )
    post_list = Post.objects.filter(author_id__in=blogers_id)
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "page_obj": page_obj,
        "title": "Cтраница избранных блоггеров YaTube",
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:follow_index")
