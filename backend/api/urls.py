from django.urls import path

from . import views as v

urlpatterns = [
    path("health/", v.health),
    path("auth/register", v.register),
    path("auth/login", v.login),
    path("auth/logout", v.logout),
    path("auth/change-pin", v.change_pin),
    path("me", v.me),
    path("me/language", v.set_language),
    path("progress", v.progress),
    path("classes/join", v.join_class),
    path("redeem", v.redeem),
    path("teacher/classes", v.teacher_classes),
    path("teacher/classes/<int:pk>", v.teacher_class_detail),
    path("teacher/classes/<int:pk>/students", v.teacher_students),
    path("teacher/classes/<int:pk>/students/<str:sid>/reset-pin", v.teacher_reset_pin),
]
