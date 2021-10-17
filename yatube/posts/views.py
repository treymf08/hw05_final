from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


@require_GET
def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context)


@require_GET
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    following = (
        request.user.is_authenticated
        and request.user != author
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'posts': posts,
        'page_obj': page_obj,
        'count_posts': paginator.count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


@require_GET
def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    author = post.author
    count_posts = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    context = {
        'comments': comments,
        'form': form,
        'post': post,
        'count_posts': count_posts,
        'author': author
    }
    return render(request, 'posts/post_detail.html', context)


@require_http_methods(['GET', 'POST'])
@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@require_http_methods(['GET', 'POST'])
@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': 'true',
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
