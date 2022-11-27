from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow
from posts.services.services import get_paginator


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = get_paginator(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
        'posts': posts
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    post_user_list = Post.objects.select_related(
        'author', 'group'
    ).filter(author__username=username)
    author = get_object_or_404(User, username=username)
    following = (request.user.is_authenticated
                 and author.following.filter(user=request.user).exists())
    number_of_posts = post_user_list.count()
    page_obj = get_paginator(request, post_user_list)
    context = {
        'page_obj': page_obj,
        'username': author,
        'number_of_posts': number_of_posts,
        'post_user_list': post_user_list,
        'following': following
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post_det = get_object_or_404(Post, id=post_id)
    post_count = Post.objects.filter(author__username=post_det.author).count()
    comments = post_det.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post_det,
        'post_count': post_count,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html',
                  {'form': form,
                   'is_edit': True,
                   'post_id': post.id})


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(request, posts)
    context = {
        'page_obj': page_obj,
        'posts': posts
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    if request.user.username == username:
        return redirect('posts:profile', username=username)
    following = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(
        user=request.user,
        author=following
    ).exists()
    if not is_follower:
        Follow.objects.create(user=request.user, author=following)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    following = get_object_or_404(User, username=username)
    follower = get_object_or_404(Follow, author=following, user=request.user)
    follower.delete()
    return redirect('posts:profile', username=username)
